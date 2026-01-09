#!/usr/bin/env python3
"""Command-line script to embed Dayflow local database activities.

Usage:
    python scripts/embed_dayflow.py --db-path "/path/to/dayflow.sqlite"
    python scripts/embed_dayflow.py  # Uses default path from config
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path
from uuid import UUID

from loguru import logger
from sqlmodel import Session, select

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.connectors.impl.dayflow_local_connector import (
    DayflowLocalConfig,
    DayflowLocalConnector,
)
from app.core.config import settings
from app.core.db import engine
from app.models.activity import Activity
from app.services.embedding_service import EmbeddingService


def main():
    """Main entry point for embedding Dayflow activities."""
    parser = argparse.ArgumentParser(
        description="Embed Dayflow local database activities into vectors"
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default=settings.dayflow.db_path,
        help="Path to Dayflow SQLite database file",
    )
    parser.add_argument(
        "--user-id",
        type=str,
        required=True,
        help="User ID to associate activities with",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Batch size for committing embeddings (default: 10)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of activities to process (for testing)",
    )
    parser.add_argument(
        "--force-regenerate-all",
        action="store_true",
        help="Force regenerate embeddings for all activities, even if they already exist",
    )
    parser.add_argument(
        "--start-date",
        type=str,
        default="2020-08-12",
        help="Start date for fetching activities (YYYY-MM-DD format, default: 2020-08-12)",
    )
    
    args = parser.parse_args()
    
    # Validate user_id is a valid UUID
    try:
        user_id = UUID(args.user_id)
    except ValueError:
        logger.error(f"Invalid user ID format: {args.user_id}")
        sys.exit(1)
    
    # Parse start date
    try:
        start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
    except ValueError:
        logger.error(f"Invalid start date format: {args.start_date}. Expected YYYY-MM-DD format")
        sys.exit(1)
    
    # Initialize connector
    logger.info(f"Reading Dayflow database from: {args.db_path}")
    config = DayflowLocalConfig(db_path=args.db_path)
    connector = DayflowLocalConnector(config)
    
    # Validate database access
    try:
        import asyncio
        asyncio.run(connector.validate_config())
    except Exception as e:
        logger.error(f"Failed to validate Dayflow database: {e}")
        sys.exit(1)
    
    # Fetch all activities
    logger.info(f"Fetching activities from Dayflow database (from {start_date.date()})...")
    activity_creates = connector.fetch_activities(start_time=start_date,
                                                  end_time=datetime.now())
    for ac in activity_creates:
        ac.user_id = user_id
    
    if args.limit:
        activity_creates = activity_creates[:args.limit]
        logger.info(f"Limited to {args.limit} activities for testing")
    
    logger.info(f"Fetched {len(activity_creates)} activities")
    
    if not activity_creates:
        logger.warning("No activities found in database")
        return
    
    # Initialize force_regenerate_ids outside session scope
    force_regenerate_ids = set()
    
    # Save activities to database with upsert logic
    with Session(engine) as session:
        # Set user_id for all activities
        for activity_create in activity_creates:
            activity_create.user_id = user_id
        
        # Batch query: get all existing fingerprints
        fingerprints = [ac.fingerprint for ac in activity_creates]
        existing_activities_dict = {
            act.fingerprint: act
            for act in session.exec(
                select(Activity).where(Activity.fingerprint.in_(fingerprints))
            ).all()
        }
        
        # Track activities by status
        new_activities = []
        updated_activities = []
        unchanged_activities = []
        
        # Process each activity create
        for activity_create in activity_creates:
            existing_activity = existing_activities_dict.get(activity_create.fingerprint)
            
            if existing_activity is None:
                # New activity: create it
                activity = Activity.model_validate(activity_create)
                session.add(activity)
                new_activities.append(activity)
            else:
                # Existing activity: check if content changed
                content_changed = (
                    existing_activity.title != activity_create.title
                    or existing_activity.content != activity_create.content
                    or existing_activity.extra_data != activity_create.extra_data
                )
                
                if content_changed:
                    # Update existing activity
                    existing_activity.title = activity_create.title
                    existing_activity.content = activity_create.content
                    existing_activity.extra_data = activity_create.extra_data
                    existing_activity.updated_at = datetime.now()
                    session.add(existing_activity)
                    updated_activities.append(existing_activity)
                    force_regenerate_ids.add(existing_activity.id)
                    logger.debug(
                        f"Updated activity {existing_activity.id} "
                        f"(fingerprint: {activity_create.fingerprint[:8]}...)"
                    )
                else:
                    # No changes: keep existing
                    unchanged_activities.append(existing_activity)
        
        # Commit all changes
        session.commit()
        
        # Refresh to get IDs for new activities
        for activity in new_activities:
            session.refresh(activity)
        
        # Combine all activities
        activities = new_activities + updated_activities + unchanged_activities
        
        logger.info(
            f"Activity upsert completed: "
            f"{len(new_activities)} new, "
            f"{len(updated_activities)} updated, "
            f"{len(unchanged_activities)} unchanged "
            f"(total: {len(activities)} activities)"
        )
        
        if force_regenerate_ids:
            logger.info(
                f"{len(force_regenerate_ids)} activities marked for embedding regeneration"
            )
    
    # Initialize embedding service
    logger.info("Initializing embedding service...")
    embedding_service = EmbeddingService()
    
    # Embed activities
    logger.info(f"Starting embedding process (batch size: {args.batch_size})...")
    with Session(engine) as session:
        # Re-query activities to get fresh session-bound objects
        activities = session.exec(
            select(Activity).where(
                Activity.fingerprint.in_([a.fingerprint for a in activity_creates])
            )
        ).all()
        
        # If --force-regenerate-all is set, add all activity IDs to force_regenerate_ids
        if args.force_regenerate_all:
            force_regenerate_ids.clear()
            force_regenerate_ids.update(
                activity.id for activity in activities if activity.id is not None
            )
            logger.info(
                f"Force regenerate all: {len(force_regenerate_ids)} activities will be re-embedded"
            )
        
        success_count = embedding_service.embed_activities_batch(
            activities,
            user_id,
            session,
            batch_size=args.batch_size,
            force_regenerate_ids=force_regenerate_ids,
        )
    
    logger.info(f"✅ Embedding completed: {success_count}/{len(activities)} activities embedded")


if __name__ == "__main__":
    main()

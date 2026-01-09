#!/usr/bin/env python3
"""Command-line script to embed Dayflow local database activities.

Usage:
    python scripts/embed_dayflow.py --db-path "/path/to/dayflow.sqlite"
    python scripts/embed_dayflow.py  # Uses default path from config
"""

import argparse
import sys
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
        default=settings.DAYFLOW_LOCAL_DB_PATH,
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
    
    args = parser.parse_args()
    
    # Validate user_id is a valid UUID
    try:
        user_id = UUID(args.user_id)
    except ValueError:
        logger.error(f"Invalid user ID format: {args.user_id}")
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
    logger.info("Fetching activities from Dayflow database...")
    activity_creates = connector.fetch_all_activities()
    for ac in activity_creates:
        ac.user_id = user_id
    
    if args.limit:
        activity_creates = activity_creates[:args.limit]
        logger.info(f"Limited to {args.limit} activities for testing")
    
    logger.info(f"Fetched {len(activity_creates)} activities")
    
    if not activity_creates:
        logger.warning("No activities found in database")
        return
    
    # Save activities to database with batch validation
    with Session(engine) as session:
        # Set user_id for all activities
        for activity_create in activity_creates:
            activity_create.user_id = user_id
        
        # Batch query: get all existing fingerprints
        fingerprints = [ac.fingerprint for ac in activity_creates]
        existing_activities = session.exec(
            select(Activity).where(Activity.fingerprint.in_(fingerprints))
        ).all()
        
        # Build a set of existing fingerprints for fast lookup
        existing_fingerprints = {act.fingerprint for act in existing_activities}
        
        # Separate new activities from existing ones
        new_activity_creates = [
            ac for ac in activity_creates 
            if ac.fingerprint not in existing_fingerprints
        ]
        
        logger.info(
            f"Found {len(existing_activities)} existing activities, "
            f"{len(new_activity_creates)} new activities to create"
        )
        
        # Batch create new activities
        new_activities = []
        for activity_create in new_activity_creates:
            activity = Activity.model_validate(activity_create)
            session.add(activity)
            new_activities.append(activity)
        
        session.commit()
        
        # Refresh to get IDs for new activities
        for activity in new_activities:
            session.refresh(activity)
        
        # Combine existing and new activities
        activities = list(existing_activities) + new_activities
        
        logger.info(
            f"Saved {len(new_activities)} new activities to database "
            f"(total: {len(activities)} activities)"
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
        
        success_count = embedding_service.embed_activities_batch(
            activities,
            user_id,
            session,
            batch_size=args.batch_size,
        )
    
    logger.info(f"✅ Embedding completed: {success_count}/{len(activities)} activities embedded")


if __name__ == "__main__":
    main()

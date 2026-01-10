"""Sync service for synchronizing activities from data sources."""

from datetime import datetime
from uuid import UUID

from loguru import logger
from sqlmodel import Session, select

from app.connectors.registry import registry
from app.models.activity import Activity
from app.models.source_config import SourceConfig
from app.services.embedding_service import EmbeddingService


class SyncService:
    """Service for syncing activities from data sources."""

    def __init__(self):
        """Initialize sync service."""
        self.embedding_service = EmbeddingService()

    async def sync_source_config(
        self,
        source_config: SourceConfig,
        user_id: UUID,
        session: Session,
        start_date: datetime,
        batch_size: int = 10,
    ) -> dict[str, int]:
        """Sync activities from a source configuration.

        Args:
            source_config: Source configuration to sync
            user_id: User ID for data isolation
            session: Database session
            start_date: Start date for fetching activities
            batch_size: Batch size for embedding commits

        Returns:
            Dictionary with sync statistics:
            - total_fetched: Total activities fetched from source
            - new_count: Number of new activities created
            - updated_count: Number of activities updated
            - embedded_count: Number of activities embedded
        """
        logger.info(
            f"Starting sync for source config {source_config.id} "
            f"(type: {source_config.type}, name: {source_config.name})"
        )

        # Get connector instance
        try:
            connector = registry.get(source_config)
        except ValueError as e:
            logger.error(f"Failed to get connector: {e}")
            raise

        # Fetch activities from connector
        end_time = datetime.now()
        logger.info(
            f"Fetching activities from {start_date.date()} to {end_time.date()}"
        )

        # Note: fetch_activities is async but we're calling it synchronously
        # We need to handle this properly

        activity_creates = await connector.fetch_activities(start_time=start_date, end_time=end_time)

        # Set user_id for all activities
        for activity_create in activity_creates:
            activity_create.user_id = user_id

        total_fetched = len(activity_creates)
        logger.info(f"Fetched {total_fetched} activities from source")

        if not activity_creates:
            return {
                "total_fetched": 0,
                "new_count": 0,
                "updated_count": 0,
                "embedded_count": 0,
            }

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
        force_regenerate_ids = set()

        # Process each activity create
        for activity_create in activity_creates:
            existing_activity = existing_activities_dict.get(
                activity_create.fingerprint
            )

            if existing_activity is None:
                # New activity: create it
                activity = Activity.model_validate(activity_create)
                activity.source_config_id = source_config.id
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
                    existing_activity.source_config_id = source_config.id
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

        # Embed activities
        logger.info("Starting embedding process...")
        embedded_count = self.embedding_service.embed_activities_batch(
            activities,
            user_id,
            session,
            batch_size=batch_size,
            force_regenerate_ids=force_regenerate_ids,
        )

        logger.info(
            f"✅ Sync completed: {total_fetched} fetched, "
            f"{len(new_activities)} new, {len(updated_activities)} updated, "
            f"{embedded_count} embedded"
        )

        return {
            "total_fetched": total_fetched,
            "new_count": len(new_activities),
            "updated_count": len(updated_activities),
            "embedded_count": embedded_count,
        }

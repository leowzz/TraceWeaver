import asyncio
import uuid
from datetime import datetime
from loguru import logger

from app.api.deps import get_db
from app.connectors import registry
from app.core.context import mock_ctx
from app.crud.source_config import source_config_crud

async def main():
    session = next(get_db())
    # Assuming the SiYuan config is at ID 1. Adjust if necessary.
    config = source_config_crud.get(session=session, id=1)
    if not config:
        logger.error("Source config with ID 1 not found.")
        return
        
    logger.info(f"Using config: {config.name} ({config.type})")
    connector = registry.get(config)
    
    # Target date: 2025-12-19
    start_time = datetime(2025, 12, 19, 0, 0, 0)
    end_time = datetime(2025, 12, 19, 23, 59, 59)
    
    logger.info(f"Fetching notes from {start_time} to {end_time}...")
    activities = await connector.fetch_activities(start_time, end_time)
    
    logger.info(f"Found {len(activities)} activities.")
    for activity in activities:
        logger.info(f"- [{activity.occurred_at}] {activity.title} (ID: {activity.source_id})")
        logger.debug(f"Content: {activity.content}...")

if __name__ == "__main__":
    with mock_ctx(user_id=uuid.uuid4()):
        asyncio.run(main())

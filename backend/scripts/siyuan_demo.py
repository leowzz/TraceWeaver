import asyncio
import re
import uuid
from datetime import datetime

from loguru import logger

from app.api.deps import get_db
from app.clients.siyuan.schema import BlockSchema
from app.connectors import registry
from app.connectors.impl.siyuan_connector import SiYuanConnector
from app.core.context import mock_ctx
from app.crud.source_config import source_config_crud
from app.services.image_analysis_service import submit_image_analysis_task
from app.schemas.llm import ImageAnalysisTaskData
from app.models.enums import ImageSourceType

# Regex to match markdown image syntax: ![alt](path)
IMG_PATH_PATTERN = re.compile(r"!\[.*?\]\((assets/[^)]+)\)")


async def main():
    session = next(get_db())
    # Assuming the SiYuan config is at ID 1. Adjust if necessary.
    config = source_config_crud.get(session=session, id=1)
    if not config:
        logger.error("Source config with ID 1 not found.")
        return

    logger.info(f"Using config: {config.name} ({config.type})")
    connector: SiYuanConnector = registry.get(config)

    # Target date: 2025-12-19
    start_time = datetime(2025, 12, 26, 0, 0, 0)
    end_time = datetime(2025, 12, 26, 23, 59, 59)

    logger.info(f"Fetching notes from {start_time} to {end_time}...")
    activities = await connector.fetch_activities(start_time, end_time)

    logger.info(f"Found {len(activities)} activities.")
    img_paths = ['assets/image-20251219112035-5zqm3ln.png']
    for activity in activities:
        if any(exclude_str in activity.title for exclude_str in ('MacOS', '2025-12-26')):
            continue
        logger.info(f"- [{activity.occurred_at}] {activity.title} (ID: {activity.source_id})")
        # logger.debug(f"Content: {activity.content}...")

        # Extract image paths from content
        paths = IMG_PATH_PATTERN.findall(activity.content or "")
        img_paths.extend(paths)

    logger.info(f"Found {len(img_paths)} images: {img_paths}")
    for img_path in img_paths:
        from app.services.image_analysis_service import submit_image_analysis_task
        from app.schemas.llm import ImageAnalysisTaskData
        from app.models.enums import ImageSourceType
        submit_image_analysis_task(ImageAnalysisTaskData(
            img_path=img_path,
            source_type=ImageSourceType.SIYUAN_LOCAL,
            llm_prompt_id=1,
            model_name="qwen3-vl:2b"
        ))


async def process_all_siyuan_img():
    session = next(get_db())
    # Assuming the SiYuan config is at ID 1. Adjust if necessary.
    config = source_config_crud.get(session=session, id=1)
    if not config:
        logger.error("Source config with ID 1 not found.")
        return

    logger.info(f"Using config: {config.name} ({config.type})")
    connector: SiYuanConnector = registry.get(config)
    siyuan_client = connector._get_client()
    query_result = await siyuan_client.query_sql("SELECT * FROM blocks where markdown like '%![image](assets%' limit 10")
    block_datas: list[BlockSchema] = [BlockSchema.model_validate(qr) for qr in query_result]
    logger.info(f"{block_datas[0]}")

    img_paths = ['assets/image-20251219112035-5zqm3ln.png']
    for b_data in block_datas:
        # Extract image paths from content
        paths = IMG_PATH_PATTERN.findall(b_data.markdown or "")
        for img_p in paths:
            submit_image_analysis_task(ImageAnalysisTaskData(
                img_path=img_p,
                source_type=ImageSourceType.SIYUAN_LOCAL,
                llm_prompt_id=1,
                model_name="qwen3-vl:2b",
                extra_data=b_data.model_dump()
            ))
        img_paths.extend(paths)


if __name__ == "__main__":
    with mock_ctx(user_id=uuid.uuid4()):
        asyncio.run(process_all_siyuan_img())

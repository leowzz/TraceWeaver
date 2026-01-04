"""Celery tasks for TraceWeaver."""

import asyncio
from pathlib import Path

from celery.utils.log import get_task_logger
from sqlmodel import Session, select

from app.core.config import settings
from app.core.celery_app import celery_app
from app.core.db import engine
from app.crud.llm_model_config import llm_model_config_crud
from app.crud.llm_prompt import llm_prompt_crud
from app.models.enums import AnalysisStatus, ImageSourceType, SourceType
from app.models.image_analysis import ImageAnalysis
from app.models.source_config import SourceConfig
from app.schemas.llm import ImageAnalysisTaskData
from app.clients.llm.client import LLMClient, LLMClientError
from app.connectors import registry

logger = get_task_logger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_image_analysis(self, task_data: dict) -> dict:
    """Process a single image analysis task.

    This is a Celery task that wraps the async processing logic.

    Args:
        task_data: Task data dictionary containing:
            - img_path: Image path
            - source_type: Source type (e.g., "SIYUAN_LOCAL")
            - llm_prompt_id: LLM prompt template ID
            - model_name: LLM model name/ID

    Returns:
        dict with analysis_id and status
    """
    # Run async code in sync context
    return asyncio.run(_process_image_analysis_async(task_data))


async def _process_image_analysis_async(task_data: dict) -> dict:
    """Async implementation of image analysis processing."""
    # Validate task data using schema
    try:
        task = ImageAnalysisTaskData.model_validate(task_data)
    except Exception as e:
        logger.error(f"Invalid task data: {e}")
        raise ValueError(f"Invalid task data: {e}")

    img_path = task.img_path
    source_type = task.source_type
    llm_prompt_id = task.llm_prompt_id
    model_name = task.model_name

    # Create database record
    with Session(engine) as session:
        # Create pending record
        analysis_record = ImageAnalysis(
            img_path=img_path,
            source_type=source_type,
            llm_prompt_id=llm_prompt_id,
            model_name=model_name,
            status=AnalysisStatus.PENDING,
        )
        session.add(analysis_record)
        session.commit()
        session.refresh(analysis_record)
        analysis_id = analysis_record.id

        try:
            # Update status to processing
            analysis_record.status = AnalysisStatus.PROCESSING
            session.add(analysis_record)
            session.commit()

            # Get prompt content
            prompt = llm_prompt_crud.get(session, llm_prompt_id)
            if not prompt:
                raise ValueError(f"LLM prompt with ID {llm_prompt_id} not found")
            if not prompt.is_active:
                raise ValueError(f"LLM prompt with ID {llm_prompt_id} is not active")

            # Get image data based on source type
            image_bytes = await _get_image_bytes(session, source_type, img_path)

            # Get model configuration
            model_config = llm_model_config_crud.get_by_model_name(session, model_name)
            logger.info(f"{model_config=}")
            if not model_config:
                raise ValueError(f"LLM model config for '{model_name}' not found")
            if not model_config.is_active:
                raise ValueError(f"LLM model config for '{model_name}' is not active")

            # Analyze image with LLM client
            analysis_result = await _analyze_image_with_llm_client(
                image_bytes, prompt.content, model_config
            )

            # Update record with result
            analysis_record.status = AnalysisStatus.COMPLETED
            analysis_record.analysis_result = analysis_result
            session.add(analysis_record)
            session.commit()

            logger.info(
                f"Successfully analyzed image {img_path} (analysis_id: {analysis_id})"
            )

            return {"analysis_id": analysis_id, "status": "completed"}

        except Exception as e:
            logger.error(f"Failed to analyze image {img_path}: {e}", exc_info=True)
            # Update record with error
            analysis_record.status = AnalysisStatus.FAILED
            analysis_record.error_message = str(e)
            session.add(analysis_record)
            session.commit()

            return {"analysis_id": analysis_id, "status": "failed", "error": str(e)}


async def _get_image_bytes(
    session: Session, source_type: ImageSourceType, img_path: str
) -> bytes:
    """Get image bytes from the source system."""
    if source_type != ImageSourceType.SIYUAN_LOCAL:
        raise ValueError(f"Image fetching from {source_type} is not yet supported")

    # Get source config for SiYuan
    statement = select(SourceConfig).where(
        SourceConfig.type == SourceType.SIYUAN, SourceConfig.is_active == True
    )
    source_config = session.exec(statement).first()
    if not source_config:
        raise ValueError("No active SiYuan source config found")

    # Get connector and fetch image
    connector = registry.get(source_config)
    if source_type == ImageSourceType.SIYUAN_LOCAL:
        from app.connectors.impl.siyuan_connector import SiYuanConnector

        if not isinstance(connector, SiYuanConnector):
            raise ValueError("Invalid connector type for SiYuan")
        client = connector._get_client()
        image_bytes = await client.get_file(f"/data/{img_path}")
        if settings.CELERY_TMP_DATA_DIR:
            with open(Path(settings.CELERY_TMP_DATA_DIR) / img_path.split('-')[-1], 'wb') as f:
                f.write(image_bytes)
        return image_bytes

    raise ValueError(f"Unsupported source type: {source_type}")


async def _analyze_image_with_llm_client(
    image_bytes: bytes, prompt_content: str, model_config
) -> str:
    """Analyze image using LLM client."""
    client = None
    try:
        client = LLMClient(
            provider=model_config.provider,
            model_id=model_config.model_id,
            base_url=model_config.base_url,
            api_key=model_config.api_key,
            config=model_config.config or {},
        )
        logger.info(f"{len(image_bytes)=}")

        response = await client.analyze_image(image_bytes, prompt_content)
        return response.content

    except LLMClientError as e:
        logger.error(f"LLM client error: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to analyze image with LLM: {e}", exc_info=True)
        raise ValueError(f"LLM analysis failed: {e}") from e
    finally:
        if client is not None:
            await client.close()

"""LLM Image Analysis Worker - Processes image analysis tasks from Redis queue."""

import asyncio
from pathlib import Path

from loguru import logger
from sqlmodel import Session, select

from app.core.db import engine
from app.core.queue import dequeue_image_analysis_task
from app.crud.image_analysis import image_analysis_crud
from app.crud.llm_model_config import llm_model_config_crud
from app.crud.llm_prompt import llm_prompt_crud
from app.models.enums import AnalysisStatus, ImageSourceType, SourceType
from app.models.image_analysis import ImageAnalysis
from app.schemas.llm import ImageAnalysisTaskData
from app.clients.llm.client import LLMClient, LLMClientError
from app.connectors import registry
from app.models.source_config import SourceConfig


async def process_image_analysis_task(task_data: dict) -> None:
    """Process a single image analysis task.

    Args:
        task_data: Task data dictionary containing:
            - img_path: Image path
            - source_type: Source type (e.g., "SIYUAN_LOCAL")
            - llm_prompt_id: LLM prompt template ID
            - model_name: LLM model name/ID
    """
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

        except Exception as e:
            logger.error(f"Failed to analyze image {img_path}: {e}", exc_info=True)
            # Update record with error
            analysis_record.status = AnalysisStatus.FAILED
            analysis_record.error_message = str(e)
            session.add(analysis_record)
            session.commit()


async def _get_image_bytes(
    session: Session, source_type: ImageSourceType, img_path: str
) -> bytes:
    """Get image bytes from the source system.

    Args:
        session: Database session
        source_type: Source type
        img_path: Image path

    Returns:
        Image bytes

    Raises:
        ValueError: If source type is not supported or connector not found
    """
    if source_type != ImageSourceType.SIYUAN_LOCAL:
        raise ValueError(f"Image fetching from {source_type} is not yet supported")

    # Get source config for SiYuan (for now, get the first active one)
    # In the future, this could be passed in the task data
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
        image_bytes = await client.get_file(img_path)
        return image_bytes

    raise ValueError(f"Unsupported source type: {source_type}")


async def _analyze_image_with_llm_client(
    image_bytes: bytes, prompt_content: str, model_config
) -> str:
    """Analyze image using LLM client (via agno framework).

    Args:
        image_bytes: Image bytes data
        prompt_content: Prompt template content
        model_config: LLM model configuration from database

    Returns:
        Analysis result text

    Raises:
        LLMClientError: If LLM client request fails
        ValueError: If model configuration is invalid
    """
    client = None
    try:
        # Create LLM client from model config
        client = LLMClient(
            provider=model_config.provider,
            model_id=model_config.model_id,
            base_url=model_config.base_url,
            api_key=model_config.api_key,
            config=model_config.config or {},
        )

        # Analyze image using multimodal capabilities
        response = await client.analyze_image(image_bytes, prompt_content)
        return response.content

    except LLMClientError as e:
        logger.error(f"LLM client error: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to analyze image with LLM: {e}", exc_info=True)
        raise ValueError(f"LLM analysis failed: {e}") from e
    finally:
        # Cleanup client if needed
        if client is not None:
            await client.close()


async def worker_loop() -> None:
    """Main worker loop - continuously process tasks from queue."""
    logger.info("LLM Image Analysis Worker started")
    while True:
        try:
            task_data = dequeue_image_analysis_task(timeout=1)
            if task_data:
                await process_image_analysis_task(task_data)
            else:
                # No task available, wait a bit before checking again
                await asyncio.sleep(0.1)
        except KeyboardInterrupt:
            logger.info("Worker interrupted, shutting down...")
            break
        except Exception as e:
            logger.error(f"Error in worker loop: {e}", exc_info=True)
            await asyncio.sleep(1)  # Wait before retrying


if __name__ == "__main__":
    asyncio.run(worker_loop())


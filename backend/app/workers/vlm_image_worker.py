"""VLM Image Analysis Worker - Processes image analysis tasks from Redis queue."""

import asyncio
import base64
import tempfile
from pathlib import Path

import ollama
from loguru import logger
from sqlmodel import Session, select

from app.core.db import engine
from app.core.queue import dequeue_image_analysis_task
from app.crud.image_analysis import image_analysis_crud
from app.crud.vlm_prompt import vlm_prompt_crud
from app.models.enums import AnalysisStatus, SourceType
from app.models.image_analysis import ImageAnalysis
from app.connectors import registry
from app.models.source_config import SourceConfig


async def process_image_analysis_task(task_data: dict) -> None:
    """Process a single image analysis task.

    Args:
        task_data: Task data dictionary containing:
            - img_path: Image path
            - source_type: Source type (e.g., "SIYUAN")
            - vlm_prompt_id: VLM prompt template ID
            - model_name: VLM model name
    """
    img_path = task_data["img_path"]
    source_type_str = task_data["source_type"]
    vlm_prompt_id = task_data["vlm_prompt_id"]
    model_name = task_data["model_name"]

    source_type = SourceType(source_type_str)

    # Create database record
    with Session(engine) as session:
        # Create pending record
        analysis_record = ImageAnalysis(
            img_path=img_path,
            source_type=source_type,
            vlm_prompt_id=vlm_prompt_id,
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
            prompt = vlm_prompt_crud.get(session, vlm_prompt_id)
            if not prompt:
                raise ValueError(f"VLM prompt with ID {vlm_prompt_id} not found")
            if not prompt.is_active:
                raise ValueError(f"VLM prompt with ID {vlm_prompt_id} is not active")

            # Get image data based on source type
            image_bytes = await _get_image_bytes(session, source_type, img_path)

            # Analyze image with ollama
            analysis_result = await _analyze_image_with_ollama(
                image_bytes, prompt.content, model_name
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
    session: Session, source_type: SourceType, img_path: str
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
    if source_type != SourceType.SIYUAN:
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
    if source_type == SourceType.SIYUAN:
        from app.connectors.impl.siyuan_connector import SiYuanConnector

        if not isinstance(connector, SiYuanConnector):
            raise ValueError("Invalid connector type for SiYuan")
        client = connector._get_client()
        image_bytes = await client.get_file(img_path)
        return image_bytes

    raise ValueError(f"Unsupported source type: {source_type}")


async def _analyze_image_with_ollama(
    image_bytes: bytes, prompt_content: str, model_name: str
) -> str:
    """Analyze image using ollama VLM.

    Args:
        image_bytes: Image bytes data
        prompt_content: Prompt template content
        model_name: VLM model name

    Returns:
        Analysis result text
    """
    # Save image to temporary file
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
        tmp_file.write(image_bytes)
        tmp_image_path = Path(tmp_file.name).absolute()

    try:
        # Encode image to base64
        img_b64 = base64.b64encode(image_bytes).decode("utf-8")

        # Call ollama
        ollama_client = ollama.AsyncClient(host="http://localhost:11434")
        response = await ollama_client.chat(
            model=model_name,
            messages=[
                {
                    "role": "user",
                    "content": prompt_content,
                    "images": [img_b64],
                }
            ],
        )

        return response["message"]["content"]

    finally:
        # Clean up temporary file
        tmp_image_path.unlink(missing_ok=True)


async def worker_loop() -> None:
    """Main worker loop - continuously process tasks from queue."""
    logger.info("VLM Image Analysis Worker started")
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


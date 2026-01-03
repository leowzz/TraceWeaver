"""Image analysis service - Task submission and management."""

from app.core.queue import enqueue_image_analysis_task
from app.models.enums import SourceType


def submit_image_analysis_task(
    img_path: str,
    source_type: SourceType,
    llm_prompt_id: int,
    model_name: str = "qwen3-vl:2B",
) -> None:
    """Submit an image analysis task to the queue.

    Args:
        img_path: Image path from the source system
        source_type: Source type (SIYUAN, GIT, DAYFLOW)
        llm_prompt_id: LLM prompt template ID
        model_name: LLM model name to use (default: "qwen3-vl:2B")

    Raises:
        ValueError: If required parameters are invalid
    """
    if not img_path:
        raise ValueError("img_path cannot be empty")
    if not llm_prompt_id:
        raise ValueError("llm_prompt_id cannot be empty")

    task_data = {
        "img_path": img_path,
        "source_type": source_type.value if isinstance(source_type, SourceType) else source_type,
        "llm_prompt_id": llm_prompt_id,
        "model_name": model_name,
    }

    enqueue_image_analysis_task(task_data)

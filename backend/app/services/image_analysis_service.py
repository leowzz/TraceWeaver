"""Image analysis service - Task submission and management."""

from app.models.enums import ImageSourceType
from app.schemas.llm import ImageAnalysisTaskData
from app.workers.tasks import process_image_analysis


def submit_image_analysis_task(task_data: ImageAnalysisTaskData) -> str:
    """Submit an image analysis task to Celery.

    Args:
        task_data: Image analysis task data

    Returns:
        Celery task ID
    """
    # Submit task to Celery
    result = process_image_analysis.delay(task_data.model_dump())
    return result.id


if __name__ == "__main__":
    submit_image_analysis_task(
        ImageAnalysisTaskData(
            img_path="assets/image-20251219112035-5zqm3ln.png",
            source_type=ImageSourceType.SIYUAN_LOCAL,
            llm_prompt_id=1,
            model_name="qwen3-vl:2b",
        )
    )

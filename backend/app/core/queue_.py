"""Redis queue client for image analysis tasks."""

import json
from typing import Any

from loguru import logger
from redis import Redis, from_url

from app.core.config import settings

# Global Redis client instance
_redis_client: Redis | None = None


def get_redis_client() -> Redis:
    """Get or create Redis client instance.

    Returns:
        Redis client instance
    """
    global _redis_client
    if _redis_client is None:
        _redis_client = from_url(
            settings.REDIS_URL, encoding="utf-8", decode_responses=True
        )
    return _redis_client


QUEUE_NAME = "vlm_image_analysis_queue"


def enqueue_image_analysis_task(task_data: dict[str, Any]) -> None:
    """Enqueue an image analysis task to Redis queue.

    Args:
        task_data: Task data dictionary containing:
            - img_path: Image path
            - source_type: Source type (e.g., "SIYUAN")
            - vlm_prompt_id: VLM prompt template ID
            - model_name: VLM model name (e.g., "qwen3-vl:2B")
    """
    client = get_redis_client()
    try:
        task_json = json.dumps(task_data, ensure_ascii=False)
        client.lpush(QUEUE_NAME, task_json)
        logger.debug(f"Enqueued image analysis task: {task_data}")
    except Exception as e:
        logger.error(f"Failed to enqueue task: {e}")
        raise


def dequeue_image_analysis_task(timeout: int = 1) -> dict[str, Any] | None:
    """Dequeue an image analysis task from Redis queue.

    Args:
        timeout: Blocking timeout in seconds (default: 1)

    Returns:
        Task data dictionary or None if no task available
    """
    client = get_redis_client()
    try:
        result = client.brpop(QUEUE_NAME, timeout=timeout)
        if result is None:
            return None
        _, task_json_bytes = result
        task_json = task_json_bytes.decode("utf-8") if isinstance(task_json_bytes, bytes) else task_json_bytes
        task_data = json.loads(task_json)
        logger.debug(f"Dequeued image analysis task: {task_data}")
        return task_data
    except redis.exceptions.ConnectionError as e:
        logger.error(f"Redis connection error: {e}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode task JSON: {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to dequeue task: {e}")
        return None


if __name__ == "__main__":
    r = get_redis_client()
    r.set('t', 'val', ex=2)
    logger.info(f"{r.get('t')=}")

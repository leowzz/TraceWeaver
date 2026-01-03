"""Run VLM Image Analysis Worker.

This script starts the worker process that processes image analysis tasks from Redis queue.
"""

import asyncio

from app.core.logger import logger
from app.workers.vlm_image_worker import worker_loop


async def main():
    """Main entry point for the worker."""
    logger.info("Starting VLM Image Analysis Worker...")
    try:
        await worker_loop()
    except KeyboardInterrupt:
        logger.info("Worker stopped by user")
    except Exception as e:
        logger.error(f"Worker crashed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())


#!/usr/bin/env python3
import logging
import sys

from loguru import logger

from app.core.config import settings


def context_info_filter(record):
    if not record:
        return record
    from app.core.context import ctx

    record["user_id"] = ctx.user_id
    record["trace_id"] = ctx.trace_id
    record["level_letter"] = record["level"].name[0]
    return record


LOG_FMT = (
    "<level>[{level_letter}]</level> <yellow>{time:MM-DD HH:mm:ss.SSS}</yellow> "
    "<le>{name}.{function}:{line}</le> {trace_id} | <level>{message}</level>"
)


class InterceptHandler(logging.Handler):
    """
    Loguru官方替换Handler的方法
    Default handler from examples in loguru documentation.
    See https://loguru.readthedocs.io/en/stable/overview.html#entirely-compatible-with-standard-logging
    """

    def emit(self, record: logging.LogRecord):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


logger.remove()
logger.add(
    sys.stderr,
    format=LOG_FMT,
    filter=context_info_filter,
    level=settings.app.log_level,
)

intercept_handler = InterceptHandler()
logging.getLogger("uvicorn").handlers = [intercept_handler]
logging.getLogger("uvicorn.access").handlers = []

if __name__ == "__main__":
    import uuid

    from app.core.context import mock_ctx

    with mock_ctx(user_id=uuid.uuid4()):
        logger.debug("hello")
        logger.info("hello")
        logger.warning("hello")
        logger.error("hello")
        logger.critical("hello")

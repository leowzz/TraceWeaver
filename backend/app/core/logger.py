#!/usr/bin/env python3
# -*- coding:utf-8 -*-
from app.core.config import settings
from loguru import logger
import sys


def context_info_filter(record):
    if not record:
        return record
    from app.core.context import ctx
    record['user_id'] = ctx.user_id
    record['trace_id'] = ctx.trace_id
    record['level_letter'] = record['level'].name[0]
    return record


LOG_FMT = (
    "<level>[{level_letter}]</level> <yellow>{time:MM-DD HH:mm:ss.SSS}</yellow> "
    "<le>{name}.{function}:{line}</le> {trace_id} | <level>{message}</level>"
)

logger.remove()
logger.add(
    sys.stderr,
    format=LOG_FMT,
    filter=context_info_filter,
    level=settings.LOG_LEVEL,
)

if __name__ == '__main__':
    from app.core.context import ctx, mock_ctx
    import uuid

    with mock_ctx(user_id=uuid.uuid4()):
        logger.debug('hello')
        logger.info('hello')
        logger.warning('hello')
        logger.error('hello')
        logger.critical('hello')

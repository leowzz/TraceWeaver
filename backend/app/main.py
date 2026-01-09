from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi.routing import APIRoute
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.cors import CORSMiddleware

from app.api.deps import SessionDep
from app.api.main import api_router
from app.core.config import settings
from app.core.exceptions import (
    general_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from app.core.middleware import ContextMiddleware
from app.core.logger import logger
from contextlib import asynccontextmanager


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0] if route.tags else ''}-{route.name}"


if settings.monitoring.sentry_dsn and settings.app.environment != "local":
    import sentry_sdk
    sentry_sdk.init(dsn=str(settings.monitoring.sentry_dsn), enable_tracing=True)


# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     logger.info("start up")
#     yield
#     logger.info("shut down")


app = FastAPI(
    title=settings.app.project_name,
    openapi_url=f"{settings.app.api_v1_str}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
    # lifespan=lifespan
)

app.add_middleware(ContextMiddleware)  # noqa

# Register exception handlers
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(ResponseValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Set all CORS enabled origins
if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,  # noqa
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.get('/health', tags=['health'])
def health(session: SessionDep):
    from sqlalchemy import select, func
    r = session.exec(select(func.now())).scalar()
    logger.info(f"{r=}")
    return {'status': 'ok', 'date': r}


app.include_router(api_router, prefix=settings.app.api_v1_str)

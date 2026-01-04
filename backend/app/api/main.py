from fastapi import APIRouter

from app.api.routes import items, login, private, users, utils, source_configs, llm_model_configs, llm_prompts, image_analyses
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(items.router)
api_router.include_router(source_configs.router)
api_router.include_router(llm_model_configs.router)
api_router.include_router(llm_prompts.router)
api_router.include_router(image_analyses.router)


if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)

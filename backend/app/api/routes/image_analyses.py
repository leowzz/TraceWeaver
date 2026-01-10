"""API routes for Image Analysis management."""

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from loguru import logger
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.connectors import registry
from app.crud.image_analysis import image_analysis_crud
from app.models.enums import AnalysisStatus, ImageSourceType, SourceType
from app.models.source_config import SourceConfig
from app.schemas.image_analysis import ImageAnalysesPublic, ImageAnalysisPublic

router = APIRouter(prefix="/image-analyses", tags=["image-analyses"])


@router.get("/", response_model=ImageAnalysesPublic)
def read_image_analyses(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
    status: AnalysisStatus | None = Query(
        None, description="Filter by analysis status"
    ),
) -> Any:
    """Retrieve Image Analyses."""
    analyses = image_analysis_crud.get_multi(
        session=session, skip=skip, limit=limit, status=status
    )
    count = image_analysis_crud.count(session=session, status=status)
    return ImageAnalysesPublic(
        data=[ImageAnalysisPublic.model_validate(a) for a in analyses],
        count=count,
    )


@router.get("/{id}", response_model=ImageAnalysisPublic)
def read_image_analysis(session: SessionDep, current_user: CurrentUser, id: int) -> Any:
    """Get Image Analysis by ID."""
    analysis = image_analysis_crud.get(session=session, id=id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Image Analysis not found")
    return analysis


@router.get("/{id}/image")
async def get_image_analysis_image(
    session: SessionDep, current_user: CurrentUser, id: int
) -> Response:
    """Get the image for an Image Analysis record.

    Streams the image bytes from the source system.
    """
    analysis = image_analysis_crud.get(session=session, id=id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Image Analysis not found")

    try:
        image_bytes = await _fetch_image_from_source(
            session, analysis.source_type, analysis.img_path
        )

        # Determine content type from path
        img_path = analysis.img_path.lower()
        if img_path.endswith(".png"):
            media_type = "image/png"
        elif img_path.endswith((".jpg", ".jpeg")):
            media_type = "image/jpeg"
        elif img_path.endswith(".gif"):
            media_type = "image/gif"
        elif img_path.endswith(".webp"):
            media_type = "image/webp"
        else:
            media_type = "image/png"  # Default

        return Response(content=image_bytes, media_type=media_type)

    except Exception as e:
        logger.error(f"Failed to fetch image for analysis {id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch image: {e}")


async def _fetch_image_from_source(
    session, source_type: ImageSourceType, img_path: str
) -> bytes:
    """Fetch image bytes from the source system."""
    if source_type != ImageSourceType.SIYUAN_LOCAL:
        raise ValueError(f"Image fetching from {source_type} is not yet supported")

    # Get source config for SiYuan
    statement = select(SourceConfig).where(
        SourceConfig.type == SourceType.SIYUAN, SourceConfig.is_active == True
    )
    source_config = session.exec(statement).first()
    if not source_config:
        raise ValueError("No active SiYuan source config found")

    # Get connector and fetch image
    connector = registry.get(source_config)
    from app.connectors.impl.siyuan_connector import SiYuanConnector

    if not isinstance(connector, SiYuanConnector):
        raise ValueError("Invalid connector type for SiYuan")

    client = connector._get_client()
    return await client.get_file(f"/data/{img_path}")

"""CRUD operations for Image Analysis model."""

from sqlmodel import Session, func, select

from app.crud.base import CRUDBase
from app.models.enums import AnalysisStatus
from app.models.image_analysis import ImageAnalysis


class ImageAnalysisCRUD(CRUDBase[ImageAnalysis, ImageAnalysis, ImageAnalysis]):
    def get_multi(
            self, session: Session, *, skip: int = 0, limit: int = 100, status: AnalysisStatus | None = None
    ) -> list[ImageAnalysis]:
        statement = select(ImageAnalysis)
        if status:
            statement = statement.where(ImageAnalysis.status == status)
        statement = statement.offset(skip).limit(limit).order_by(ImageAnalysis.created_at.desc())
        return list(session.exec(statement).all())

    def count(self, session: Session, status: AnalysisStatus | None = None) -> int:
        statement = select(func.count()).select_from(ImageAnalysis)
        if status:
            statement = statement.where(ImageAnalysis.status == status)
        return session.exec(statement).one()

    def get_by_img_path_status(
            self, session: Session, img_path: str, status: AnalysisStatus
    ) -> list[ImageAnalysis]:
        """Get all image analyses by image path and status.

        Args:
            session: Database session
            img_path: Image path
            status: Analysis status

        Returns:
            List of image analyses with the specified image path and status
        """
        statement = select(ImageAnalysis).where(
            ImageAnalysis.img_path == img_path, ImageAnalysis.status == status
        )
        return list(session.exec(statement).all())

    def get_by_img_path_status_prompt_id(
            self, session: Session, img_path: str, status: AnalysisStatus, llm_prompt_id: int
    ) -> list[ImageAnalysis]:
        """Get all image analyses by image path and status.

        Args:
            session: Database session
            img_path: Image path
            status: Analysis status
            llm_prompt_id: LLM prompt ID

        Returns:
            List of image analyses with the specified image path and status
        """
        statement = select(ImageAnalysis).where(
            ImageAnalysis.img_path == img_path,
            ImageAnalysis.status == status,
            ImageAnalysis.llm_prompt_id == llm_prompt_id
        )
        return list(session.exec(statement).all())


image_analysis_crud = ImageAnalysisCRUD(ImageAnalysis)

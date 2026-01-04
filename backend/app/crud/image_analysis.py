"""CRUD operations for Image Analysis model."""

from sqlmodel import Session, select

from app.crud.base import CRUDBase
from app.models.enums import AnalysisStatus
from app.models.image_analysis import ImageAnalysis


class ImageAnalysisCRUD(CRUDBase[ImageAnalysis, ImageAnalysis, ImageAnalysis]):
    """CRUD operations for Image Analysis."""

    def get_by_status(
        self, session: Session, status: AnalysisStatus
    ) -> list[ImageAnalysis]:
        """Get all image analyses by status.

        Args:
            session: Database session
            status: Analysis status

        Returns:
            List of image analyses with the specified status
        """
        statement = select(ImageAnalysis).where(ImageAnalysis.status == status)
        return list(session.exec(statement).all())
    
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


image_analysis_crud = ImageAnalysisCRUD(ImageAnalysis)


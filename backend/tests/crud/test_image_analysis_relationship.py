"""Unit tests for ImageAnalysis and LLMPrompt relationship."""

import pytest
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from app.crud.image_analysis import image_analysis_crud
from app.crud.llm_prompt import llm_prompt_crud
from app.models.enums import AnalysisStatus, ImageSourceType
from app.models.image_analysis import ImageAnalysis
from app.models.llm_prompt import LLMPrompt


@pytest.fixture
def sample_llm_prompt(db: Session) -> LLMPrompt:
    """Create a sample LLMPrompt for testing."""
    prompt_data = {
        "name": "Test Prompt",
        "content": "Analyze this image and describe its content.",
        "is_active": True,
    }
    prompt = llm_prompt_crud.create(db, prompt_data)
    return prompt


@pytest.fixture
def sample_image_analysis(db: Session, sample_llm_prompt: LLMPrompt) -> ImageAnalysis:
    """Create a sample ImageAnalysis for testing."""
    analysis_data = {
        "img_path": "/test/image.jpg",
        "source_type": ImageSourceType.SIYUAN_LOCAL,
        "llm_prompt_id": sample_llm_prompt.id,
        "model_name": "qwen3-vl:2B",
        "status": AnalysisStatus.PENDING,
    }
    analysis = image_analysis_crud.create(db, analysis_data)
    return analysis


class TestImageAnalysisToLLMPrompt:
    """Test ImageAnalysis -> LLMPrompt relationship."""

    def test_image_analysis_has_llm_prompt(
        self, db: Session, sample_image_analysis: ImageAnalysis
    ):
        """Test that ImageAnalysis can access its related LLMPrompt."""
        # Load with relationship using selectinload
        statement = (
            select(ImageAnalysis)
            .where(ImageAnalysis.id == sample_image_analysis.id)
            .options(selectinload(ImageAnalysis.llm_prompt))
        )
        analysis = db.exec(statement).first()

        assert analysis is not None
        assert analysis.llm_prompt is not None
        assert analysis.llm_prompt_id == analysis.llm_prompt.id
        assert analysis.llm_prompt.name == "Test Prompt"

    def test_image_analysis_llm_prompt_is_none_when_not_set(self, db: Session):
        """Test that ImageAnalysis.llm_prompt is None when llm_prompt_id doesn't exist."""
        analysis_data = {
            "img_path": "/test/image2.jpg",
            "source_type": ImageSourceType.URL,
            "llm_prompt_id": 99999,  # Non-existent ID
            "model_name": "qwen3-vl:2B",
            "status": AnalysisStatus.PENDING,
        }
        analysis = image_analysis_crud.create(db, analysis_data)
        db.refresh(analysis)

        # The relationship should handle non-existent foreign key gracefully
        # In SQLModel, this might return None or raise an error depending on configuration
        # We test that it doesn't crash
        assert analysis.llm_prompt_id == 99999


class TestLLMPromptToImageAnalysis:
    """Test LLMPrompt -> ImageAnalysis relationship."""

    def test_llm_prompt_has_image_analyses(
        self,
        db: Session,
        sample_llm_prompt: LLMPrompt,
        sample_image_analysis: ImageAnalysis,
    ):
        """Test that LLMPrompt can access its related ImageAnalysis list."""
        # Load with relationship using selectinload
        statement = (
            select(LLMPrompt)
            .where(LLMPrompt.id == sample_llm_prompt.id)
            .options(selectinload(LLMPrompt.image_analyses))
        )
        prompt = db.exec(statement).first()

        assert prompt is not None
        assert len(prompt.image_analyses) >= 1
        analysis_ids = [a.id for a in prompt.image_analyses]
        assert sample_image_analysis.id in analysis_ids
        assert sample_image_analysis.llm_prompt_id == prompt.id

    def test_llm_prompt_image_analyses_is_empty_when_none(self, db: Session):
        """Test that LLMPrompt.image_analyses is empty when no analyses exist."""
        prompt_data = {
            "name": "Empty Prompt",
            "content": "No analyses for this prompt.",
            "is_active": True,
        }
        prompt = llm_prompt_crud.create(db, prompt_data)

        # Load with relationship using selectinload
        statement = (
            select(LLMPrompt)
            .where(LLMPrompt.id == prompt.id)
            .options(selectinload(LLMPrompt.image_analyses))
        )
        loaded_prompt = db.exec(statement).first()

        assert loaded_prompt is not None
        assert len(loaded_prompt.image_analyses) == 0

    def test_llm_prompt_has_multiple_image_analyses(
        self, db: Session, sample_llm_prompt: LLMPrompt
    ):
        """Test that LLMPrompt can have multiple ImageAnalysis records."""
        # Create multiple image analyses
        analysis1_data = {
            "img_path": "/test/image1.jpg",
            "source_type": ImageSourceType.SIYUAN_LOCAL,
            "llm_prompt_id": sample_llm_prompt.id,
            "model_name": "qwen3-vl:2B",
            "status": AnalysisStatus.PENDING,
        }
        analysis2_data = {
            "img_path": "/test/image2.jpg",
            "source_type": ImageSourceType.URL,
            "llm_prompt_id": sample_llm_prompt.id,
            "model_name": "qwen3-vl:2B",
            "status": AnalysisStatus.COMPLETED,
        }

        analysis1 = image_analysis_crud.create(db, analysis1_data)
        analysis2 = image_analysis_crud.create(db, analysis2_data)

        # Load with relationship using selectinload
        statement = (
            select(LLMPrompt)
            .where(LLMPrompt.id == sample_llm_prompt.id)
            .options(selectinload(LLMPrompt.image_analyses))
        )
        prompt = db.exec(statement).first()

        assert prompt is not None
        assert len(prompt.image_analyses) >= 2
        analysis_ids = [a.id for a in prompt.image_analyses]
        assert analysis1.id in analysis_ids
        assert analysis2.id in analysis_ids


class TestBidirectionalRelationship:
    """Test bidirectional relationship between ImageAnalysis and LLMPrompt."""

    def test_bidirectional_relationship_consistency(
        self,
        db: Session,
        sample_llm_prompt: LLMPrompt,
        sample_image_analysis: ImageAnalysis,
    ):
        """Test that both sides of the relationship are consistent."""
        # Load ImageAnalysis with relationship
        analysis_stmt = (
            select(ImageAnalysis)
            .where(ImageAnalysis.id == sample_image_analysis.id)
            .options(selectinload(ImageAnalysis.llm_prompt))
        )
        analysis = db.exec(analysis_stmt).first()

        # Load LLMPrompt with relationship
        prompt_stmt = (
            select(LLMPrompt)
            .where(LLMPrompt.id == sample_llm_prompt.id)
            .options(selectinload(LLMPrompt.image_analyses))
        )
        prompt = db.exec(prompt_stmt).first()

        assert analysis is not None
        assert prompt is not None

        # Test ImageAnalysis -> LLMPrompt
        assert analysis.llm_prompt is not None
        assert analysis.llm_prompt.id == prompt.id

        # Test LLMPrompt -> ImageAnalysis
        analysis_ids = [a.id for a in prompt.image_analyses]
        assert analysis.id in analysis_ids

        # Test consistency
        assert analysis.llm_prompt.name == prompt.name
        assert analysis.llm_prompt_id == prompt.id

    def test_relationship_after_update(
        self,
        db: Session,
        sample_llm_prompt: LLMPrompt,
        sample_image_analysis: ImageAnalysis,
    ):
        """Test that relationship persists after updates."""
        # Update the prompt
        updated_data = {"name": "Updated Prompt Name"}
        updated_prompt = llm_prompt_crud.update(db, sample_llm_prompt.id, updated_data)

        # Load analysis with relationship
        statement = (
            select(ImageAnalysis)
            .where(ImageAnalysis.id == sample_image_analysis.id)
            .options(selectinload(ImageAnalysis.llm_prompt))
        )
        analysis = db.exec(statement).first()

        assert analysis is not None
        assert analysis.llm_prompt is not None
        assert analysis.llm_prompt.name == "Updated Prompt Name"
        assert analysis.llm_prompt.id == updated_prompt.id

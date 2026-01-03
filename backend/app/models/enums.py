"""Common enums used across the application."""

from enum import Enum


class SourceType(str, Enum):
    """Data source types."""

    GIT = "GIT"
    DAYFLOW = "DAYFLOW"
    SIYUAN = "SIYUAN"


class ImageSourceType(str, Enum):
    SIYUAN_LOCAL = "SIYUAN_LOCAL"
    URL = "URL"


class AnalysisStatus(str, Enum):
    """Image analysis task status."""

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class LLMProvider(str, Enum):
    """LLM/LLM model provider types.
    
    Note: All providers are accessed through agno framework as unified agent interface.
    The provider type indicates which underlying model service to use, but all calls
    go through agno Agent for consistency.
    """

    OPENAI = "OPENAI"
    ANTHROPIC = "ANTHROPIC"
    OLLAMA = "OLLAMA"
    # Add more providers as needed

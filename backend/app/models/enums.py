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

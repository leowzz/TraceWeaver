"""Common enums used across the application."""

from enum import Enum


class SourceType(str, Enum):
    """Data source types."""

    GIT = "GIT"
    DAYFLOW = "DAYFLOW"
    SIYUAN = "SIYUAN"

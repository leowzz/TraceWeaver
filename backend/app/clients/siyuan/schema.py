"""Pydantic schemas for SiYuan API responses."""

from pydantic import BaseModel, Field


class NotebookInfo(BaseModel):
    """Notebook information."""

    id: str = Field(..., description="Notebook ID")
    name: str = Field(..., description="Notebook name")
    icon: str = Field(..., description="Notebook icon (emoji code)")
    sort: int = Field(..., description="Sort order")
    closed: bool = Field(..., description="Whether the notebook is closed")


class ExportResult(BaseModel):
    """Export result for Markdown content."""

    hPath: str = Field(..., description="Human-readable path")
    content: str = Field(..., description="Markdown content")


class FileInfo(BaseModel):
    """File information."""

    isDir: bool = Field(..., description="Whether it is a directory")
    name: str = Field(..., description="File or directory name")


class SystemProgress(BaseModel):
    """System boot progress."""

    details: str = Field(..., description="Progress details")
    progress: int = Field(..., description="Progress percentage (0-100)")


class MessageResult(BaseModel):
    """Message push result."""

    id: str = Field(..., description="Message ID")


class DocumentInfo(BaseModel):
    """Document information (returned by create_doc_with_markdown)."""

    id: str = Field(..., description="Document ID")


class BlockInfo(BaseModel):
    """Block information (returned by block operations)."""

    id: str = Field(..., description="Block ID")


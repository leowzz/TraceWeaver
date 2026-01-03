from typing import Optional, List
from pydantic import BaseModel, Field


class SiYuanBlock(BaseModel):
    """Pydantic model representing a block in the SiYuan database."""
    id: str
    parent_id: Optional[str] = None
    root_id: Optional[str] = None
    box: str
    path: str
    hpath: str
    content: str
    markdown: Optional[str] = None
    type: str
    subtype: Optional[str] = None
    tag: Optional[str] = None
    alias: Optional[str] = None
    memo: Optional[str] = None
    created: str
    updated: str
    
    # Optional field for nested blocks or related content
    children: Optional[List["SiYuanBlock"]] = None


class SiYuanDocument(SiYuanBlock):
    """Pydantic model representing a SiYuan document (type='d')."""
    # Documents might have specific fields or nested content we want to expose
    pass


# Rebuild forward refs for recursive children
SiYuanBlock.model_rebuild()

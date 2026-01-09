"""Base chunker interface for text segmentation."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class Chunk:
    """Text chunk with metadata.
    
    Attributes:
        text: The chunk text content
        index: Position in the sequence of chunks
        metadata: Additional metadata about the chunk
    """
    
    text: str
    index: int
    metadata: Optional[dict[str, Any]] = None


class BaseChunker(ABC):
    """Abstract base class for text chunkers.
    
    All chunkers must implement the chunk() method to split text into chunks.
    """
    
    @abstractmethod
    def chunk(self, text: str, metadata: Optional[dict[str, Any]] = None) -> list[Chunk]:
        """Split text into chunks.
        
        Args:
            text: Input text to be chunked
            metadata: Optional metadata to attach to chunks
            
        Returns:
            List of Chunk objects
        """
        pass

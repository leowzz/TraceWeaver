"""Time block chunker for Dayflow timeline data."""

import re
from typing import Any, Optional

from app.services.chunkers.base import BaseChunker, Chunk


class TimeBlockChunker(BaseChunker):
    """Chunk text by time blocks in Dayflow detailed_summary format.
    
    Parses text like:
    7:36 PM - 7:37 PM exploring Dayflow application
    7:37 PM - 7:39 PM reviewing files...
    
    Each time block becomes a separate chunk.
    """
    
    # 匹配时间块格式：HH:MM AM/PM - HH:MM AM/PM description
    TIME_BLOCK_PATTERN = re.compile(
        r'^(\d{1,2}:\d{2}\s+(?:AM|PM))\s*-\s*(\d{1,2}:\d{2}\s+(?:AM|PM))\s+(.+)$',
        re.MULTILINE
    )
    
    def chunk(self, text: str, metadata: Optional[dict[str, Any]] = None) -> list[Chunk]:
        """Split text into time block chunks.
        
        Args:
            text: Detailed summary text with time blocks
            metadata: Optional metadata (e.g., day, title, category)
            
        Returns:
            List of Chunk objects, one per time block
        """
        if not text or not text.strip():
            return []
        
        chunks = []
        matches = list(self.TIME_BLOCK_PATTERN.finditer(text))
        
        if not matches:
            # If no time blocks found, treat entire text as single chunk
            chunks.append(Chunk(
                text=text.strip(),
                index=0,
                metadata=metadata or {}
            ))
            return chunks
        
        for idx, match in enumerate(matches):
            start_time = match.group(1)  # e.g., "7:36 PM"
            end_time = match.group(2)    # e.g., "7:37 PM"
            description = match.group(3)  # e.g., "exploring Dayflow application"
            
            # 构建 chunk 文本，包含时间信息和描述
            chunk_text = f"{start_time} - {end_time}: {description}"
            
            # 合并元数据
            chunk_metadata = metadata.copy() if metadata else {}
            chunk_metadata.update({
                "start_time": start_time,
                "end_time": end_time,
                "time_block_index": idx
            })
            
            chunks.append(Chunk(
                text=chunk_text,
                index=idx,
                metadata=chunk_metadata
            ))
        
        return chunks

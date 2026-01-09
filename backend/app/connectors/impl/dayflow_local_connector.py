"""Dayflow local connector - Fetches time tracking data from local SQLite database."""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from loguru import logger

from app.connectors.base import BaseConnector
from app.models.enums import SourceType
from app.schemas.activity import ActivityCreate


class DayflowLocalConfig:
    """Configuration for local Dayflow database."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path


class DayflowLocalConnector(BaseConnector):
    """Connector for local Dayflow SQLite database.
    
    Reads timeline_cards from local Dayflow backup database.
    """
    
    def __init__(self, config: DayflowLocalConfig):
        """Initialize Dayflow local connector with configuration.
        
        Args:
            config: DayflowLocalConfig with db_path
        """
        super().__init__(config)
        self.config: DayflowLocalConfig = config
    
    @property
    def source_type(self) -> str:
        return SourceType.DAYFLOW.value
    
    async def validate_config(self) -> bool:
        """Validate Dayflow local database configuration.
        
        Returns:
            True if valid
            
        Raises:
            ConnectionError: If cannot access database file
        """
        db_path = Path(self.config.db_path)
        
        if not db_path.exists():
            raise ConnectionError(f"Database file not found: {self.config.db_path}")
        
        if not db_path.is_file():
            raise ConnectionError(f"Path is not a file: {self.config.db_path}")
        
        # Try to open and query database
        try:
            conn = sqlite3.connect(self.config.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM timeline_cards WHERE is_deleted = 0")
            count = cursor.fetchone()[0]
            conn.close()
            
            logger.info(f"Found {count} timeline cards in local Dayflow database")
            return True
        except sqlite3.Error as e:
            raise ConnectionError(f"Failed to access Dayflow database: {e}")
    
    async def fetch_activities(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> list[ActivityCreate]:
        """Fetch timeline cards from local Dayflow database.
        
        Args:
            start_time: Start of time range (Unix timestamp)
            end_time: End of time range (Unix timestamp)
            
        Returns:
            List of activities representing timeline cards
        """
        conn = sqlite3.connect(self.config.db_path)
        conn.row_factory = sqlite3.Row  # Access columns by name
        cursor = conn.cursor()
        
        # Query timeline_cards
        query = """
        SELECT id, day, start_ts, end_ts, title, summary,
               category, subcategory, detailed_summary, metadata
        FROM timeline_cards
        WHERE is_deleted = 0
          AND start_ts >= ?
          AND end_ts <= ?
        ORDER BY start_ts
        """
        
        cursor.execute(query, (int(start_time.timestamp()), int(end_time.timestamp())))
        rows = cursor.fetchall()
        conn.close()
        
        activities = []
        for row in rows:
            card_id = row["id"]
            day = row["day"]
            start_ts = row["start_ts"]
            title = row["title"] or "Untitled activity"
            summary = row["summary"] or ""
            category = row["category"] or "Uncategorized"
            subcategory = row["subcategory"]
            detailed_summary = row["detailed_summary"] or ""
            metadata = row["metadata"]
            
            # Combine summary and detailed_summary for content
            content_parts = []
            if summary:
                content_parts.append(f"Summary: {summary}")
            if detailed_summary:
                content_parts.append(f"\nDetailed:\n{detailed_summary}")
            content = "\n".join(content_parts)
            
            # Convert Unix timestamp to datetime
            occurred_at = datetime.fromtimestamp(start_ts)
            
            activity = ActivityCreate(
                user_id=None,  # Will be set by service layer
                source_type=SourceType.DAYFLOW,
                source_id=f"dayflow_local_{card_id}",
                occurred_at=occurred_at,
                title=title,
                content=content,
                extra_data={
                    "day": day,
                    "category": category,
                    "subcategory": subcategory,
                    "start_ts": start_ts,
                    "end_ts": row["end_ts"],
                    "metadata": metadata,
                    "detailed_summary": detailed_summary,  # Keep for chunking
                },
                fingerprint=self.generate_fingerprint(
                    SourceType.DAYFLOW.value,
                    f"dayflow_local_{card_id}",
                    occurred_at,
                ),
            )
            activities.append(activity)
        
        logger.info(f"Fetched {len(activities)} timeline cards from local Dayflow database")
        return activities
    
    def fetch_all_activities(self) -> list[ActivityCreate]:
        """Fetch all timeline cards (synchronous version for CLI).
        
        Returns:
            List of all activities
        """
        try:
            conn = sqlite3.connect(self.config.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = """
            SELECT id, day, start_ts, end_ts, title, summary,
                category, subcategory, detailed_summary, metadata
            FROM timeline_cards
            WHERE is_deleted = 0
            ORDER BY start_ts
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            logger.info(f"Fetched {len(rows)} timeline cards from local Dayflow database")
            conn.close()
            
            activities = []
            for row in rows:
                card_id = row["id"]
                day = row["day"]
                start_ts = row["start_ts"]
                title = row["title"] or "Untitled activity"
                summary = row["summary"] or ""
                category = row["category"] or "Uncategorized"
                subcategory = row["subcategory"]
                detailed_summary = row["detailed_summary"] or ""
                metadata = row["metadata"]
                
                content_parts = []
                if summary:
                    content_parts.append(f"Summary: {summary}")
                if detailed_summary:
                    content_parts.append(f"\nDetailed:\n{detailed_summary}")
                content = "\n".join(content_parts)
                
                occurred_at = datetime.fromtimestamp(start_ts)
                
                activity = ActivityCreate(
                    user_id=None,
                    source_type=SourceType.DAYFLOW,
                    source_id=f"dayflow_local_{card_id}",
                    occurred_at=occurred_at,
                    title=title,
                    content=content,
                    extra_data={
                        "day": day,
                        "category": category,
                        "subcategory": subcategory,
                        "start_ts": start_ts,
                        "end_ts": row["end_ts"],
                        "metadata": metadata,
                        "detailed_summary": detailed_summary,
                    },
                    fingerprint=self.generate_fingerprint(
                        SourceType.DAYFLOW.value,
                        f"dayflow_local_{card_id}",
                        occurred_at,
                    ),
                )
                activities.append(activity)
            
            logger.info(f"Fetched {len(activities)} timeline cards from local Dayflow database")
            return activities
        except Exception as e:
            logger.exception(f"{e=}")
            return []

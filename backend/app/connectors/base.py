"""Base connector interface for all data sources.

Following the hexagonal architecture pattern, this module defines the port (interface)
that all adapters (concrete connectors) must implement.
"""

import hashlib
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Union

from app.schemas.activity import ActivityCreate


class BaseConnector(ABC):
    """Abstract base class that all data source connectors must implement.

    This interface ensures decoupling between the core business logic and external systems.
    """

    def __init__(self, config: Union["GitConfig", "DayflowConfig", "SiYuanConfig"]):
        """Initialize connector with configuration.

        Args:
            config: Data source configuration schema
        """
        self.config = config

    @property
    @abstractmethod
    def source_type(self) -> str:
        """Return the data source type identifier.

        Returns:
            str: One of "git", "dayflow", "siyuan"
        """
        pass

    @abstractmethod
    async def validate_config(self) -> bool:
        """Validate that the configuration is correct and can connect to the data source.

        Returns:
            bool: True if configuration is valid

        Raises:
            ValueError: If configuration format is invalid
            ConnectionError: If cannot connect to the data source
        """
        pass

    @abstractmethod
    async def fetch_activities(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> list[ActivityCreate]:
        """Fetch activities from the data source within the time range.
            start_time: Start of time range
            end_time: End of time range

        Returns:
            List of ActivityCreate objects

        Raises:
            ValueError: If configuration is invalid
            ConnectionError: If connection fails
        """
        pass

    def generate_fingerprint(
        self,
        source_type: str,
        source_id: str,
        occurred_at: datetime,
    ) -> str:
        """Generate a unique fingerprint for deduplication.

        Args:
            source_type: Data source type
            source_id: Unique ID from source
            occurred_at: When the activity occurred

        Returns:
            SHA256 hash string
        """
        content = f"{source_type}:{source_id}:{occurred_at.isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()

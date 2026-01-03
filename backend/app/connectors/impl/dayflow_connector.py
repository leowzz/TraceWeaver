"""Dayflow connector - Fetches time tracking data from Dayflow API."""

from datetime import datetime

import httpx

from app.connectors.base import BaseConnector
from app.models.enums import SourceType
from app.schemas.activity import ActivityCreate
from app.schemas.source_config import DayflowConfig


class DayflowConnector(BaseConnector):
    """Connector for Dayflow time tracking API."""

    def __init__(self, config: DayflowConfig):
        """Initialize Dayflow connector with configuration.

        Args:
            config: DayflowConfig with api_url and api_token
        """
        super().__init__(config)
        self.config: DayflowConfig = config

    @property
    def source_type(self) -> str:
        return SourceType.DAYFLOW.value

    async def validate_config(self) -> bool:
        """Validate Dayflow API configuration.

        Returns:
            True if valid

        Raises:
            ConnectionError: If cannot connect to API
        """
        # Test connection
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.config.api_url}/api/v1/health",
                    headers={"Authorization": f"Bearer {self.config.api_token}"},
                    timeout=5.0,
                )
                if response.status_code != 200:
                    raise ConnectionError(f"API returned status {response.status_code}")
                return True
        except httpx.HTTPError as e:
            raise ConnectionError(f"Failed to connect to Dayflow API: {e}")

    async def fetch_activities(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> list[ActivityCreate]:
        """Fetch time tracking entries from Dayflow API.

        Args:
            start_time: Start of time range
            end_time: End of time range

        Returns:
            List of activities representing time entries
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.config.api_url}/api/v1/entries",
                headers={"Authorization": f"Bearer {self.config.api_token}"},
                params={
                    "start_date": start_time.isoformat(),
                    "end_date": end_time.isoformat(),
                },
            )
            response.raise_for_status()
            entries = response.json()

        activities = []
        for entry in entries.get("data", []):
            # Extract entry details
            entry_id = entry["id"]
            title = entry.get("title", "Untitled activity")
            description = entry.get("description", "")
            started_at = datetime.fromisoformat(entry["started_at"])
            duration_minutes = entry.get("duration_minutes", 0)
            project = entry.get("project", "")
            tags = entry.get("tags", [])

            activity = ActivityCreate(
                user_id=None,  # Will be set by service layer
                source_type=SourceType.DAYFLOW,
                source_id=str(entry_id),
                occurred_at=started_at,
                title=title,
                content=description,
                extra_data={
                    "project": project,
                    "tags": tags,
                    "duration_minutes": duration_minutes,
                },
                fingerprint=self.generate_fingerprint(
                    SourceType.DAYFLOW.value,
                    str(entry_id),
                    started_at,
                ),
            )
            activities.append(activity)

        return activities

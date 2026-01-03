"""SiYuan connector - Fetches notes from SiYuan note-taking application."""

from datetime import datetime

import httpx
from fastapi import HTTPException
from loguru import logger
from app.connectors.base import BaseConnector
from app.models.enums import SourceType
from app.schemas.activity import ActivityCreate
from app.schemas.source_config import SiYuanConfig


class SiYuanConnector(BaseConnector):
    """Connector for SiYuan note-taking application API."""

    def __init__(self, config: SiYuanConfig):
        """Initialize SiYuan connector with configuration.

        Args:
            config: SiYuanConfig with api_url and api_token
        """
        super().__init__(config)
        self.config: SiYuanConfig = config

    @property
    def source_type(self) -> str:
        return SourceType.SIYUAN.value

    async def validate_config(self) -> bool:
        """Validate SiYuan API configuration.

        Returns:
            True if valid

        Raises:
            ValueError: If required fields are missing
            ConnectionError: If cannot connect to API
        """
        api_url = str(self.config.api_url)
        api_token = self.config.api_token

        # Test connection
        try:
            async with httpx.AsyncClient(base_url=api_url) as client:
                logger.debug(f"Testing SiYuan connection to {api_url}")
                response = await client.post(
                    "/api/system/version",
                    headers={"Authorization": f"Token {api_token}"},
                    timeout=5.0,
                )
                if response.status_code != 200:
                    raise ConnectionError(f"API returned status {response.status_code}")
                logger.info(f"SiYuan connection successful: {response.text}")
                return True
        except httpx.HTTPError as e:
            raise ConnectionError(f"Failed to connect to SiYuan API: {e}")

    async def fetch_activities(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> list[ActivityCreate]:
        """Fetch notes from SiYuan API.

        Args:
            start_time: Start of time range
            end_time: End of time range

        Returns:
            List of activities representing notes
        """
        api_url = str(self.config.api_url)
        api_token = self.config.api_token

        # Query notes created or updated in the time range
        async with httpx.AsyncClient(base_url=api_url) as client:
            response = await client.post(
                "/api/query/sql",
                headers={"Authorization": f"Token {api_token}"},
                json={
                    "stmt": f"""
                        SELECT * FROM blocks 
                        WHERE type='d' 
                        AND (created >= '{start_time.strftime("%Y%m%d%H%M%S")}' 
                             OR updated >= '{start_time.strftime("%Y%m%d%H%M%S")}')
                        AND (created <= '{end_time.strftime("%Y%m%d%H%M%S")}' 
                             OR updated <= '{end_time.strftime("%Y%m%d%H%M%S")}')
                        ORDER BY created DESC
                    """
                },
            )
            response.raise_for_status()
            notes = response.json()

        activities = []
        for note in notes.get("data", []):
            # Extract note details
            note_id = note["id"]
            title = note.get("content", "Untitled note")[
                :100
            ]  # First 100 chars as title
            content = note.get("markdown", "")
            created_str = note.get("created", "")

            # Parse SiYuan timestamp format (YYYYMMDDHHmmSS)
            try:
                occurred_at = datetime.strptime(created_str, "%Y%m%d%H%M%S")
            except (ValueError, TypeError):
                occurred_at = start_time

            # Extract metadata
            notebook = note.get("box", "")
            path = note.get("hpath", "")
            tags_str = note.get("tag", "")
            tags = [tag.strip() for tag in tags_str.split(",") if tag.strip()]

            activity = ActivityCreate(
                user_id=None,  # Will be set by service layer
                source_type=SourceType.SIYUAN,
                source_id=note_id,
                occurred_at=occurred_at,
                title=title,
                content=content,
                extra_data={
                    "notebook": notebook,
                    "path": path,
                    "tags": tags,
                },
                fingerprint=self.generate_fingerprint(
                    SourceType.SIYUAN.value,
                    note_id,
                    occurred_at,
                ),
            )
            activities.append(activity)

        return activities
    
    async def test_connection(self):
        try:
            await self.validate_config()
            return True
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

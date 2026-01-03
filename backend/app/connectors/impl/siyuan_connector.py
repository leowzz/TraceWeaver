"""SiYuan connector - Fetches notes from SiYuan note-taking application."""

from datetime import datetime

import httpx
from fastapi import HTTPException
from loguru import logger
from app.connectors.base import BaseConnector
from app.core.context import ctx
from app.models.enums import SourceType
from app.schemas.activity import ActivityCreate
from app.schemas.source_config import SiYuanConfig
from app.schemas.siyuan import SiYuanBlock


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
        """Fetch full documents from SiYuan API.

        Step 1: Find document IDs created/updated in the time range.
        Step 2: Fetch all component blocks for those documents.
        Step 3: Aggregate content.
        """
        api_url = str(self.config.api_url)
        api_token = self.config.api_token

        # Step 1: Query document IDs created or updated in the time range
        async with httpx.AsyncClient(base_url=api_url) as client:
            response = await client.post(
                "/api/query/sql",
                headers={"Authorization": f"Token {api_token}"},
                json={
                    "stmt": f"""
                        SELECT id FROM blocks 
                        WHERE type='d' 
                        AND (
                            (created >= '{start_time.strftime("%Y%m%d%H%M%S")}' AND created <= '{end_time.strftime("%Y%m%d%H%M%S")}')
                            OR 
                            (updated >= '{start_time.strftime("%Y%m%d%H%M%S")}' AND updated <= '{end_time.strftime("%Y%m%d%H%M%S")}')
                        )
                        ORDER BY updated DESC
                    """
                },
            )
            response.raise_for_status()
            doc_rows = response.json().get("data", [])

        if not doc_rows:
            return []

        doc_ids = [row["id"] for row in doc_rows]
        doc_ids_str = ", ".join([f"'{d}'" for d in doc_ids])

        # Step 2: Fetch all constituent blocks for these documents
        async with httpx.AsyncClient(base_url=api_url) as client:
            response = await client.post(
                "/api/query/sql",
                headers={"Authorization": f"Token {api_token}"},
                json={
                    "stmt": f"""
                        SELECT * FROM blocks 
                        WHERE root_id IN ({doc_ids_str})
                        ORDER BY root_id, hpath, id
                    """
                },
            )
            response.raise_for_status()
            all_blocks_data = response.json().get("data", [])

        # Step 3: Aggregate blocks by document (root_id)
        docs_agg: dict[str, dict] = {}
        for block_data in all_blocks_data:
            try:
                block = SiYuanBlock.model_validate(block_data)
                root_id = block.root_id
                
                # If it's the document block itself, initialize doc info
                if block.type == 'd':
                    docs_agg[block.id] = {
                        "info": block,
                        "markdown_parts": []
                    }
                
                # Append markdown if present, otherwise content
                if root_id in docs_agg:
                    content_part = block.markdown or block.content
                    if content_part:
                        docs_agg[root_id]["markdown_parts"].append(content_part)
            except Exception as e:
                logger.error(f"Failed to parse SiYuan block: {e}")
                continue

        activities = []
        for doc_id, doc_data in docs_agg.items():
            doc = doc_data["info"]
            full_content = "\n\n".join(doc_data["markdown_parts"])
            
            # Extract basic info from the document block
            title = doc.content[:100]
            created_str = doc.created
            
            try:
                occurred_at = datetime.strptime(created_str, "%Y%m%d%H%M%S")
            except (ValueError, TypeError):
                occurred_at = start_time

            tags_str = doc.tag or ""
            tags = [tag.strip() for tag in tags_str.split(",") if tag.strip()]

            activity = ActivityCreate(
                user_id=ctx.user_id,
                source_type=SourceType.SIYUAN,
                source_id=doc_id,
                occurred_at=occurred_at,
                title=title,
                content=full_content,
                extra_data={
                    "notebook": doc.box,
                    "path": doc.hpath,
                    "tags": tags,
                    "memo": doc.memo,
                    "alias": doc.alias,
                },
                fingerprint=self.generate_fingerprint(
                    SourceType.SIYUAN.value,
                    doc_id,
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

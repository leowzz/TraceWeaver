"""SiYuan connector - Fetches notes from SiYuan note-taking application."""

from datetime import datetime

from fastapi import HTTPException
from loguru import logger
from app.clients.siyuan import SiYuanClient, SiYuanAPIError
from app.connectors.base import BaseConnector
from app.core.context import ctx
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
        self._client: SiYuanClient | None = None

    def _get_client(self) -> SiYuanClient:
        """Get or create SiYuan client."""
        if self._client is None:
            self._client = SiYuanClient(
                api_url=str(self.config.api_url),
                api_token=self.config.api_token,
            )
        return self._client

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
        client = self._get_client()
        try:
            logger.debug(f"Testing SiYuan connection to {self.config.api_url}")
            version = await client.get_version()
            logger.info(f"SiYuan connection successful, version: {version}")
            return True
        except SiYuanAPIError as e:
            raise ConnectionError(f"SiYuan API error: {e.msg}") from e
        except Exception as e:
            raise ConnectionError(f"Failed to connect to SiYuan API: {e}") from e

    async def fetch_activities(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> list[ActivityCreate]:
        """Fetch full documents from SiYuan API.

        Step 1: Find document IDs created/updated in the time range using SQL.
        Step 2: For each document, use export_md_content to get full Markdown content.
        Step 3: Get document metadata using get_block_kramdown or SQL for document block.
        """
        client = self._get_client()

        # Step 1: Query document IDs created or updated in the time range
        # Note: We still need SQL here as there's no time-range query API
        start_str = start_time.strftime("%Y%m%d%H%M%S")
        end_str = end_time.strftime("%Y%m%d%H%M%S")
        
        doc_rows = await client.query_sql(f"""
            SELECT id, created, updated, content, box, hpath, tag, memo, alias
            FROM blocks 
            WHERE type='d' 
            AND (
                (created >= '{start_str}' AND created <= '{end_str}')
                OR 
                (updated >= '{start_str}' AND updated <= '{end_str}')
            )
            ORDER BY updated DESC
        """)

        if not doc_rows:
            return []

        activities = []
        for doc_row in doc_rows:
            doc_id = doc_row["id"]
            
            try:
                # Step 2: Export document as Markdown using the client API
                export_result = await client.export_md_content(doc_id)
                full_content = export_result.content
                hpath = export_result.hPath
                
                # Step 3: Extract metadata from the document row
                title = doc_row.get("content", "")[:100] or hpath.split("/")[-1] or "Untitled"
                created_str = doc_row.get("created", "")
                
                try:
                    occurred_at = datetime.strptime(created_str, "%Y%m%d%H%M%S")
                except (ValueError, TypeError):
                    occurred_at = start_time

                tags_str = doc_row.get("tag", "") or ""
                tags = [tag.strip() for tag in tags_str.split(",") if tag.strip()]

                activity = ActivityCreate(
                    user_id=ctx.user_id,
                    source_type=SourceType.SIYUAN,
                    source_id=doc_id,
                    occurred_at=occurred_at,
                    title=title,
                    content=full_content,
                    extra_data={
                        "notebook": doc_row.get("box", ""),
                        "path": hpath,
                        "tags": tags,
                        "memo": doc_row.get("memo", ""),
                        "alias": doc_row.get("alias", ""),
                    },
                    fingerprint=self.generate_fingerprint(
                        SourceType.SIYUAN.value,
                        doc_id,
                        occurred_at,
                    ),
                )
                activities.append(activity)
            except Exception as e:
                logger.error(f"Failed to fetch document {doc_id}: {e}")
                continue

        return activities

    async def test_connection(self):
        try:
            await self.validate_config()
            return True
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

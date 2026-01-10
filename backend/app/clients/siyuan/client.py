"""SiYuan API client implementation."""

import httpx
from loguru import logger

from app.clients.siyuan.schema import (
    BlockInfo,
    DocumentInfo,
    ExportResult,
    FileInfo,
    MessageResult,
    NotebookInfo,
    SystemProgress,
)


class SiYuanAPIError(Exception):
    """Exception raised when SiYuan API returns an error."""

    def __init__(self, code: int, msg: str):
        self.code = code
        self.msg = msg
        super().__init__(f"SiYuan API error (code={code}): {msg}")


class SiYuanClient:
    """Client for SiYuan kernel API.

    Provides type-safe Python interface to SiYuan note-taking application API.
    All methods are async and return typed data.
    """

    def __init__(self, api_url: str, api_token: str, timeout: float = 30.0):
        """Initialize SiYuan client.

        Args:
            api_url: SiYuan API base URL (e.g., "http://localhost:6806")
            api_token: API authentication token
            timeout: Request timeout in seconds (default: 30.0)
        """
        self.api_url = api_url.rstrip("/")
        self.api_token = api_token
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.api_url,
                timeout=self.timeout,
            )
        return self._client

    async def _request(
        self, route: str, data: dict | None = None, files: dict | None = None
    ) -> dict:
        """Internal method to make API requests.

        Args:
            route: API route (e.g., "/api/notebook/lsNotebooks")
            data: Request JSON data
            files: Files for multipart/form-data uploads

        Returns:
            Response data dictionary

        Raises:
            SiYuanAPIError: If API returns an error (code != 0)
            httpx.HTTPError: If HTTP request fails
        """
        client = await self._get_client()
        headers = {"Authorization": f"Token {self.api_token}"}

        try:
            if files:
                response = await client.post(
                    route,
                    headers=headers,
                    data=data,
                    files=files,
                )
            else:
                headers["Content-Type"] = "application/json"
                response = await client.post(
                    route,
                    headers=headers,
                    json=data or {},
                )
            response.raise_for_status()
            result = response.json()

            if result.get("code", 0) != 0:
                raise SiYuanAPIError(
                    code=result.get("code", -1),
                    msg=result.get("msg", "Unknown error"),
                )

            return result.get("data", {})
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error calling {route}: {e}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error calling {route}: {e}")
            raise

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    # Notebook operations

    async def ls_notebooks(self) -> list[NotebookInfo]:
        """List all notebooks.

        Returns:
            List of notebook information
        """
        data = await self._request("/api/notebook/lsNotebooks")
        notebooks = data.get("notebooks", [])
        return [NotebookInfo.model_validate(nb) for nb in notebooks]

    async def open_notebook(self, notebook_id: str) -> None:
        """Open a notebook.

        Args:
            notebook_id: Notebook ID to open
        """
        await self._request("/api/notebook/openNotebook", {"notebook": notebook_id})

    async def close_notebook(self, notebook_id: str) -> None:
        """Close a notebook.

        Args:
            notebook_id: Notebook ID to close
        """
        await self._request("/api/notebook/closeNotebook", {"notebook": notebook_id})

    async def rename_notebook(self, notebook_id: str, name: str) -> None:
        """Rename a notebook.

        Args:
            notebook_id: Notebook ID
            name: New notebook name
        """
        await self._request(
            "/api/notebook/renameNotebook", {"notebook": notebook_id, "name": name}
        )

    async def create_notebook(self, name: str) -> NotebookInfo:
        """Create a new notebook.

        Args:
            name: Notebook name

        Returns:
            Created notebook information
        """
        data = await self._request("/api/notebook/createNotebook", {"name": name})
        notebook = data.get("notebook", {})
        return NotebookInfo.model_validate(notebook)

    async def remove_notebook(self, notebook_id: str) -> None:
        """Remove a notebook.

        Args:
            notebook_id: Notebook ID to remove
        """
        await self._request("/api/notebook/removeNotebook", {"notebook": notebook_id})

    async def get_notebook_conf(self, notebook_id: str) -> dict:
        """Get notebook configuration.

        Args:
            notebook_id: Notebook ID

        Returns:
            Notebook configuration dictionary
        """
        return await self._request(
            "/api/notebook/getNotebookConf", {"notebook": notebook_id}
        )

    async def set_notebook_conf(self, notebook_id: str, conf: dict) -> None:
        """Set notebook configuration.

        Args:
            notebook_id: Notebook ID
            conf: Configuration dictionary
        """
        await self._request(
            "/api/notebook/setNotebookConf", {"notebook": notebook_id, "conf": conf}
        )

    # Document operations

    async def create_doc_with_markdown(
        self, notebook_id: str, path: str, markdown: str
    ) -> DocumentInfo:
        """Create a document from Markdown.

        Args:
            notebook_id: Notebook ID
            path: Document path
            markdown: Markdown content

        Returns:
            Created document information
        """
        data = await self._request(
            "/api/filetree/createDocWithMd",
            {
                "notebook": notebook_id,
                "path": path,
                "markdown": markdown,
            },
        )
        return DocumentInfo.model_validate(data)

    async def rename_doc(self, notebook_id: str, path: str, title: str) -> None:
        """Rename a document.

        Args:
            notebook_id: Notebook ID
            path: Document path
            title: New document title
        """
        await self._request(
            "/api/filetree/renameDoc",
            {
                "notebook": notebook_id,
                "path": path,
                "title": title,
            },
        )

    async def remove_doc(self, notebook_id: str, doc_id: str) -> None:
        """Remove a document.

        Args:
            notebook_id: Notebook ID
            doc_id: Document ID
        """
        await self._request(
            "/api/filetree/removeDoc",
            {
                "notebook": notebook_id,
                "id": doc_id,
            },
        )

    async def move_doc(
        self,
        notebook_id: str,
        src_doc_id: str,
        target_notebook_id: str,
        target_path: str,
    ) -> None:
        """Move a document.

        Args:
            notebook_id: Source notebook ID
            src_doc_id: Source document ID
            target_notebook_id: Target notebook ID
            target_path: Target document path
        """
        await self._request(
            "/api/filetree/moveDoc",
            {
                "notebook": notebook_id,
                "srcID": src_doc_id,
                "targetNotebook": target_notebook_id,
                "targetPath": target_path,
            },
        )

    async def get_hpath_by_path(self, notebook_id: str, path: str) -> str:
        """Get human-readable path by path.

        Args:
            notebook_id: Notebook ID
            path: Document path

        Returns:
            Human-readable path
        """
        data = await self._request(
            "/api/filetree/getHPathByPath",
            {
                "notebook": notebook_id,
                "path": path,
            },
        )
        return data

    async def get_hpath_by_id(self, doc_id: str) -> str:
        """Get human-readable path by document ID.

        Args:
            doc_id: Document ID

        Returns:
            Human-readable path
        """
        data = await self._request("/api/filetree/getHPathByID", {"id": doc_id})
        return data

    # Block operations

    async def insert_block(
        self,
        parent_id: str,
        data: str,
        data_type: str,
        previous_id: str | None = None,
    ) -> BlockInfo:
        """Insert a block.

        Args:
            parent_id: Parent block ID
            data: Block data/content
            data_type: Block data type (e.g., "markdown", "dom")
            previous_id: Previous block ID (optional, for ordering)

        Returns:
            Created block information
        """
        request_data: dict = {
            "parentID": parent_id,
            "data": data,
            "dataType": data_type,
        }
        if previous_id:
            request_data["previousID"] = previous_id

        result = await self._request("/api/block/insertBlock", request_data)
        return BlockInfo.model_validate(result)

    async def prepend_block(
        self, parent_id: str, data: str, data_type: str
    ) -> BlockInfo:
        """Prepend a block (insert as first child).

        Args:
            parent_id: Parent block ID
            data: Block data/content
            data_type: Block data type

        Returns:
            Created block information
        """
        result = await self._request(
            "/api/block/prependBlock",
            {
                "parentID": parent_id,
                "data": data,
                "dataType": data_type,
            },
        )
        return BlockInfo.model_validate(result)

    async def append_block(
        self, parent_id: str, data: str, data_type: str
    ) -> BlockInfo:
        """Append a block (insert as last child).

        Args:
            parent_id: Parent block ID
            data: Block data/content
            data_type: Block data type

        Returns:
            Created block information
        """
        result = await self._request(
            "/api/block/appendBlock",
            {
                "parentID": parent_id,
                "data": data,
                "dataType": data_type,
            },
        )
        return BlockInfo.model_validate(result)

    async def update_block(self, block_id: str, data: str, data_type: str) -> None:
        """Update a block.

        Args:
            block_id: Block ID
            data: New block data/content
            data_type: Block data type
        """
        await self._request(
            "/api/block/updateBlock",
            {
                "id": block_id,
                "data": data,
                "dataType": data_type,
            },
        )

    async def delete_block(self, block_id: str) -> None:
        """Delete a block.

        Args:
            block_id: Block ID to delete
        """
        await self._request("/api/block/deleteBlock", {"id": block_id})

    async def move_block(
        self,
        block_id: str,
        target_parent_id: str,
        previous_id: str | None = None,
    ) -> None:
        """Move a block.

        Args:
            block_id: Block ID to move
            target_parent_id: Target parent block ID
            previous_id: Previous block ID for ordering (optional)
        """
        request_data: dict = {
            "id": block_id,
            "targetParentID": target_parent_id,
        }
        if previous_id:
            request_data["previousID"] = previous_id

        await self._request("/api/block/moveBlock", request_data)

    async def get_block_kramdown(self, block_id: str) -> str:
        """Get block kramdown source.

        Args:
            block_id: Block ID

        Returns:
            Kramdown source code
        """
        data = await self._request("/api/block/getBlockKramdown", {"id": block_id})
        return data

    async def get_child_blocks(self, block_id: str) -> list[dict]:
        """Get child blocks.

        Args:
            block_id: Parent block ID

        Returns:
            List of child block dictionaries
        """
        data = await self._request("/api/block/getChildBlocks", {"id": block_id})
        return data

    async def transfer_block_ref(
        self, from_block_id: str, to_block_id: str, ref_ids: list[str]
    ) -> None:
        """Transfer block references.

        Args:
            from_block_id: Source block ID
            to_block_id: Target block ID
            ref_ids: List of reference IDs to transfer
        """
        await self._request(
            "/api/block/transferBlockRef",
            {
                "fromID": from_block_id,
                "toID": to_block_id,
                "refIDs": ref_ids,
            },
        )

    # Attribute operations

    async def set_block_attr(self, block_id: str, name: str, value: str) -> None:
        """Set block attribute.

        Args:
            block_id: Block ID
            name: Attribute name
            value: Attribute value
        """
        await self._request(
            "/api/attr/setBlockAttrs",
            {
                "id": block_id,
                "attrs": {name: value},
            },
        )

    async def get_block_attr(self, block_id: str, name: str) -> str:
        """Get block attribute.

        Args:
            block_id: Block ID
            name: Attribute name

        Returns:
            Attribute value
        """
        data = await self._request(
            "/api/attr/getBlockAttrs",
            {
                "id": block_id,
                "name": name,
            },
        )
        return data

    # SQL query

    async def query_sql(self, stmt: str) -> list[dict]:
        """Execute SQL query.

        Args:
            stmt: SQL statement

        Returns:
            Query results as list of dictionaries
        """
        data = await self._request("/api/query/sql", {"stmt": stmt})
        return data

    # Export operations

    async def export_md_content(self, doc_id: str) -> ExportResult:
        """Export document as Markdown.

        Args:
            doc_id: Document block ID

        Returns:
            Export result with human-readable path and content
        """
        data = await self._request("/api/export/exportMdContent", {"id": doc_id})
        return ExportResult.model_validate(data)

    # File operations

    async def get_file(self, path: str) -> bytes:
        """Get file content.

        Args:
            path: File path (relative to workspace)

        Returns:
            File content as bytes
        """
        client = await self._get_client()
        headers = {"Authorization": f"Token {self.api_token}"}

        response = await client.post(
            "/api/file/getFile",
            headers=headers,
            json={"path": path},
        )
        response.raise_for_status()
        return response.content

    async def put_file(
        self,
        path: str,
        file: bytes | str,
        is_dir: bool = False,
        mod_time: int | None = None,
    ) -> None:
        """Put file (upload or create directory).

        Args:
            path: File path (relative to workspace)
            file: File content (bytes or string). Ignored if is_dir is True
            is_dir: Whether to create a directory instead
            mod_time: Modification time (Unix timestamp). Optional
        """
        client = await self._get_client()
        headers = {"Authorization": f"Token {self.api_token}"}

        data = {"path": path, "isDir": is_dir}
        if mod_time is not None:
            data["modTime"] = mod_time

        files = None
        if not is_dir:
            files = {"file": file}

        response = await client.post(
            "/api/file/putFile",
            headers=headers,
            data=data,
            files=files,
        )
        response.raise_for_status()

        result = response.json()
        if result.get("code", 0) != 0:
            raise SiYuanAPIError(
                code=result.get("code", -1),
                msg=result.get("msg", "Unknown error"),
            )

    async def remove_file(self, path: str) -> None:
        """Remove file or directory.

        Args:
            path: File path (relative to workspace)
        """
        await self._request("/api/file/removeFile", {"path": path})

    async def rename_file(self, path: str, new_path: str) -> None:
        """Rename file or directory.

        Args:
            path: Current file path
            new_path: New file path
        """
        await self._request(
            "/api/file/renameFile",
            {
                "path": path,
                "newPath": new_path,
            },
        )

    async def read_dir(self, path: str) -> list[FileInfo]:
        """List directory contents.

        Args:
            path: Directory path (relative to workspace)

        Returns:
            List of file/directory information
        """
        data = await self._request("/api/file/readDir", {"path": path})
        return [FileInfo.model_validate(item) for item in data]

    # System operations

    async def get_boot_progress(self) -> SystemProgress:
        """Get system boot progress.

        Returns:
            Boot progress information
        """
        data = await self._request("/api/system/bootProgress")
        return SystemProgress.model_validate(data)

    async def get_version(self) -> str:
        """Get system version.

        Returns:
            System version string
        """
        return await self._request("/api/system/version")

    async def get_current_time(self) -> int:
        """Get current system time.

        Returns:
            Current time as milliseconds since epoch
        """
        return await self._request("/api/system/currentTime")

    # Notification operations

    async def push_msg(self, msg: str, timeout: int = 7000) -> MessageResult:
        """Push notification message.

        Args:
            msg: Message content
            timeout: Message display timeout in milliseconds (default: 7000)

        Returns:
            Message result with message ID
        """
        data = await self._request(
            "/api/notification/pushMsg",
            {
                "msg": msg,
                "timeout": timeout,
            },
        )
        return MessageResult.model_validate(data)

    async def push_err_msg(self, msg: str, timeout: int = 7000) -> MessageResult:
        """Push error notification message.

        Args:
            msg: Error message content
            timeout: Message display timeout in milliseconds (default: 7000)

        Returns:
            Message result with message ID
        """
        data = await self._request(
            "/api/notification/pushErrMsg",
            {
                "msg": msg,
                "timeout": timeout,
            },
        )
        return MessageResult.model_validate(data)

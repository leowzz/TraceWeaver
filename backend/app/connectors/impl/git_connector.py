"""Git connector - Fetches commit history from Git repositories."""

import os
from datetime import datetime

from git import Repo
from git.exc import GitError

from app.connectors.base import BaseConnector
from app.models.enums import SourceType
from app.schemas.activity import ActivityCreate
from app.schemas.source_config import GitConfig


class GitConnector(BaseConnector):
    """Connector for Git repositories."""

    def __init__(self, config: GitConfig):
        """Initialize Git connector with configuration.

        Args:
            config: GitConfig with repo_path and branch
        """
        super().__init__(config)
        self.config: GitConfig = config

    @property
    def source_type(self) -> str:
        return SourceType.GIT.value

    async def validate_config(self) -> bool:
        """Validate Git repository configuration.

        Returns:
            True if valid

        Raises:
            ValueError: If repo_path is invalid
            ConnectionError: If repository is invalid
        """
        if not os.path.exists(self.config.repo_path):
            raise ConnectionError(
                f"Repository path does not exist: {self.config.repo_path}"
            )

        try:
            repo = Repo(self.config.repo_path)
            if repo.bare:
                raise ConnectionError(f"Repository is bare: {self.config.repo_path}")
            return True
        except GitError as e:
            raise ConnectionError(f"Invalid git repository: {e}")

    async def fetch_activities(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> list[ActivityCreate]:
        """Fetch commit history from Git repository.

        Args:
            start_time: Start of time range
            end_time: End of time range

        Returns:
            List of activities representing commits
        """
        repo = Repo(self.config.repo_path)

        # Try to checkout the branch, but don't fail if it doesn't exist
        try:
            repo.git.checkout(self.config.branch)
        except GitError:
            # Use current branch if specified branch doesn't exist
            self.config.branch = repo.active_branch.name

        activities = []
        for commit in repo.iter_commits(
            rev=self.config.branch,
            since=start_time,
            until=end_time,
        ):
            # Extract commit message first line as title
            message_lines = commit.message.strip().split("\n")
            title = message_lines[0] if message_lines else "No message"

            activity = ActivityCreate(
                user_id=None,  # Will be set by the service layer
                source_type=SourceType.GIT,
                source_id=commit.hexsha,
                occurred_at=commit.authored_datetime,
                title=title,
                content=commit.message,
                extra_data={
                    "repo": os.path.basename(self.config.repo_path),
                    "branch": self.config.branch,
                    "author": commit.author.name,
                    "email": commit.author.email,
                    "files_changed": len(commit.stats.files),
                    "insertions": commit.stats.total["insertions"],
                    "deletions": commit.stats.total["deletions"],
                },
                fingerprint=self.generate_fingerprint(
                    SourceType.GIT.value,
                    commit.hexsha,
                    commit.authored_datetime,
                ),
            )
            activities.append(activity)

        return activities

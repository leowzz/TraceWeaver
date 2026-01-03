"""Connector initialization - Register all connectors."""

from app.connectors.impl.git_connector import GitConnector
from app.connectors.impl.dayflow_connector import DayflowConnector
from app.connectors.impl.siyuan_connector import SiYuanConnector
from app.connectors.registry import registry
from app.models import SourceType
# Register all connectors
registry.register(SourceType.GIT, GitConnector)
registry.register(SourceType.DAYFLOW, DayflowConnector)
registry.register(SourceType.SIYUAN, SiYuanConnector)

__all__ = ["registry", "GitConnector", "DayflowConnector", "SiYuanConnector"]

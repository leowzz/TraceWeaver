"""Connector initialization - Register all connectors."""

from app.connectors.impl.git_connector import GitConnector
from app.connectors.impl.dayflow_connector import DayflowConnector
from app.connectors.impl.siyuan_connector import SiYuanConnector
from app.connectors.registry import registry

# Register all connectors
registry.register("git", GitConnector)
registry.register("dayflow", DayflowConnector)
registry.register("siyuan", SiYuanConnector)

__all__ = ["registry", "GitConnector", "DayflowConnector", "SiYuanConnector"]

"""Connector registry - Factory pattern for managing connectors."""

from typing import Type

from app.connectors.base import BaseConnector


class ConnectorRegistry:
    """Factory for creating and managing data source connectors."""

    def __init__(self):
        self._connectors: dict[str, Type[BaseConnector]] = {}

    def register(self, source_type: str, connector_class: Type[BaseConnector]):
        """Register a connector class for a data source type.

        Args:
            source_type: Data source type identifier
            connector_class: Connector class to register
        """
        self._connectors[source_type] = connector_class

    def get(self, source_type: str, config) -> BaseConnector:
        """Get a connector instance for the specified source type.

        Args:
            source_type: Data source type
            config: Configuration schema for the connector

        Returns:
            Connector instance

        Raises:
            ValueError: If source type is not registered
        """
        if source_type not in self._connectors:
            raise ValueError(f"Unknown connector type: {source_type}")
        return self._connectors[source_type](config)

    def list_types(self) -> list[str]:
        """List all registered connector types.

        Returns:
            List of source type identifiers
        """
        return list(self._connectors.keys())


# Global registry instance
registry = ConnectorRegistry()

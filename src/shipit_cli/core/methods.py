"""Shipping methods operations."""

from shipit_cli.core.client import ShipitClient


def list_methods(client: ShipitClient) -> list[dict]:
    """List all available shipping methods."""
    return client._request("/list-methods")

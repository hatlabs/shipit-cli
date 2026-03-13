"""Shipping methods operations."""

from shipit_cli.core.client import ShipitClient


def list_methods(client: ShipitClient) -> list[dict]:
    """List all available shipping methods."""
    return client._request("/list-methods")


def quote_methods(client: ShipitClient, data: dict) -> dict:
    """Get shipping methods with prices for a shipment (POST /shipping-methods)."""
    return client._request("/shipping-methods", method="POST", data=data)

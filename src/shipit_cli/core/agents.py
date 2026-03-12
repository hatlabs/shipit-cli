"""Service point (agent) operations."""

from shipit_cli.core.client import ShipitClient


def search_agents(client: ShipitClient, data: dict) -> list:
    """Search for service points / pickup locations."""
    return client._request("/agents", method="POST", data=data)

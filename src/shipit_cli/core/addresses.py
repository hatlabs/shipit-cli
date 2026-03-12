"""Address operations."""

from shipit_cli.core.client import ShipitClient


def list_addresses(client: ShipitClient) -> list:
    """List all saved addresses."""
    return client._request("/addresses")


def get_address(client: ShipitClient, address_id: str) -> dict:
    """Get a single address."""
    return client._request(f"/addresses/{address_id}")


def create_address(client: ShipitClient, data: dict) -> dict:
    """Create a new address."""
    return client._request("/addresses", method="POST", data=data)


def update_address(client: ShipitClient, address_id: str, data: dict) -> dict:
    """Update an address."""
    return client._request(f"/addresses/{address_id}", method="PUT", data=data)


def delete_address(client: ShipitClient, address_id: str) -> dict:
    """Delete an address."""
    return client._request(f"/addresses/{address_id}", method="DELETE")

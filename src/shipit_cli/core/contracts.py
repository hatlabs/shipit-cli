"""Carrier contract operations."""

from shipit_cli.core.client import ShipitClient


def list_contracts(client: ShipitClient) -> list:
    """List all carrier contracts."""
    return client._request("/carrier-contracts")


def get_contract(client: ShipitClient, contract_id: str) -> dict:
    """Get a single carrier contract."""
    return client._request(f"/carrier-contracts/{contract_id}")


def create_contract(client: ShipitClient, data: dict) -> dict:
    """Create a new carrier contract."""
    return client._request("/carrier-contracts", method="POST", data=data)


def update_contract(client: ShipitClient, contract_id: str, data: dict) -> dict:
    """Update a carrier contract."""
    return client._request(f"/carrier-contracts/{contract_id}", method="PUT", data=data)


def delete_contract(client: ShipitClient, contract_id: str) -> dict:
    """Delete a carrier contract."""
    return client._request(f"/carrier-contracts/{contract_id}", method="DELETE")

"""Shipment operations."""

from shipit_cli.core.client import ShipitClient, ShipitAPIError


def create_shipment(client: ShipitClient, data: dict) -> dict:
    """Create a shipment (PUT /v1/shipment)."""
    result = client._request("/shipment", method="PUT", data=data)
    if isinstance(result, dict) and result.get("status") == 0:
        error = result.get("error", "Unknown error")
        raise ShipitAPIError(f"Shipment creation failed: {error}")
    return result


def list_shipments(
    client: ShipitClient,
    tracking_number: str | None = None,
    created_after: str | None = None,
    created_before: str | None = None,
    per_page: int | None = None,
    cursor: str | None = None,
) -> dict | list:
    """List shipments (GET /v1/shipments)."""
    params = {}
    if tracking_number:
        params["trackingNumber"] = tracking_number
    if created_after:
        params["createdAfter"] = created_after
    if created_before:
        params["createdBefore"] = created_before
    if per_page:
        params["perPage"] = str(per_page)
    if cursor:
        params["cursor"] = cursor
    return client._request("/shipments", params=params if params else None)


def consolidate_shipment(client: ShipitClient, data: dict) -> dict:
    """Consolidate a shipment (POST /v1/consolidate-shipment)."""
    return client._request("/consolidate-shipment", method="POST", data=data)

"""Shipit CLI — Click-based command interface with REPL."""

import json
import sys

import click

from shipit_cli.core.client import ShipitAPIError, make_client
from shipit_cli.core import addresses, agents, contracts, methods, shipments


class CliContext:
    """Shared state passed via Click context."""

    def __init__(
        self,
        json_output: bool,
        url: str | None,
        api_key: str | None,
    ):
        self.json_output = json_output
        self.url = url
        self.api_key = api_key
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = make_client(url=self.url, api_key=self.api_key)
        return self._client


pass_ctx = click.make_pass_decorator(CliContext, ensure=True)


def _output(ctx: CliContext, data) -> None:
    """Print data as JSON."""
    click.echo(json.dumps(data, indent=2, default=str))


def _output_list(ctx: CliContext, data: list[dict], headers: list[str], row_fn) -> None:
    """Print a list as JSON or table."""
    if ctx.json_output:
        click.echo(json.dumps(data, indent=2, default=str))
        return

    from shipit_cli.utils.repl_skin import ReplSkin

    skin = ReplSkin("shipit")
    rows = [row_fn(d) for d in data]
    skin.table(headers, rows)
    skin.hint(f"\n  {len(data)} result(s)")


# ---------------------------------------------------------------------------
# Root group
# ---------------------------------------------------------------------------


@click.group(invoke_without_command=True)
@click.option("--json", "json_output", is_flag=True, help="Output as JSON.")
@click.option("--url", envvar="SHIPIT_URL", help="Shipit API URL.")
@click.option("--api-key", envvar="SHIPIT_API_KEY", help="Shipit API key.")
@click.pass_context
def cli(ctx, json_output, url, api_key):
    """Shipit CLI — command-line interface to Shipit shipping API."""
    ctx.obj = CliContext(
        json_output=json_output,
        url=url,
        api_key=api_key,
    )

    if ctx.invoked_subcommand is None:
        _run_repl(ctx.obj)


def _run_repl(ctx: CliContext) -> None:
    """Interactive REPL mode."""
    from shipit_cli.utils.repl_skin import ReplSkin

    skin = ReplSkin("shipit")
    skin.print_banner()

    pt_session = skin.create_prompt_session()

    commands = {
        "methods list": "List all shipping methods",
        "methods quote -d JSON": "Get shipping methods with prices",
        "addresses list": "List saved addresses",
        "addresses get <id>": "Get single address",
        "addresses create -d JSON": "Create address",
        "addresses update <id> -d JSON": "Update address",
        "addresses delete <id>": "Delete address",
        "contracts list": "List carrier contracts",
        "contracts get <id>": "Get single contract",
        "contracts create -d JSON": "Create contract",
        "contracts update <id> -d JSON": "Update contract",
        "contracts delete <id>": "Delete contract",
        "agents search -d JSON": "Search service points",
        "shipment create -d JSON": "Create shipment",
        "shipments list": "List shipments",
        "shipments consolidate -d JSON": "Consolidate shipment",
        "help": "Show this help",
        "quit / exit": "Exit the REPL",
    }

    while True:
        try:
            line = skin.get_input(pt_session)
        except (EOFError, KeyboardInterrupt):
            skin.print_goodbye()
            break

        if not line:
            continue

        if line in ("quit", "exit", "q"):
            skin.print_goodbye()
            break

        if line == "help":
            skin.help(commands)
            continue

        args = _split_args(line)
        if ctx.json_output:
            args = ["--json"] + args

        try:
            cli.main(args=args, standalone_mode=False, obj=ctx)
        except SystemExit:
            pass
        except ShipitAPIError as e:
            skin.error(str(e))
        except click.UsageError as e:
            skin.error(str(e))
        except Exception as e:
            skin.error(f"Unexpected error: {e}")


def _split_args(line: str) -> list[str]:
    """Split a REPL input line respecting quoted strings."""
    import shlex

    try:
        return shlex.split(line)
    except ValueError:
        return line.split()


# ---------------------------------------------------------------------------
# methods
# ---------------------------------------------------------------------------


@cli.group(name="methods")
def methods_cmd():
    """Shipping method operations."""


@methods_cmd.command("list")
@pass_ctx
def methods_list(ctx):
    """List all available shipping methods."""
    data = methods.list_methods(ctx.client)
    _output_list(
        ctx,
        data,
        ["Service ID", "Name", "Carrier", "Home", "Pickup", "EU", "World"],
        lambda d: [
            d.get("serviceId", ""),
            d.get("name", ""),
            d.get("carrier", ""),
            "Yes" if d.get("homeDelivery") else "",
            "Yes" if d.get("pickUpPoints") else "",
            "Yes" if d.get("euDelivery") else "",
            "Yes" if d.get("worldwideDelivery") else "",
        ],
    )


@methods_cmd.command("quote")
@click.option("--data", "-d", required=True, help="JSON shipment data (sender, receiver, parcels).")
@pass_ctx
def methods_quote(ctx, data):
    """Get shipping methods with prices for a shipment."""
    data = json.loads(data)
    result = methods.quote_methods(ctx.client, data)
    _output(ctx, result)


# ---------------------------------------------------------------------------
# addresses
# ---------------------------------------------------------------------------


@cli.group(name="addresses")
def addresses_cmd():
    """Saved address operations."""


@addresses_cmd.command("list")
@pass_ctx
def addresses_list(ctx):
    """List all saved addresses."""
    data = addresses.list_addresses(ctx.client)
    _output(ctx, data)


@addresses_cmd.command("get")
@click.argument("address_id")
@pass_ctx
def addresses_get(ctx, address_id):
    """Get a single address."""
    data = addresses.get_address(ctx.client, address_id)
    _output(ctx, data)


@addresses_cmd.command("create")
@click.option("--data", "-d", required=True, help="JSON address data.")
@pass_ctx
def addresses_create(ctx, data):
    """Create a new address."""
    data = json.loads(data)
    result = addresses.create_address(ctx.client, data)
    _output(ctx, result)


@addresses_cmd.command("update")
@click.argument("address_id")
@click.option("--data", "-d", required=True, help="JSON address data.")
@pass_ctx
def addresses_update(ctx, address_id, data):
    """Update an address."""
    data = json.loads(data)
    result = addresses.update_address(ctx.client, address_id, data)
    _output(ctx, result)


@addresses_cmd.command("delete")
@click.argument("address_id")
@pass_ctx
def addresses_delete(ctx, address_id):
    """Delete an address."""
    result = addresses.delete_address(ctx.client, address_id)
    _output(ctx, result)


# ---------------------------------------------------------------------------
# contracts
# ---------------------------------------------------------------------------


@cli.group(name="contracts")
def contracts_cmd():
    """Carrier contract operations."""


@contracts_cmd.command("list")
@pass_ctx
def contracts_list(ctx):
    """List all carrier contracts."""
    data = contracts.list_contracts(ctx.client)
    _output(ctx, data)


@contracts_cmd.command("get")
@click.argument("contract_id")
@pass_ctx
def contracts_get(ctx, contract_id):
    """Get a single carrier contract."""
    data = contracts.get_contract(ctx.client, contract_id)
    _output(ctx, data)


@contracts_cmd.command("create")
@click.option("--data", "-d", required=True, help="JSON contract data.")
@pass_ctx
def contracts_create(ctx, data):
    """Create a new carrier contract."""
    data = json.loads(data)
    result = contracts.create_contract(ctx.client, data)
    _output(ctx, result)


@contracts_cmd.command("update")
@click.argument("contract_id")
@click.option("--data", "-d", required=True, help="JSON contract data.")
@pass_ctx
def contracts_update(ctx, contract_id, data):
    """Update a carrier contract."""
    data = json.loads(data)
    result = contracts.update_contract(ctx.client, contract_id, data)
    _output(ctx, result)


@contracts_cmd.command("delete")
@click.argument("contract_id")
@pass_ctx
def contracts_delete(ctx, contract_id):
    """Delete a carrier contract."""
    result = contracts.delete_contract(ctx.client, contract_id)
    _output(ctx, result)


# ---------------------------------------------------------------------------
# agents
# ---------------------------------------------------------------------------


@cli.group(name="agents")
def agents_cmd():
    """Service point / pickup location operations."""


@agents_cmd.command("search")
@click.option("--data", "-d", required=True, help="JSON search criteria.")
@pass_ctx
def agents_search(ctx, data):
    """Search for service points / pickup locations."""
    data = json.loads(data)
    result = agents.search_agents(ctx.client, data)
    _output(ctx, result)


# ---------------------------------------------------------------------------
# shipment (singular — create)
# ---------------------------------------------------------------------------


@cli.group(name="shipment")
def shipment_cmd():
    """Single shipment operations."""


@shipment_cmd.command("create")
@click.option("--data", "-d", required=True, help="JSON shipment data.")
@click.option("--output-dir", default=None, help="Directory to save label PDFs.")
@pass_ctx
def shipment_create(ctx, data, output_dir):
    """Create a shipment."""
    data = json.loads(data)
    result = shipments.create_shipment(ctx.client, data)

    if output_dir and isinstance(result, dict):
        _download_freight_docs(result, output_dir)

    _output(ctx, result)


def _download_freight_docs(result: dict, output_dir: str) -> None:
    """Download freight document PDFs from URLs in the response."""
    import os
    import urllib.request

    os.makedirs(output_dir, exist_ok=True)
    tracking = result.get("trackingNumber", "unknown")

    for i, url in enumerate(result.get("freightDoc", [])):
        filename = f"{tracking}_label_{i}.pdf"
        filepath = os.path.join(output_dir, filename)
        urllib.request.urlretrieve(url, filepath)
        click.echo(f"Saved: {filepath}", err=True)

    proforma_url = result.get("proforma")
    if proforma_url:
        filepath = os.path.join(output_dir, f"{tracking}_proforma.pdf")
        urllib.request.urlretrieve(proforma_url, filepath)
        click.echo(f"Saved: {filepath}", err=True)


# ---------------------------------------------------------------------------
# shipments (plural — list, consolidate)
# ---------------------------------------------------------------------------


@cli.group(name="shipments")
def shipments_cmd():
    """Shipment query operations."""


@shipments_cmd.command("list")
@click.option("--tracking-number", default=None, help="Filter by tracking number.")
@click.option("--created-after", default=None, help="Filter: created after (ISO date).")
@click.option("--created-before", default=None, help="Filter: created before (ISO date).")
@click.option("--per-page", default=None, type=int, help="Results per page.")
@click.option("--cursor", default=None, help="Pagination cursor.")
@pass_ctx
def shipments_list(ctx, tracking_number, created_after, created_before, per_page, cursor):
    """List shipments."""
    data = shipments.list_shipments(
        ctx.client,
        tracking_number=tracking_number,
        created_after=created_after,
        created_before=created_before,
        per_page=per_page,
        cursor=cursor,
    )
    _output(ctx, data)


@shipments_cmd.command("consolidate")
@click.option("--data", "-d", required=True, help="JSON consolidation data.")
@pass_ctx
def shipments_consolidate(ctx, data):
    """Consolidate a shipment."""
    data = json.loads(data)
    result = shipments.consolidate_shipment(ctx.client, data)
    _output(ctx, result)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main():
    try:
        cli(standalone_mode=True)
    except ShipitAPIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

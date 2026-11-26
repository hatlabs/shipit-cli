"""Tests for `shipment create` and its document downloads."""

import json
import urllib.error
from email.message import Message
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from shipit_cli.cli import cli
from shipit_cli.core.client import ShipitAPIError, ShipitClient

LABEL_URL = "https://api.shipit.ax/documents/shipment/abc"
PROFORMA_URL = "https://api.shipit.ax/documents/proforma/abc"
RESULT = {
    "status": 1,
    "trackingNumber": "1Z123",
    "freightDoc": [LABEL_URL],
    "proforma": PROFORMA_URL,
}
ARGS = ["--url", "https://api.example", "--api-key", "k", "shipment", "create", "-d", "{}"]


def test_download_sends_user_agent(tmp_path):
    response = MagicMock()
    response.__enter__.return_value.read.return_value = b"%PDF"
    target = tmp_path / "label.pdf"

    with patch("urllib.request.urlopen", return_value=response) as urlopen:
        ShipitClient(url="https://api.example", api_key="k").download(LABEL_URL, str(target))

    request = urlopen.call_args.args[0]
    assert request.full_url == LABEL_URL
    assert request.get_header("User-agent") == "shipit-cli/1.0"
    assert target.read_bytes() == b"%PDF"


def test_download_http_error_raises_api_error(tmp_path):
    error = urllib.error.HTTPError(LABEL_URL, 403, "Forbidden", Message(), None)

    with patch("urllib.request.urlopen", side_effect=error):
        try:
            ShipitClient(url="https://api.example", api_key="k").download(LABEL_URL, str(tmp_path / "x.pdf"))
        except ShipitAPIError as e:
            assert e.status_code == 403
            assert LABEL_URL in str(e)
        else:
            raise AssertionError("expected ShipitAPIError")


def test_create_saves_label_and_proforma(tmp_path):
    with patch("shipit_cli.cli.shipments.create_shipment", return_value=RESULT), \
         patch.object(ShipitClient, "download") as download:
        result = CliRunner().invoke(cli, ARGS + ["--output-dir", str(tmp_path)])

    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout) == RESULT
    assert [c.args for c in download.call_args_list] == [
        (LABEL_URL, str(tmp_path / "1Z123_label_0.pdf")),
        (PROFORMA_URL, str(tmp_path / "1Z123_proforma.pdf")),
    ]


def test_create_prints_response_when_download_fails(tmp_path):
    failure = ShipitAPIError(f"HTTP 403 downloading {LABEL_URL}", status_code=403)

    with patch("shipit_cli.cli.shipments.create_shipment", return_value=RESULT), \
         patch.object(ShipitClient, "download", side_effect=[failure, None]) as download:
        result = CliRunner().invoke(cli, ARGS + ["--output-dir", str(tmp_path)])

    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout) == RESULT
    assert LABEL_URL in result.stderr
    assert download.call_count == 2


def test_create_without_output_dir_downloads_nothing():
    with patch("shipit_cli.cli.shipments.create_shipment", return_value=RESULT), \
         patch.object(ShipitClient, "download") as download:
        result = CliRunner().invoke(cli, ARGS)

    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout) == RESULT
    download.assert_not_called()

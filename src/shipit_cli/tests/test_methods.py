"""Tests for methods module."""

from unittest.mock import MagicMock

from shipit_cli.core.methods import list_methods, quote_methods


def test_list_methods_calls_correct_endpoint():
    client = MagicMock()
    client._request.return_value = [{"serviceId": "posti-2103"}]

    result = list_methods(client)

    client._request.assert_called_once_with("/list-methods")
    assert result == [{"serviceId": "posti-2103"}]


def test_quote_methods_calls_correct_endpoint():
    client = MagicMock()
    client._request.return_value = {"status": 1, "methods": []}
    data = {
        "sender": {"postcode": "00840", "country": "FI"},
        "receiver": {"postcode": "20100", "country": "FI"},
        "parcels": [{"weight": 2.5, "length": 30, "width": 20, "height": 10, "type": "PACKAGE"}],
    }

    result = quote_methods(client, data)

    client._request.assert_called_once_with("/shipping-methods", method="POST", data=data)
    assert result == {"status": 1, "methods": []}

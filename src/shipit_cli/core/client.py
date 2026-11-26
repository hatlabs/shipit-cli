"""Shipit HTTP API client."""

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

# Shipit sits behind Cloudflare, which rejects the default Python-urllib User-Agent.
USER_AGENT = "shipit-cli/1.0"


class ShipitAPIError(Exception):
    """Raised when the Shipit API returns an error."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


def extract_error_detail(error: Exception) -> str:
    """Extract human-readable error from Shipit API error responses."""
    if isinstance(error, urllib.error.HTTPError):
        try:
            body = error.read().decode("utf-8", errors="replace")
            data = json.loads(body)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return f"HTTP {error.code}: {body[:500] if 'body' in dir() else str(error)}"

        if isinstance(data, dict):
            if data.get("error"):
                err = data["error"]
                if isinstance(err, dict):
                    return json.dumps(err)
                return str(err)
            if data.get("message"):
                return str(data["message"])

        return f"HTTP {error.code}: {body[:500]}"

    return str(error)


@dataclass
class ShipitClient:
    """HTTP client for Shipit API."""

    url: str
    api_key: str

    def _request(
        self,
        path: str,
        method: str = "GET",
        data: dict | list | None = None,
        params: dict | None = None,
    ) -> dict | list:
        """Make an HTTP request to Shipit and return parsed JSON."""
        url = f"{self.url}{path}"
        if params:
            qs = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
            url = f"{url}?{qs}"

        body = json.dumps(data).encode("utf-8") if data is not None else None
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
            "X-SHIPIT-KEY": self.api_key,
        }

        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            detail = extract_error_detail(e)
            raise ShipitAPIError(detail, status_code=e.code) from e
        except urllib.error.URLError as e:
            raise ShipitAPIError(f"Connection error: {e.reason}") from e

    def download(self, url: str, path: str) -> None:
        """Save a Shipit document (label, proforma) from url to path."""
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req) as resp:
                content = resp.read()
        except urllib.error.HTTPError as e:
            raise ShipitAPIError(f"HTTP {e.code} downloading {url}", status_code=e.code) from e
        except urllib.error.URLError as e:
            raise ShipitAPIError(f"Connection error downloading {url}: {e.reason}") from e
        with open(path, "wb") as f:
            f.write(content)


def make_client(
    url: str | None = None,
    api_key: str | None = None,
) -> ShipitClient:
    """Create a ShipitClient from explicit args or environment variables."""
    url = url or os.environ.get("SHIPIT_URL")
    api_key = api_key or os.environ.get("SHIPIT_API_KEY")

    if not url:
        raise ShipitAPIError(
            "SHIPIT_URL not set. Provide --url or set the env var."
        )
    if not api_key:
        raise ShipitAPIError(
            "SHIPIT_API_KEY not set. Provide --api-key or set the env var."
        )

    url = url.rstrip("/")

    return ShipitClient(url=url, api_key=api_key)

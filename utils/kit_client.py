"""
Kit (ConvertKit) API Client
Wraps the Kit V4 REST API for subscriber management, tags, sequences, and broadcasts.
"""

import os
import json
import urllib.request
import urllib.error
from typing import Any


class KitAPIError(Exception):
    """Raised when the Kit API returns an error."""
    def __init__(self, status: int, message: str):
        self.status = status
        super().__init__(f"Kit API {status}: {message}")


class KitClient:
    """Client for the Kit (ConvertKit) V4 API."""

    BASE_URL = "https://api.kit.com/v4"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("CONVERTKIT_API_KEY", "")
        if not self.api_key or self.api_key.startswith("your_"):
            raise KitAPIError(0, "CONVERTKIT_API_KEY not set. Add it to .env")

    def _request(self, method: str, path: str, body: dict | None = None,
                 params: dict | None = None) -> dict[str, Any]:
        """Make an authenticated request to the Kit API."""
        url = f"{self.BASE_URL}{path}"
        if params:
            query = "&".join(f"{k}={v}" for k, v in params.items() if v is not None)
            if query:
                url = f"{url}?{query}"

        data = json.dumps(body).encode() if body else None
        headers = {
            "X-Kit-Api-Key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            error_body = e.read().decode() if e.fp else str(e)
            raise KitAPIError(e.code, error_body) from e

    # ── Subscribers ──

    def create_subscriber(self, email: str, first_name: str | None = None,
                          fields: dict | None = None) -> dict[str, Any]:
        """Create or update a subscriber."""
        body: dict[str, Any] = {"email_address": email}
        if first_name:
            body["first_name"] = first_name
        if fields:
            body["fields"] = fields
        return self._request("POST", "/subscribers", body)

    def list_subscribers(self, per_page: int = 100, after: str | None = None) -> dict[str, Any]:
        """List subscribers with pagination."""
        params = {"per_page": str(per_page)}
        if after:
            params["after"] = after
        return self._request("GET", "/subscribers", params=params)

    def get_subscriber(self, subscriber_id: int) -> dict[str, Any]:
        """Get a specific subscriber by ID."""
        return self._request("GET", f"/subscribers/{subscriber_id}")

    # ── Tags ──

    def list_tags(self, per_page: int = 500) -> dict[str, Any]:
        """List all tags."""
        return self._request("GET", "/tags", params={"per_page": str(per_page)})

    def create_tag(self, name: str) -> dict[str, Any]:
        """Create a tag (returns existing if name matches)."""
        return self._request("POST", "/tags", {"name": name})

    def tag_subscriber(self, tag_id: int, subscriber_id: int) -> dict[str, Any]:
        """Apply a tag to a subscriber."""
        return self._request("POST", f"/tags/{tag_id}/subscribers/{subscriber_id}", {})

    def untag_subscriber(self, tag_id: int, subscriber_id: int) -> dict[str, Any]:
        """Remove a tag from a subscriber."""
        return self._request("DELETE", f"/tags/{tag_id}/subscribers/{subscriber_id}")

    def list_tag_subscribers(self, tag_id: int, per_page: int = 100) -> dict[str, Any]:
        """List subscribers with a specific tag."""
        return self._request("GET", f"/tags/{tag_id}/subscribers",
                             params={"per_page": str(per_page)})

    # ── Sequences ──

    def list_sequences(self) -> dict[str, Any]:
        """List all sequences."""
        return self._request("GET", "/sequences")

    def add_subscriber_to_sequence(self, sequence_id: int, email: str) -> dict[str, Any]:
        """Add a subscriber to a sequence by email."""
        return self._request("POST", f"/sequences/{sequence_id}/subscribers",
                             {"email_address": email})

    # ── Broadcasts ──

    def create_broadcast(self, subject: str, content: str,
                         description: str = "", preview_text: str = "",
                         public: bool = True, send_at: str | None = None) -> dict[str, Any]:
        """Create a broadcast (newsletter/email blast)."""
        body: dict[str, Any] = {
            "subject": subject,
            "content": content,
            "description": description or subject,
            "preview_text": preview_text or content[:150],
            "public": public,
            "published_at": send_at or "",
            "subscriber_filter": [{"all": [{"type": "all"}]}],
        }
        if send_at:
            body["send_at"] = send_at
        return self._request("POST", "/broadcasts", body)

    def list_broadcasts(self, per_page: int = 50) -> dict[str, Any]:
        """List broadcasts."""
        return self._request("GET", "/broadcasts", params={"per_page": str(per_page)})

    def get_broadcast(self, broadcast_id: int) -> dict[str, Any]:
        """Get a specific broadcast."""
        return self._request("GET", f"/broadcasts/{broadcast_id}")

    # ── Forms ──

    def list_forms(self) -> dict[str, Any]:
        """List all forms."""
        return self._request("GET", "/forms")

    def add_subscriber_to_form(self, form_id: int, email: str,
                               first_name: str | None = None) -> dict[str, Any]:
        """Add a subscriber to a form."""
        body: dict[str, Any] = {"email_address": email}
        if first_name:
            body["first_name"] = first_name
        return self._request("POST", f"/forms/{form_id}/subscribers", body)

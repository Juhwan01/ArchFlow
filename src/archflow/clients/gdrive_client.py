"""Async Google Drive API client with OAuth 2.0 token refresh."""

from __future__ import annotations

import os
from typing import Any

import httpx


class GDriveClient:
    """Google Drive API client for accessing .drawio files."""

    TOKEN_URL = "https://oauth2.googleapis.com/token"
    DRIVE_API = "https://www.googleapis.com/drive/v3"

    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None
        self._access_token: str = ""

        self._client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
        self._client_secret = os.environ.get("GOOGLE_CLIENT_SECRET", "")
        self._refresh_token = os.environ.get("GOOGLE_REFRESH_TOKEN", "")

        self._available = bool(
            self._client_id and self._client_secret and self._refresh_token
        )

    @property
    def available(self) -> bool:
        return self._available

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def _ensure_access_token(self) -> str:
        """Refresh access token using refresh token."""
        if self._access_token:
            return self._access_token

        resp = await self.client.post(
            self.TOKEN_URL,
            data={
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "refresh_token": self._refresh_token,
                "grant_type": "refresh_token",
            },
        )

        if resp.status_code != 200:
            raise RuntimeError(f"Failed to refresh token: {resp.text}")

        data = resp.json()
        self._access_token = data["access_token"]
        return self._access_token

    async def list_drawio_files(self, folder_id: str) -> list[dict[str, Any]]:
        """List .drawio files in a Google Drive folder."""
        if not self._available:
            return []

        token = await self._ensure_access_token()
        query = f"'{folder_id}' in parents and name contains '.drawio' and trashed = false"

        resp = await self.client.get(
            f"{self.DRIVE_API}/files",
            params={
                "q": query,
                "fields": "files(id,name,modifiedTime,size)",
                "pageSize": 100,
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        if resp.status_code != 200:
            self._access_token = ""
            return []

        return resp.json().get("files", [])

    async def download_file(self, file_id: str) -> str:
        """Download file content as string."""
        if not self._available:
            return ""

        token = await self._ensure_access_token()

        resp = await self.client.get(
            f"{self.DRIVE_API}/files/{file_id}",
            params={"alt": "media"},
            headers={"Authorization": f"Bearer {token}"},
        )

        if resp.status_code != 200:
            self._access_token = ""
            return ""

        return resp.text

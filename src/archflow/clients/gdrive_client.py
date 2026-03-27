"""Async Google Drive API client with Service Account authentication."""

from __future__ import annotations

import json
import os
import time
from typing import Any

import httpx
import jwt


class GDriveClient:
    """Google Drive API client for accessing .drawio files.

    Supports two authentication methods:
    1. Service Account JSON key file (recommended)
    2. OAuth 2.0 refresh token (legacy)
    """

    TOKEN_URL = "https://oauth2.googleapis.com/token"
    DRIVE_API = "https://www.googleapis.com/drive/v3"
    SCOPES = "https://www.googleapis.com/auth/drive.readonly"

    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None
        self._access_token: str = ""
        self._token_expiry: float = 0

        # Service Account (preferred)
        self._sa_key: dict[str, Any] | None = None
        sa_key_path = os.environ.get("GOOGLE_SERVICE_ACCOUNT_KEY", "")
        if sa_key_path and os.path.isfile(sa_key_path):
            with open(sa_key_path, encoding="utf-8") as f:
                self._sa_key = json.load(f)

        # OAuth fallback (legacy)
        self._client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
        self._client_secret = os.environ.get("GOOGLE_CLIENT_SECRET", "")
        self._refresh_token = os.environ.get("GOOGLE_REFRESH_TOKEN", "")

        self._available = bool(self._sa_key) or bool(
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
        """Get a valid access token, refreshing if needed."""
        if self._access_token and time.time() < self._token_expiry:
            return self._access_token

        if self._sa_key:
            return await self._get_sa_token()
        return await self._get_oauth_token()

    async def _get_sa_token(self) -> str:
        """Get access token via Service Account JWT assertion."""
        now = int(time.time())
        payload = {
            "iss": self._sa_key["client_email"],
            "scope": self.SCOPES,
            "aud": self.TOKEN_URL,
            "iat": now,
            "exp": now + 3600,
        }
        signed_jwt = jwt.encode(
            payload,
            self._sa_key["private_key"],
            algorithm="RS256",
        )

        resp = await self.client.post(
            self.TOKEN_URL,
            data={
                "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                "assertion": signed_jwt,
            },
        )

        if resp.status_code != 200:
            raise RuntimeError(f"Service Account token failed: {resp.text}")

        data = resp.json()
        self._access_token = data["access_token"]
        self._token_expiry = now + data.get("expires_in", 3600) - 60
        return self._access_token

    async def _get_oauth_token(self) -> str:
        """Get access token via OAuth refresh token (legacy)."""
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
        self._token_expiry = time.time() + data.get("expires_in", 3600) - 60
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

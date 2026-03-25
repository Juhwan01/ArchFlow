"""Async GitHub REST API client."""

from __future__ import annotations

import asyncio
import os
from typing import Any

import httpx


class GitHubClient:
    """Lightweight async GitHub REST API client with PAT auth."""

    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None

        token = os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN", "")
        if not token:
            self._available = False
            self._headers: dict[str, str] = {}
            return

        self._available = True
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    @property
    def available(self) -> bool:
        return self._available

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url="https://api.github.com",
                headers=self._headers,
                timeout=30.0,
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def request(
        self,
        method: str,
        path: str,
        *,
        json: Any = None,
        params: dict[str, Any] | None = None,
        max_retries: int = 2,
    ) -> dict[str, Any] | list[Any] | None:
        """Make an API request with rate-limit retry."""
        if not self._available:
            return {"error": "GitHub not configured. Set GITHUB_PERSONAL_ACCESS_TOKEN."}

        for attempt in range(max_retries + 1):
            resp = await self.client.request(
                method, path, json=json, params=params
            )

            if resp.status_code in (403, 429):
                remaining = resp.headers.get("X-RateLimit-Remaining", "1")
                if remaining == "0":
                    retry_after = int(resp.headers.get("Retry-After", "60"))
                    if attempt < max_retries:
                        await asyncio.sleep(min(retry_after, 10))
                        continue
                return {"error": "Rate limited", "status": resp.status_code}

            if resp.status_code == 204:
                return {"success": True}

            if resp.status_code >= 400:
                try:
                    body = resp.json()
                except Exception:
                    body = resp.text
                return {"error": body, "status": resp.status_code}

            if not resp.content:
                return {"success": True}

            return resp.json()

        return {"error": "Max retries exceeded", "status": 429}

    async def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        return await self.request("GET", path, params=params)

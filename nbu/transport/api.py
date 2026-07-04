"""HTTP transport for NetBackup REST APIs."""

from __future__ import annotations

import time
from typing import Any, Literal

import httpx

from nbu.auth import TokenState
from nbu.config import NetBackupConfig
from nbu.exceptions import ApiError, AuthenticationError, AuthorizationError, NotFoundError, TimeoutError

PaginationMode = Literal["offset", "cursor"]


class ApiTransport:
    """Small retrying HTTP transport that hides httpx details from callers."""

    def __init__(self, config: NetBackupConfig, transport: httpx.BaseTransport | None = None) -> None:
        self.config = config
        self.token = TokenState(token=config.token.get_secret_value() if config.token else None)
        client_kwargs: dict[str, Any] = {
            "base_url": config.api_base_url,
            "verify": config.verify_ssl,
            "timeout": config.timeout,
            "headers": {
                "User-Agent": config.user_agent,
                "Accept": self._media_type(),
                **config.extra_headers,
            },
        }
        if transport is not None:
            client_kwargs["transport"] = transport
        if config.proxies:
            client_kwargs["proxy"] = (
                config.proxies.get("all://")
                or config.proxies.get("https://")
                or config.proxies.get("http://")
                or next(iter(config.proxies.values()))
            )
        self._client = httpx.Client(**client_kwargs)

    def close(self) -> None:
        self._client.close()

    def login(self) -> str:
        if not self.config.username or not self.config.password:
            raise AuthenticationError("username and password are required for REST API login")
        payload = {
            "userName": self.config.username,
            "password": self.config.password.get_secret_value(),
            "domainType": self.config.domain_type,
            "domainName": self.config.domain_name,
        }
        data = self.request(
            "POST",
            "/login",
            json=payload,
            authenticated=False,
            headers={"Content-Type": self._media_type()},
        )
        token = data.get("token") or data.get("access_token")
        if not token:
            raise AuthenticationError("NetBackup login response did not include a token")
        self.token.update(token, data.get("expires_in") or data.get("expiresIn"))
        return token

    def ensure_authenticated(self) -> None:
        if not self.token.is_valid:
            self.login()

    def request(
        self,
        method: str,
        path: str,
        *,
        authenticated: bool = True,
        **kwargs: Any,
    ) -> dict[str, Any]:
        if authenticated:
            self.ensure_authenticated()
        headers = dict(kwargs.pop("headers", {}) or {})
        headers.setdefault("Accept", self._media_type())
        if authenticated and self.token.token:
            headers["Authorization"] = self._authorization_value(self.token.token)

        last_error: Exception | None = None
        for attempt in range(self.config.retries + 1):
            try:
                response = self._client.request(method, path, headers=headers, **kwargs)
                return self._handle_response(response)
            except httpx.TimeoutException as exc:
                last_error = TimeoutError(str(exc))
            except httpx.HTTPError as exc:
                last_error = ApiError(str(exc))
            if attempt < self.config.retries:
                time.sleep(self.config.retry_backoff * (2**attempt))
        if last_error:
            raise last_error
        raise ApiError("REST API request failed")

    def request_text(
        self,
        method: str,
        path: str,
        *,
        authenticated: bool = True,
        **kwargs: Any,
    ) -> str:
        if authenticated:
            self.ensure_authenticated()
        headers = dict(kwargs.pop("headers", {}) or {})
        if authenticated and self.token.token:
            headers["Authorization"] = self._authorization_value(self.token.token)

        last_error: Exception | None = None
        for attempt in range(self.config.retries + 1):
            try:
                response = self._client.request(method, path, headers=headers, **kwargs)
                if response.status_code in {401, 403}:
                    if response.status_code == 401:
                        raise AuthenticationError("NetBackup API authentication failed")
                    raise AuthorizationError("NetBackup API authorization failed")
                if response.status_code == 404:
                    raise NotFoundError("NetBackup API resource was not found")
                if response.status_code >= 400:
                    raise ApiError(f"NetBackup API returned HTTP {response.status_code}: {response.text}")
                return response.text
            except httpx.TimeoutException as exc:
                last_error = TimeoutError(str(exc))
            except httpx.HTTPError as exc:
                last_error = ApiError(str(exc))
            if attempt < self.config.retries:
                time.sleep(self.config.retry_backoff * (2**attempt))
        if last_error:
            raise last_error
        raise ApiError("REST API text request failed")

    @staticmethod
    def _handle_response(response: httpx.Response) -> dict[str, Any]:
        if response.status_code in {401, 403}:
            if response.status_code == 401:
                raise AuthenticationError("NetBackup API authentication failed")
            raise AuthorizationError("NetBackup API authorization failed")
        if response.status_code == 404:
            raise NotFoundError("NetBackup API resource was not found")
        if response.status_code >= 400:
            raise ApiError(f"NetBackup API returned HTTP {response.status_code}: {response.text}")
        if not response.content:
            return {}
        try:
            data = response.json()
        except ValueError as exc:
            raise ApiError("NetBackup API returned non-JSON content") from exc
        return data if isinstance(data, dict) else {"data": data}

    def get_collection(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        *,
        paginate: bool = True,
        pagination: PaginationMode = "offset",
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        if not paginate:
            data = self.request("GET", path, params=params)
            items = self._extract_items(data)
            return items[:limit] if limit is not None else items

        items: list[dict[str, Any]] = []
        for page in self.iter_collection_pages(path, params, pagination=pagination, limit=limit):
            remaining = None if limit is None else limit - len(items)
            items.extend(page if remaining is None else page[:remaining])
            if limit is not None and len(items) >= limit:
                break
        return items

    def iter_collection(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        *,
        pagination: PaginationMode = "offset",
        limit: int | None = None,
    ):
        yielded = 0
        for page in self.iter_collection_pages(path, params, pagination=pagination, limit=limit):
            for item in page:
                if limit is not None and yielded >= limit:
                    return
                yielded += 1
                yield item

    def iter_collection_pages(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        *,
        pagination: PaginationMode = "offset",
        limit: int | None = None,
    ):
        query = dict(params or {})
        query.setdefault("page[limit]", self.config.page_limit)
        seen_offsets: set[str] = set()
        yielded = 0

        while True:
            data = self.request("GET", path, params=query)
            page = self._extract_items(data)
            if limit is not None:
                remaining = limit - yielded
                if remaining <= 0:
                    break
                page = page[:remaining]
            yielded += len(page)
            yield page
            if limit is not None and yielded >= limit:
                break
            next_cursor = self._next_offset(data, pagination=pagination)
            if not next_cursor or next_cursor in seen_offsets:
                break
            seen_offsets.add(next_cursor)
            query["page[after]" if pagination == "cursor" else "page[offset]"] = next_cursor

    def _media_type(self) -> str:
        return f"application/vnd.netbackup+json;version={self.config.api_version}"

    def _authorization_value(self, token: str) -> str:
        scheme = self.config.authorization_scheme.strip()
        return f"{scheme} {token}" if scheme else token

    @staticmethod
    def _extract_items(data: dict[str, Any]) -> list[dict[str, Any]]:
        items = data.get("data") or data.get("items") or data.get("results") or []
        return items if isinstance(items, list) else [items]

    @staticmethod
    def _next_offset(data: dict[str, Any], *, pagination: PaginationMode = "offset") -> str | None:
        meta = data.get("meta") if isinstance(data.get("meta"), dict) else {}
        pagination_meta = meta.get("pagination") if isinstance(meta.get("pagination"), dict) else {}
        next_value = pagination_meta.get("next")
        has_next = pagination_meta.get("hasNext")
        if next_value not in {None, ""} and has_next is not False:
            return str(next_value)

        links = data.get("links") if isinstance(data.get("links"), dict) else {}
        next_link = links.get("next")
        if isinstance(next_link, dict):
            href = next_link.get("href")
        else:
            href = next_link
        if isinstance(href, str):
            param = "page[after]=" if pagination == "cursor" else "page[offset]="
            if param in href:
                return href.split(param, 1)[1].split("&", 1)[0]
        return None

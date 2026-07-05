import json

import httpx

from nbu.config import NetBackupConfig
from nbu.transport.api import ApiTransport


def test_login_sends_domain_fields_and_vendor_content_type() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["headers"] = dict(request.headers)
        captured["body"] = json.loads(request.content.decode())
        return httpx.Response(200, json={"token": "abc123"})

    transport = ApiTransport(
        NetBackupConfig(
            master="master.example.com",
            username="admin",
            password="secret",
            domain_type="unixpwd",
            domain_name="master.example.com",
        ),
        transport=httpx.MockTransport(handler),
    )

    assert transport.login() == "abc123"
    assert captured["body"] == {
        "userName": "admin",
        "password": "secret",
        "domainType": "unixpwd",
        "domainName": "master.example.com",
    }
    assert captured["headers"]["content-type"] == "application/vnd.netbackup+json;version=7.0"


def test_authenticated_requests_use_raw_netbackup_token_by_default() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["authorization"] == "abc123"
        assert request.headers["accept"] == "application/vnd.netbackup+json;version=7.0"
        return httpx.Response(200, json={"data": []})

    transport = ApiTransport(
        NetBackupConfig(master="master.example.com", token="abc123"),
        transport=httpx.MockTransport(handler),
    )

    transport.request("GET", "/admin/jobs")


def test_get_collection_follows_netbackup_pagination_offsets() -> None:
    seen_offsets: list[str | None] = []

    def handler(request: httpx.Request) -> httpx.Response:
        offset = request.url.params.get("page[offset]")
        seen_offsets.append(offset)
        if offset is None:
            return httpx.Response(
                200,
                json={
                    "data": [{"id": "1"}],
                    "meta": {"pagination": {"next": "100"}},
                    "links": {"next": "/admin/jobs?page[offset]=100"},
                },
            )
        return httpx.Response(200, json={"data": [{"id": "2"}], "meta": {"pagination": {}}})

    transport = ApiTransport(
        NetBackupConfig(master="master.example.com", token="abc123", page_limit=100),
        transport=httpx.MockTransport(handler),
    )

    assert transport.get_collection("/admin/jobs") == [{"id": "1"}, {"id": "2"}]
    assert seen_offsets == [None, "100"]


def test_get_collection_follows_cursor_pagination() -> None:
    seen_after: list[str | None] = []

    def handler(request: httpx.Request) -> httpx.Response:
        after = request.url.params.get("page[after]")
        seen_after.append(after)
        if after is None:
            return httpx.Response(
                200,
                json={
                    "data": [{"id": "1"}],
                    "meta": {"pagination": {"next": "cursor-1", "hasNext": True}},
                    "links": {"next": "/admin/jobs?page[after]=cursor-1"},
                },
            )
        return httpx.Response(
            200,
            json={"data": [{"id": "2"}], "meta": {"pagination": {"hasNext": False}}},
        )

    transport = ApiTransport(
        NetBackupConfig(master="master.example.com", token="abc123", page_limit=100),
        transport=httpx.MockTransport(handler),
    )

    assert transport.get_collection("/admin/jobs", pagination="cursor") == [{"id": "1"}, {"id": "2"}]
    assert seen_after == [None, "cursor-1"]


def test_get_collection_stops_at_limit() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(
            200,
            json={
                "data": [{"id": "1"}, {"id": "2"}, {"id": "3"}],
                "meta": {"pagination": {"next": "100"}},
            },
        )

    transport = ApiTransport(
        NetBackupConfig(master="master.example.com", token="abc123"),
        transport=httpx.MockTransport(handler),
    )

    assert transport.get_collection("/catalog/images", limit=2) == [{"id": "1"}, {"id": "2"}]
    assert calls == 1


def test_iter_collection_streams_records() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        offset = request.url.params.get("page[offset]")
        if offset is None:
            return httpx.Response(
                200,
                json={
                    "data": [{"id": "1"}],
                    "meta": {"pagination": {"next": "1", "hasNext": True}},
                },
            )
        return httpx.Response(
            200,
            json={"data": [{"id": "2"}], "meta": {"pagination": {"hasNext": False}}},
        )

    transport = ApiTransport(
        NetBackupConfig(master="master.example.com", token="abc123"),
        transport=httpx.MockTransport(handler),
    )

    assert list(transport.iter_collection("/catalog/images")) == [{"id": "1"}, {"id": "2"}]


def test_get_collection_page_exposes_next_token_and_optional_total() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params.get("page[offset]") == "200"
        return httpx.Response(
            200,
            json={
                "data": [{"id": "3"}],
                "meta": {"pagination": {"next": "300", "total": 900}},
            },
        )

    transport = ApiTransport(
        NetBackupConfig(master="master.example.com", token="abc123", page_limit=100),
        transport=httpx.MockTransport(handler),
    )

    page = transport.get_collection_page("/catalog/images", page_token=200)

    assert page.items == [{"id": "3"}]
    assert page.next_token == "300"
    assert page.total == 900


def test_request_text_supports_official_ping_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["accept"] == "text/vnd.netbackup+plain;version=14.0"
        return httpx.Response(200, text="1787654321")

    transport = ApiTransport(
        NetBackupConfig(master="master.example.com", version="11.2"),
        transport=httpx.MockTransport(handler),
    )

    assert (
        transport.request_text(
            "GET",
            "/ping",
            authenticated=False,
            headers={"Accept": "text/vnd.netbackup+plain;version=14.0"},
        )
        == "1787654321"
    )

import json

import httpx

from nbu import NetBackup, NetBackupConfig
from nbu.transport.api import ApiTransport


def test_direct_api_get_accepts_raw_path_and_params() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["method"] = request.method
        captured["path"] = request.url.path
        captured["params"] = dict(request.url.params)
        captured["accept"] = request.headers["accept"]
        return httpx.Response(200, json={"data": {"ok": True}})

    nb = NetBackup(config=NetBackupConfig(master="master.example.com", token="abc123", version="11.2"))
    nb.api.close()
    nb.api = ApiTransport(nb.config, transport=httpx.MockTransport(handler))

    result = nb.api_get("config/workloads/vmware/test-query/query-1", params={"include": "assets"})

    assert result == {"data": {"ok": True}}
    assert captured == {
        "method": "GET",
        "path": "/netbackup/config/workloads/vmware/test-query/query-1",
        "params": {"include": "assets"},
        "accept": "application/vnd.netbackup+json;version=14.0",
    }
    nb.close()


def test_direct_api_post_accepts_raw_body_and_api_version() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["method"] = request.method
        captured["path"] = request.url.path
        captured["accept"] = request.headers["accept"]
        captured["content_type"] = request.headers["content-type"]
        captured["body"] = json.loads(request.read().decode())
        return httpx.Response(200, json={"data": {"id": "query-1"}})

    nb = NetBackup(config=NetBackupConfig(master="master.example.com", token="abc123", version="10.0"))
    nb.api.close()
    nb.api = ApiTransport(nb.config, transport=httpx.MockTransport(handler))

    body = {
        "data": {
            "type": "intelligentTestQueryRequest",
            "attributes": {"testQuery": "vcenter Equal 'vc01'"},
        }
    }
    result = nb.api_post("/config/workloads/vmware/test-query", json=body, api_version="14.0")

    assert result == {"data": {"id": "query-1"}}
    assert captured == {
        "method": "POST",
        "path": "/netbackup/config/workloads/vmware/test-query",
        "accept": "application/vnd.netbackup+json;version=14.0",
        "content_type": "application/vnd.netbackup+json;version=14.0",
        "body": body,
    }
    nb.close()

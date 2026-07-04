from types import SimpleNamespace

import pytest

from nbu import NetBackup, NetBackupConfig


def test_config_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NBU_MASTER", "master.example.com")
    monkeypatch.setenv("NBU_USERNAME", "admin")
    monkeypatch.setenv("NBU_PASSWORD", "secret")
    monkeypatch.setenv("NBU_DOMAIN_TYPE", "unixpwd")
    monkeypatch.setenv("NBU_DOMAIN_NAME", "master.example.com")
    monkeypatch.setenv("NBU_VERSION", "11.2")
    monkeypatch.setenv("NBU_VERIFY_SSL", "false")

    config = NetBackupConfig.from_env()

    assert config.master == "master.example.com"
    assert config.username == "admin"
    assert config.password is not None
    assert config.password.get_secret_value() == "secret"
    assert config.domain_type == "unixpwd"
    assert config.api_version == "14.0"
    assert config.verify_ssl is False


def test_top_level_shortcuts_delegate_to_services() -> None:
    nb = NetBackup(master="master.example.com", token="token")
    nb.jobs = SimpleNamespace(list=lambda **kwargs: [{"kind": "job", **kwargs}])
    nb.policies = SimpleNamespace(list=lambda **kwargs: [{"kind": "policy", **kwargs}])
    nb.storage = SimpleNamespace(
        storage_units=lambda **kwargs: [{"kind": "storage-unit", **kwargs}],
        disk_pools=lambda **kwargs: [{"kind": "disk-pool", **kwargs}],
    )

    assert nb.list_jobs(mode="api") == [{"kind": "job", "mode": "api"}]
    assert nb.list_policies(mode="ssh") == [{"kind": "policy", "mode": "ssh"}]
    assert nb.list_storage(mode="api") == [
        {"kind": "storage-unit", "mode": "api"},
        {"kind": "disk-pool", "mode": "api"},
    ]

    nb.close()


def test_generic_collector_keeps_old_fluent_usage_simple() -> None:
    nb = NetBackup(master="master.example.com", token="token")
    nb.jobs = SimpleNamespace(list=lambda **kwargs: [{"id": 1, **kwargs}])

    result = nb.collectors.jobs().collect(mode="api", start_date="2026-07-01")

    assert result.collector == "jobs"
    assert result.records == [{"id": 1, "mode": "api", "start_date": "2026-07-01"}]
    assert result.metadata == {"mode": "api", "start_date": "2026-07-01"}

    nb.close()


def test_collect_by_name() -> None:
    nb = NetBackup(master="master.example.com", token="token")
    nb.images = SimpleNamespace(list=lambda **kwargs: [{"image_id": "client_1", **kwargs}])

    result = nb.collect("images", mode="api", client="app01")

    assert result.collector == "images"
    assert result.records == [{"image_id": "client_1", "mode": "api", "client": "app01"}]

    nb.close()


def test_top_level_iterators_delegate_to_services() -> None:
    nb = NetBackup(master="master.example.com", token="token")
    nb.jobs = SimpleNamespace(iter=lambda **kwargs: iter([{"id": 1, **kwargs}]))
    nb.images = SimpleNamespace(iter=lambda **kwargs: iter([{"image_id": "client_1", **kwargs}]))

    assert list(nb.iter_jobs(limit=1)) == [{"id": 1, "limit": 1}]
    assert list(nb.iter_images(client="app01")) == [{"image_id": "client_1", "client": "app01"}]

    nb.close()

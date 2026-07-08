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
    nb.images = SimpleNamespace(list=lambda **kwargs: [{"kind": "image", **kwargs}])
    nb.slp = SimpleNamespace(
        list=lambda **kwargs: [{"kind": "slp", **kwargs}],
        get=lambda name: {"kind": "slp", "name": name},
    )

    assert nb.list_jobs(limit=5) == [{"kind": "job", "limit": 5}]
    assert nb.list_policies(name="prod") == [{"kind": "policy", "name": "prod"}]
    assert nb.list_images(client="app01") == [{"kind": "image", "client": "app01"}]
    assert nb.list_slps(limit=10) == [{"kind": "slp", "limit": 10}]
    assert nb.get_slp("gold-copy") == {"kind": "slp", "name": "gold-copy"}

    nb.close()


def test_generic_collector_keeps_old_fluent_usage_simple() -> None:
    nb = NetBackup(master="master.example.com", token="token")
    nb.jobs = SimpleNamespace(list=lambda **kwargs: [{"id": 1, **kwargs}])

    result = nb.collectors.jobs().collect(start_date="2026-07-01", filter="status eq 0")

    assert result.collector == "jobs"
    assert result.records == [{"id": 1, "start_date": "2026-07-01", "filter": "status eq 0"}]
    assert result.metadata == {"start_date": "2026-07-01", "filter": "status eq 0"}

    nb.close()


def test_collect_by_name() -> None:
    nb = NetBackup(master="master.example.com", token="token")
    nb.images = SimpleNamespace(list=lambda **kwargs: [{"image_id": "client_1", **kwargs}])

    result = nb.collect("images", client="app01")

    assert result.collector == "images"
    assert result.records == [{"image_id": "client_1", "client": "app01"}]

    nb.close()


def test_top_level_iterators_delegate_to_services() -> None:
    nb = NetBackup(master="master.example.com", token="token")
    nb.jobs = SimpleNamespace(iter=lambda **kwargs: iter([{"id": 1, **kwargs}]))
    nb.images = SimpleNamespace(iter=lambda **kwargs: iter([{"image_id": "client_1", **kwargs}]))

    assert list(nb.iter_jobs(limit=1)) == [{"id": 1, "limit": 1}]
    assert list(nb.iter_images(client="app01")) == [{"image_id": "client_1", "client": "app01"}]

    nb.close()


def test_recent_and_state_shortcuts_delegate_to_jobs_and_images() -> None:
    nb = NetBackup(master="master.example.com", token="token")
    nb.jobs = SimpleNamespace(list=lambda **kwargs: [{"kind": "job", **kwargs}])
    nb.images = SimpleNamespace(list=lambda **kwargs: [{"kind": "image", **kwargs}])

    assert nb.list_jobs_last_24h(limit=10) == [{"kind": "job", "last_hours": 24, "limit": 10}]
    assert nb.list_jobs_last_hour() == [{"kind": "job", "last_hours": 1}]
    assert nb.list_running_jobs(limit=5) == [{"kind": "job", "job_state": "running", "limit": 5}]
    assert nb.list_finished_jobs(limit=5) == [{"kind": "job", "job_state": "done", "limit": 5}]
    assert nb.list_images_last_hour(client="app01") == [
        {"kind": "image", "last_hours": 1, "client": "app01"}
    ]

    nb.close()

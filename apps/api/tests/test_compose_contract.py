from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]


def test_compose_declares_required_local_services() -> None:
    compose = yaml.safe_load((ROOT / "docker-compose.yml").read_text(encoding="utf-8"))

    services = compose["services"]
    assert {"api", "worker", "web", "postgres", "redis", "minio"}.issubset(services.keys())


def test_compose_keeps_live_trading_disabled_by_default() -> None:
    compose = yaml.safe_load((ROOT / "docker-compose.yml").read_text(encoding="utf-8"))

    assert compose["services"]["api"]["env_file"] == ".env.example"
    assert "QUANTRESEARCH_LIVE_TRADING_ENABLED=false" in (
        ROOT / ".env.example"
    ).read_text(encoding="utf-8")

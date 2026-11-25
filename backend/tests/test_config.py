import os

from app.core.config import load_local_environment


def test_local_dotenv_exposes_dynamic_provider_credentials(tmp_path, monkeypatch) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("RELIABILITY_PROVIDER_KEY=local-test-secret\n", encoding="utf-8")
    monkeypatch.delenv("RELIABILITY_PROVIDER_KEY", raising=False)

    load_local_environment(env_file)

    assert os.getenv("RELIABILITY_PROVIDER_KEY") == "local-test-secret"


def test_local_dotenv_does_not_override_existing_environment(tmp_path, monkeypatch) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("RELIABILITY_PROVIDER_KEY=dotenv-secret\n", encoding="utf-8")
    monkeypatch.setenv("RELIABILITY_PROVIDER_KEY", "shell-secret")

    load_local_environment(env_file)

    assert os.getenv("RELIABILITY_PROVIDER_KEY") == "shell-secret"

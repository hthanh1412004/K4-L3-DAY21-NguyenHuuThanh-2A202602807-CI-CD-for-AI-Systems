import json
import pytest
from src.authenticate import authenticate


def test_gcp_auth_uses_private_runner_file(tmp_path, monkeypatch):
    env_file = tmp_path / "env"
    monkeypatch.setenv("GITHUB_ENV", str(env_file))
    monkeypatch.setenv("RUNNER_TEMP", str(tmp_path))
    monkeypatch.setenv("CLOUD_PROVIDER", "gcp")
    monkeypatch.setenv("STORAGE_CREDENTIALS", '{"type":"service_account"}')
    authenticate()
    assert json.loads((tmp_path / "income-sa-key.json").read_text())["type"] == "service_account"
    assert "GOOGLE_APPLICATION_CREDENTIALS=" in env_file.read_text()


def test_aws_auth_includes_session_token(tmp_path, monkeypatch):
    env_file = tmp_path / "env"
    monkeypatch.setenv("GITHUB_ENV", str(env_file))
    monkeypatch.setenv("CLOUD_PROVIDER", "aws")
    monkeypatch.setenv("STORAGE_CREDENTIALS", json.dumps({
        "aws_access_key_id": "test-key", "aws_secret_access_key": "test-secret",
        "aws_session_token": "test-session"}))
    authenticate()
    assert "AWS_SESSION_TOKEN=test-session" in env_file.read_text()


def test_auth_rejects_missing_secret(monkeypatch):
    monkeypatch.setenv("STORAGE_CREDENTIALS", "")
    with pytest.raises(ValueError, match="missing"):
        authenticate()

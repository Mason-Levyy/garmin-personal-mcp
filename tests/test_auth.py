import stat

import pytest

from garmin_personal_mcp import auth, config, garmin_client


@pytest.fixture
def garmin(monkeypatch):
    accepted = {"good-key"}
    seen = []

    def verify(api_key=None):
        seen.append(api_key)
        if api_key is not None and api_key not in accepted:
            raise garmin_client.ApiKeyError("Garmin rejected the Personal API key")

    monkeypatch.setattr(auth, "verify", verify)
    return seen


def paste(monkeypatch, value):
    monkeypatch.setattr(auth.getpass, "getpass", lambda prompt: value)


def test_save_key_is_owner_only():
    path = auth.save_key("secret")
    assert path == config.key_file()
    assert path.read_text() == "secret\n"
    assert stat.S_IMODE(path.stat().st_mode) == 0o600


def test_auth_verifies_then_saves(monkeypatch, garmin, capsys):
    paste(monkeypatch, "  good-key \n")
    assert auth.run_auth_flow() == 0
    assert garmin == ["good-key"]
    assert config.key_file().read_text() == "good-key\n"
    assert "Connected" in capsys.readouterr().out


def test_rejected_key_is_not_saved(monkeypatch, garmin):
    paste(monkeypatch, "bad-key")
    assert auth.run_auth_flow() == 1
    assert not config.key_file().exists()


def test_empty_key_is_not_saved(monkeypatch, garmin):
    paste(monkeypatch, "  ")
    assert auth.run_auth_flow() == 1
    assert garmin == []


def test_auth_warns_when_env_var_shadows_the_file(monkeypatch, garmin, capsys):
    monkeypatch.setenv("GARMIN_PERSONAL_API_KEY", "other")
    paste(monkeypatch, "good-key")
    auth.run_auth_flow()
    assert "takes precedence" in capsys.readouterr().out


def test_check_reports_connection(garmin, capsys):
    assert auth.run_check() == 0
    assert "Connected" in capsys.readouterr().out

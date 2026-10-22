import sys

import pytest

from garmin_personal_mcp import auth, cli


def test_transport_security_accepts_an_extra_host_on_any_port():
    settings = cli.transport_security(["box.example.ts.net"])
    assert "box.example.ts.net:*" in settings.allowed_hosts
    assert "127.0.0.1:*" in settings.allowed_hosts
    assert "https://box.example.ts.net:*" in settings.allowed_origins


def test_check_only_applies_to_auth(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["garmin-personal-mcp", "--check"])
    with pytest.raises(SystemExit) as exit_info:
        cli.main()
    assert exit_info.value.code == 2


def test_auth_check_exit_code(monkeypatch):
    monkeypatch.setattr(auth, "run_check", lambda: 1)
    monkeypatch.setattr(sys, "argv", ["garmin-personal-mcp", "auth", "--check"])
    with pytest.raises(SystemExit) as exit_info:
        cli.main()
    assert exit_info.value.code == 1

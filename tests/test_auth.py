import stat
import sys

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


class Stdin:
    def __init__(self, text, tty):
        self.text = text
        self.tty = tty

    def isatty(self):
        return self.tty

    def readline(self):
        return self.text


def paste(monkeypatch, value):
    monkeypatch.setattr(auth.sys, "stdin", Stdin("", tty=True))
    monkeypatch.setattr(auth.getpass, "getpass", lambda prompt: value)


def pipe(monkeypatch, text):
    def no_prompt(prompt):
        raise AssertionError("getpass needs a terminal")

    monkeypatch.setattr(auth.sys, "stdin", Stdin(text, tty=False))
    monkeypatch.setattr(auth.getpass, "getpass", no_prompt)


def test_save_key_writes_inside_the_test_home(isolated_home):
    path = auth.save_key("secret")
    assert path == config.key_file()
    assert path.is_relative_to(isolated_home)
    assert path.read_text() == "secret\n"


@pytest.mark.skipif(sys.platform == "win32", reason="Windows has no POSIX file modes")
def test_save_key_is_owner_only():
    path = auth.save_key("secret")
    assert stat.S_IMODE(path.stat().st_mode) == 0o600


def test_auth_verifies_then_saves(monkeypatch, garmin, capsys):
    paste(monkeypatch, "  good-key \n")
    assert auth.run_auth_flow() == 0
    assert garmin == ["good-key"]
    assert config.key_file().read_text() == "good-key\n"
    assert "Connected" in capsys.readouterr().out


def test_piped_key_is_read_without_a_terminal(monkeypatch, garmin):
    pipe(monkeypatch, "good-key\n")
    assert auth.run_auth_flow() == 0
    assert config.key_file().read_text() == "good-key\n"


def test_no_terminal_and_nothing_piped_explains_instead_of_crashing(
    monkeypatch, garmin, capsys
):
    pipe(monkeypatch, "")
    assert auth.run_auth_flow() == 1
    assert "pipe the key in" in capsys.readouterr().out
    assert garmin == []


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


def test_unreachable_garmin_explains_and_saves_nothing(monkeypatch, capsys):
    def offline(api_key=None):
        raise ConnectionError("proxy refused the tunnel")

    monkeypatch.setattr(auth, "verify", offline)
    paste(monkeypatch, "good-key")
    assert auth.run_auth_flow() == 1
    assert not config.key_file().exists()
    output = capsys.readouterr().out
    assert "Couldn't reach Garmin" in output
    assert "didn't accept" not in output


def test_check_reports_unreachable_garmin(monkeypatch, capsys):
    def offline(api_key=None):
        raise TimeoutError("timed out")

    monkeypatch.setattr(auth, "verify", offline)
    assert auth.run_check() == 1
    assert "Couldn't reach Garmin" in capsys.readouterr().out

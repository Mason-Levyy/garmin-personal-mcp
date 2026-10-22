from dataclasses import dataclass

import pytest
from garmin_personal_api import GarminPersonalApiError, HttpError

from garmin_personal_mcp import garmin


def http_error(status: int) -> HttpError:
    return HttpError(status_code=status, method="GET", url="/x", response_text="nope")


@dataclass
class Token:
    access_token: str


class FakeAuthenticator:
    def __init__(self, failure: Exception | None = None):
        self.failure = failure
        self.requests = []

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        pass

    def obtain_token(self, api_key, *, force_refresh=False):
        self.requests.append((api_key, force_refresh))
        if self.failure is not None:
            raise self.failure
        return Token(f"token-{len(self.requests)}")


class FakeClient:
    def __init__(self, access_token):
        self.access_token = access_token

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        pass


@pytest.fixture
def authenticator(monkeypatch):
    fake = FakeAuthenticator()
    monkeypatch.setattr(garmin, "PersonalApiAuthenticator", lambda: fake)
    monkeypatch.setattr(garmin, "GarminPersonalApiClient", FakeClient)
    monkeypatch.setattr(garmin, "resolve_api_key", lambda: "the-key")
    return fake


def test_call_uses_cached_token(authenticator):
    assert garmin.call(lambda c: c.access_token) == "token-1"
    assert authenticator.requests == [("the-key", False)]


def test_call_retries_once_with_fresh_token_on_401(authenticator):
    def op(client):
        if client.access_token == "token-1":
            raise http_error(401)
        return client.access_token

    assert garmin.call(op) == "token-2"
    assert authenticator.requests == [("the-key", False), ("the-key", True)]


def test_call_does_not_retry_other_http_errors(authenticator):
    def op(client):
        raise http_error(404)

    with pytest.raises(HttpError):
        garmin.call(op)
    assert len(authenticator.requests) == 1


def test_rejected_key_explains_how_to_fix(authenticator):
    authenticator.failure = http_error(401)
    with pytest.raises(garmin.ApiKeyError, match="personalApiToken"):
        garmin.call(lambda c: None)


def test_missing_key_explains_how_to_fix(authenticator, monkeypatch):
    def no_key():
        raise GarminPersonalApiError("No personal API key was provided.")

    monkeypatch.setattr(garmin, "resolve_api_key", no_key)
    with pytest.raises(garmin.ApiKeyError, match="GARMIN_PERSONAL_API_KEY"):
        garmin.call(lambda c: None)


def test_read_sections_isolates_missing_data():
    def missing(client):
        raise http_error(404)

    record = garmin.read_sections(None, {"ok": lambda c: 1, "missing": missing})
    assert record["ok"] == 1
    assert "404" in record["missing"]["error"]


def test_read_sections_propagates_401_so_call_can_retry():
    def expired(client):
        raise http_error(401)

    with pytest.raises(HttpError):
        garmin.read_sections(None, {"expired": expired})

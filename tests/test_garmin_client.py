from dataclasses import dataclass

import pytest
from conftest import http_error
from garmin_personal_api import GarminPersonalApiError, HttpError

from garmin_personal_mcp import garmin_client


@dataclass
class Token:
    access_token: str


class FakeAuthenticator:
    def __init__(self):
        self.failure = None
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


class TokenClient:
    def __init__(self, access_token):
        self.access_token = access_token

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        pass


@pytest.fixture
def authenticator(monkeypatch):
    fake = FakeAuthenticator()
    monkeypatch.setattr(garmin_client, "PersonalApiAuthenticator", lambda: fake)
    monkeypatch.setattr(garmin_client, "GarminPersonalApiClient", TokenClient)
    monkeypatch.setenv("GARMIN_PERSONAL_API_KEY", "the-key")
    return fake


def test_call_uses_cached_token(authenticator):
    assert garmin_client.call(lambda c: c.access_token) == "token-1"
    assert authenticator.requests == [("the-key", False)]


def test_explicit_key_overrides_discovery(authenticator):
    garmin_client.call(lambda c: None, api_key="pasted")
    assert authenticator.requests == [("pasted", False)]


def test_call_retries_once_with_fresh_token_on_401(authenticator):
    def op(client):
        if client.access_token == "token-1":
            raise http_error(401)
        return client.access_token

    assert garmin_client.call(op) == "token-2"
    assert authenticator.requests == [("the-key", False), ("the-key", True)]


def test_call_does_not_retry_other_http_errors(authenticator):
    def op(client):
        raise http_error(404)

    with pytest.raises(HttpError):
        garmin_client.call(op)
    assert len(authenticator.requests) == 1


@pytest.mark.parametrize("status", [400, 401, 403])
def test_rejected_key_explains_how_to_fix(authenticator, status):
    authenticator.failure = http_error(status)
    with pytest.raises(garmin_client.ApiKeyError, match="garmin-personal-mcp auth"):
        garmin_client.call(lambda c: None)


def test_token_server_errors_are_not_blamed_on_the_key(authenticator):
    authenticator.failure = http_error(503)
    with pytest.raises(HttpError):
        garmin_client.call(lambda c: None)


def test_missing_key_explains_how_to_fix(authenticator, monkeypatch):
    monkeypatch.delenv("GARMIN_PERSONAL_API_KEY")
    with pytest.raises(garmin_client.ApiKeyError, match="personalApiToken"):
        garmin_client.call(lambda c: None)


def test_unusable_token_explains_how_to_fix(authenticator):
    authenticator.failure = GarminPersonalApiError("not a JWT")
    with pytest.raises(garmin_client.ApiKeyError, match="not a JWT"):
        garmin_client.call(lambda c: None)

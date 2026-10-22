import json
from pathlib import Path

import pytest
from garmin_personal_api import HttpError

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name):
    return json.loads((FIXTURES / name).read_text())


def http_error(status):
    return HttpError(
        status_code=status, method="GET", url="/fake", response_text="nope"
    )


class FakeClient:
    """Routes GETs by path fragment. Unrouted paths answer None, like Garmin's
    204 for a day with no data."""

    def __init__(self, routes=None):
        self.routes = routes or {}
        self.calls = []
        self.downloads = {}

    def get(self, path, *, params=None):
        self.calls.append((path, params))
        for fragment, response in self.routes.items():
            if fragment not in path:
                continue
            if isinstance(response, Exception):
                raise response
            if callable(response):
                return response(path, params)
            return response
        return None

    def download_activity(self, activity_id):
        return self.downloads[activity_id]


@pytest.fixture(autouse=True)
def isolated_home(tmp_path, monkeypatch):
    """Keeps key files and the bearer-token cache away from the real home."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("GARMIN_PERSONAL_API_KEY", raising=False)
    monkeypatch.delenv("GARMIN_MCP_DOWNLOAD_DIR", raising=False)
    return tmp_path


@pytest.fixture
def client():
    return FakeClient()

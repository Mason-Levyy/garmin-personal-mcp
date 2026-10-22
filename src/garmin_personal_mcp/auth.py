import getpass
import os
import sys
from pathlib import Path

from garmin_personal_api import GarminPersonalApiError

from . import config, garmin_client, profile

UNREACHABLE_HINT = "Check your internet connection or proxy, then try again."


def save_key(key: str) -> Path:
    path = config.key_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as key_file:
        key_file.write(key + "\n")
    path.chmod(0o600)
    return path


def verify(api_key: str | None = None) -> None:
    garmin_client.call(profile.get_settings, api_key=api_key)


def read_key() -> str:
    """Without a terminal (a pipe, or a shell an agent runs), getpass can't
    hide input and raises EOFError, so read one line from stdin instead."""
    if not sys.stdin.isatty():
        return sys.stdin.readline().strip()
    print(
        "Create a Garmin Connect Personal API key (it is shown only once):\n"
        f"  {garmin_client.KEY_PAGE}\n",
        flush=True,
    )
    return getpass.getpass("Paste the key (input is hidden): ").strip()


def run_auth_flow() -> int:
    key = read_key()
    if not key:
        print(
            "No key entered; nothing saved. Run `garmin-personal-mcp auth` in a "
            "terminal, or pipe the key in on stdin."
        )
        return 1
    try:
        verify(key)
    except (GarminPersonalApiError, garmin_client.ApiKeyError) as exc:
        print(f"Garmin didn't accept that key, so it wasn't saved: {exc}")
        return 1
    # requests' connection errors and timeouts subclass OSError, and Garmin's
    # client lets them through unwrapped.
    except OSError as exc:
        print(
            f"Couldn't reach Garmin to check the key ({type(exc).__name__}), so it "
            f"wasn't saved. {UNREACHABLE_HINT}"
        )
        return 1
    path = save_key(key)
    print(f"Connected to Garmin Connect. Key saved to {path} (owner-only permissions).")
    if os.environ.get(config.KEY_ENV_VAR):
        print(
            f"Note: {config.KEY_ENV_VAR} is set and takes precedence over the "
            "saved key; unset it to use the new one."
        )
    return 0


def run_check() -> int:
    try:
        verify()
    except (GarminPersonalApiError, garmin_client.ApiKeyError) as exc:
        print(f"Not connected: {exc}")
        return 1
    except OSError as exc:
        print(f"Couldn't reach Garmin ({type(exc).__name__}). {UNREACHABLE_HINT}")
        return 1
    print("Connected to Garmin Connect.")
    return 0

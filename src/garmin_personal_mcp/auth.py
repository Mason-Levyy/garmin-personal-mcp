import getpass
import os
from pathlib import Path

from garmin_personal_api import GarminPersonalApiError

from . import config, garmin_client, profile


def save_key(key: str) -> Path:
    path = config.key_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as key_file:
        key_file.write(key + "\n")
    path.chmod(0o600)
    return path


def display_name(api_key: str | None = None) -> str:
    settings = garmin_client.call(profile.get_settings, api_key=api_key) or {}
    return settings.get("displayName") or "your Garmin account"


def run_auth_flow() -> int:
    print(
        "Create a Garmin Connect Personal API key (it is shown only once):\n"
        f"  {garmin_client.KEY_PAGE}\n"
    )
    key = getpass.getpass("Paste the key (input is hidden): ").strip()
    if not key:
        print("No key entered; nothing saved.")
        return 1
    try:
        name = display_name(key)
    except (GarminPersonalApiError, garmin_client.ApiKeyError) as exc:
        print(f"Garmin didn't accept that key, so it wasn't saved: {exc}")
        return 1
    path = save_key(key)
    print(f"Connected to {name}. Key saved to {path} (owner-only permissions).")
    if os.environ.get(config.KEY_ENV_VAR):
        print(
            f"Note: {config.KEY_ENV_VAR} is set and takes precedence over the "
            "saved key; unset it to use the new one."
        )
    return 0


def run_check() -> int:
    try:
        name = display_name()
    except (GarminPersonalApiError, garmin_client.ApiKeyError) as exc:
        print(f"Not connected: {exc}")
        return 1
    print(f"Connected to {name}.")
    return 0

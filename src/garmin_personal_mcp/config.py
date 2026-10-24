import os
from pathlib import Path

import platformdirs
from garmin_personal_api import DEFAULT_API_KEY_FILE

KEY_ENV_VAR = "GARMIN_PERSONAL_API_KEY"
DOWNLOAD_DIR_ENV_VAR = "GARMIN_MCP_DOWNLOAD_DIR"


def key_file() -> Path:
    return DEFAULT_API_KEY_FILE.expanduser()


def download_dir() -> Path:
    configured = os.environ.get(DOWNLOAD_DIR_ENV_VAR)
    if configured:
        return Path(configured).expanduser()
    return Path(platformdirs.user_downloads_dir()) / "garmin"


def download_target(directory: str | None) -> Path:
    base = download_dir()
    if directory is None:
        return base
    target = (base / Path(directory).expanduser()).resolve()
    if not target.is_relative_to(base.resolve()):
        raise ValueError(
            f"directory must be inside {base}; pass a subfolder name such as "
            f"'races', or set {DOWNLOAD_DIR_ENV_VAR} to change the download folder"
        )
    return target

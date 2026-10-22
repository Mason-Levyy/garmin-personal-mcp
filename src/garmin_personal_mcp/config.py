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

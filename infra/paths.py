import os
import sys
from typing import Optional

try:
    from appdirs import user_data_dir
except Exception:  # pragma: no cover - appdirs is a runtime dependency
    user_data_dir = None  # type: ignore


APP_NAME: str = "SchoolTimetableWidgetV2"
APP_AUTHOR: str = "Timetable"


def get_data_directory() -> str:
    """Return the per-user data directory for the app, ensuring it exists.

    On Windows, this resolves to %APPDATA%\\<Author>\\<AppName>.
    Falls back to a folder next to the executable when appdirs is unavailable.
    """
    base_dir: Optional[str] = None

    if user_data_dir is not None:
        base_dir = user_data_dir(APP_NAME, APP_AUTHOR)
    else:
        # Fallback: place under the executable directory
        if getattr(sys, "frozen", False):
            base_dir = os.path.join(os.path.dirname(sys.executable), APP_NAME)
        else:
            base_dir = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")), "_data")

    if not os.path.exists(base_dir):
        os.makedirs(base_dir, exist_ok=True)
    return base_dir


def get_log_directory() -> str:
    """Return the directory where log files are stored."""
    path = os.path.join(get_data_directory(), "logs")
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
    return path


def get_config_file_path() -> str:
    """Return the path to the main JSON config file."""
    return os.path.join(get_data_directory(), "config.json")


def resource_path(relative_path: str) -> str:
    """Return absolute path to resource, works for dev and PyInstaller bundle.

    When frozen by PyInstaller, resources are located under sys._MEIPASS.
    """
    base_path = getattr(sys, "_MEIPASS", None)
    if base_path:
        return os.path.join(base_path, relative_path)
    # Dev mode: resolve from project root
    return os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")), relative_path)



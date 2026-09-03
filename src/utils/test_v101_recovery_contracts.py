"""Behavioral contracts for recovering the distributed v1.0.1 application.

The executable's missing cell-sizing and debounced-save implementations are
specified below, but deliberately are not represented by failing, skipped, or
xfail tests.  Once production APIs exist, the data tables in this module can be
used directly as parametrized test inputs.

Future cell-size contract
-------------------------
The release notes define these logical rules::

    minimum cell height = font size * 2.5 * DPI scale
    minimum cell width  = font size * 3.0 * DPI scale

For a representative 10-point font, the expected values are:

    DPI   scale   minimum height   minimum width
    100%  1.00    25.00            30.00
    125%  1.25    31.25            37.50
    150%  1.50    37.50            45.00
    200%  2.00    50.00            60.00

The eventual implementation must also enforce these contracts:

* A calculated widget minimum takes precedence over a smaller saved size.
* Per-cell sizes and ratios are not persisted.
* Widget position and total widget size remain persisted.

Future debounced-save contract
------------------------------
The eventual SettingsManager implementation must satisfy all of the following:

* Multiple save requests in a short interval cause one physical write.
* The final requested state is the state written.
* Application shutdown flushes a pending write.
* Position and auto-start changes cannot overwrite one another.
* Readers never observe malformed or partially-written JSON during a save.
"""

import importlib
import json
import sys

import pytest

from utils.config import Config
from utils.paths import get_widget_settings_file_path
from utils.settings_manager import SettingsManager


# Ready-made inputs for the future production cell-size calculation tests.
V101_CELL_SIZE_CASES_FOR_TEN_POINT_FONT = (
    pytest.param(1.00, 25.00, 30.00, id="100-percent-dpi"),
    pytest.param(1.25, 31.25, 37.50, id="125-percent-dpi"),
    pytest.param(1.50, 37.50, 45.00, id="150-percent-dpi"),
    pytest.param(2.00, 50.00, 60.00, id="200-percent-dpi"),
)


@pytest.fixture(autouse=True)
def isolated_settings_manager(tmp_path, monkeypatch):
    """Keep every SettingsManager read and write out of user AppData."""
    monkeypatch.setenv("SCHOOL_TIMETABLE_DATA_DIR", str(tmp_path))
    SettingsManager._instance = None
    yield
    SettingsManager._instance = None


@pytest.mark.parametrize(
    ("current", "latest", "update_required"),
    (
        pytest.param("1.0.0", "v1.0.0", False, id="same-version"),
        pytest.param("1.0.0", "v1.0.1", True, id="newer-release"),
        pytest.param("1.0.1", "v1.0.1", False, id="installed-release"),
        pytest.param("1.0.10", "v1.0.9", False, id="numeric-patch-order"),
        pytest.param("v1.0.0", "v1.0.1", True, id="v-prefix-on-both-sides"),
    ),
)
def test_updater_numeric_version_comparison_contract(
    tmp_path, current, latest, update_required
):
    """Characterize Updater without performing a GitHub request."""
    # Importing main configures logging, so it happens only after the fixture
    # redirects the application's data directory to tmp_path.
    sys.modules.pop("main", None)
    main_module = importlib.import_module("main")

    assert main_module.Updater.is_newer_version(latest, current) is update_required


def _reload_settings_manager():
    SettingsManager._instance = None
    return SettingsManager.get_instance()


def test_widget_position_round_trips():
    manager = SettingsManager.get_instance()
    manager.save_widget_position(210, 320, 640, 480)

    restored = _reload_settings_manager()

    assert restored.widget_position == {"x": 210, "y": 320}


def test_widget_size_round_trips():
    manager = SettingsManager.get_instance()
    manager.save_widget_position(210, 320, 640, 480)

    restored = _reload_settings_manager()

    assert restored.widget_size == {"width": 640, "height": 480}


def test_widget_position_lock_round_trips():
    manager = SettingsManager.get_instance()
    manager.is_position_locked = True
    manager.save_widget_settings()

    restored = _reload_settings_manager()

    assert restored.is_position_locked is True


def test_widget_screen_info_round_trips():
    screen_info = {"geometry": [1920, 0, 1920, 1080], "name": "MockScreen1"}
    manager = SettingsManager.get_instance()
    manager.save_widget_position(210, 320, 640, 480, screen_info)

    restored = _reload_settings_manager()

    assert restored.widget_screen_info == screen_info


def test_auto_start_enabled_round_trips_without_touching_startup_or_registry():
    manager = SettingsManager.get_instance()
    manager.auto_start_enabled = True
    manager.save_widget_settings()

    restored = _reload_settings_manager()

    assert restored.auto_start_enabled is True


def test_missing_widget_settings_file_preserves_defaults(tmp_path):
    assert not (tmp_path / "widget_settings.json").exists()

    manager = SettingsManager.get_instance()

    assert manager.widget_position == {
        "x": Config.DEFAULT_WINDOW_POSITION[0],
        "y": Config.DEFAULT_WINDOW_POSITION[1],
    }
    assert manager.widget_size == {
        "width": Config.DEFAULT_WINDOW_SIZE[0],
        "height": Config.DEFAULT_WINDOW_SIZE[1],
    }
    assert manager.is_position_locked is False
    assert manager.widget_screen_info is None
    assert manager.auto_start_enabled is False


def test_corrupt_widget_settings_json_is_backed_up_and_defaults_are_kept(tmp_path):
    settings_path = tmp_path / "widget_settings.json"
    settings_path.write_text('{"position": ', encoding="utf-8")

    manager = SettingsManager.get_instance()

    assert manager.widget_position == {
        "x": Config.DEFAULT_WINDOW_POSITION[0],
        "y": Config.DEFAULT_WINDOW_POSITION[1],
    }
    assert manager.widget_size == {
        "width": Config.DEFAULT_WINDOW_SIZE[0],
        "height": Config.DEFAULT_WINDOW_SIZE[1],
    }
    assert manager.is_position_locked is False
    assert manager.widget_screen_info is None
    assert manager.auto_start_enabled is False
    assert not settings_path.exists()

    backups = list(tmp_path.rglob("widget_settings_backup_widget_settings.json_*"))
    assert len(backups) == 1
    assert backups[0].read_text(encoding="utf-8") == '{"position": '


def test_widget_settings_persist_only_total_geometry_and_shared_options():
    manager = SettingsManager.get_instance()
    manager.save_widget_position(210, 320, 640, 480)

    with open(get_widget_settings_file_path(), encoding="utf-8") as settings_file:
        saved = json.load(settings_file)

    assert set(saved) == {
        "position",
        "size",
        "is_position_locked",
        "screen_info",
        "auto_start_enabled",
    }
    assert not any("cell" in key.lower() or "ratio" in key.lower() for key in saved)

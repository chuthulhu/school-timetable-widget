"""Behavioral contracts for recovering the distributed v1.0.1 application.

The executable's recovered cell-sizing and debounced-save implementations are
specified and exercised below.

Cell-size contract
------------------
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

Recovered debounced-save contract
---------------------------------
SettingsManager must satisfy all of the following:

* Multiple save requests in a short interval cause one physical write.
* The final requested state is the state written.
* Application shutdown flushes a pending write.
* Position and auto-start changes cannot overwrite one another.
* Readers never observe malformed or partially-written JSON during a save.
"""

import importlib
import json
import math
import os
import re
import sys

import pytest
from PyQt5 import QtCore, QtWidgets

from gui.widget import Widget
from utils.config import Config
from utils.paths import get_widget_settings_file_path
from utils.settings_manager import SettingsManager
from utils.styling import calculate_minimum_cell_size


# Release-derived inputs for the production cell-size calculation tests.
V101_CELL_SIZE_CASES_FOR_TEN_POINT_FONT = (
    pytest.param(1.00, 25.00, 30.00, id="100-percent-dpi"),
    pytest.param(1.25, 31.25, 37.50, id="125-percent-dpi"),
    pytest.param(1.50, 37.50, 45.00, id="150-percent-dpi"),
    pytest.param(2.00, 50.00, 60.00, id="200-percent-dpi"),
)


@pytest.mark.parametrize(
    ("dpi_scale", "expected_height", "expected_width"),
    V101_CELL_SIZE_CASES_FOR_TEN_POINT_FONT,
)
def test_v101_minimum_cell_size_dpi_contract(
    dpi_scale, expected_height, expected_width
):
    width, height = calculate_minimum_cell_size(10, dpi_scale)

    assert width == pytest.approx(expected_width)
    assert height == pytest.approx(expected_height)


@pytest.mark.parametrize(
    ("font_size", "dpi_scale"),
    (
        pytest.param(6, 1.25, id="small-font"),
        pytest.param(24, 1.50, id="large-font"),
    ),
)
def test_v101_minimum_cell_size_is_linear_for_other_font_sizes(
    font_size, dpi_scale
):
    width, height = calculate_minimum_cell_size(font_size, dpi_scale)

    assert width == pytest.approx(font_size * 3.0 * dpi_scale)
    assert height == pytest.approx(font_size * 2.5 * dpi_scale)


def test_widget_dpi_scale_uses_logical_dpi_without_device_pixel_ratio():
    class ScreenStub:
        def logicalDotsPerInch(self):
            return 120.0

        def devicePixelRatio(self):
            raise AssertionError("devicePixelRatio must not be applied")

    class WidgetStub:
        BASE_LOGICAL_DPI = 96.0

        def _get_target_screen(self):
            return ScreenStub()

    assert Widget._get_initial_dpi_scale(WidgetStub()) == pytest.approx(1.25)


@pytest.fixture(autouse=True)
def isolated_settings_manager(tmp_path, monkeypatch):
    """Keep every SettingsManager read and write out of user AppData."""
    monkeypatch.setenv("SCHOOL_TIMETABLE_DATA_DIR", str(tmp_path))
    SettingsManager._instance = None
    yield
    SettingsManager._instance = None


@pytest.fixture(scope="module")
def qapplication():
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    application = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    yield application


class _NotificationStub:
    next_period_warning = False
    warning_minutes = 5

    def check_notifications(self, *args):
        pass


def _create_widget(monkeypatch, manager, dpi_scale):
    monkeypatch.setattr(
        Widget,
        "_get_initial_dpi_scale",
        lambda self: dpi_scale,
    )
    widget = Widget(
        settings_manager=manager,
        notification_manager=_NotificationStub(),
    )
    widget.timer.stop()
    return widget


def test_widget_applies_cell_and_grid_minimums(qapplication, monkeypatch):
    manager = SettingsManager.get_instance()
    manager.header_font_size = 11
    manager.cell_font_size = 10
    widget = _create_widget(monkeypatch, manager, dpi_scale=2.0)

    header_width, header_height = calculate_minimum_cell_size(11, 2.0)
    cell_width, cell_height = calculate_minimum_cell_size(10, 2.0)
    expected_weekday_width = math.ceil(max(header_width, cell_width))
    expected_period_height = math.ceil(max(header_height, cell_height))

    assert all(
        label.minimumWidth() == math.ceil(header_width)
        for label in widget.day_headers.values()
    )
    assert all(
        label.minimumHeight() == expected_period_height
        for label in widget.period_headers.values()
    )
    assert all(
        cell.minimumSize()
        == QtCore.QSize(math.ceil(cell_width), math.ceil(cell_height))
        for cell in widget.cell_widgets.values()
    )
    assert widget.grid_layout.columnMinimumWidth(1) == expected_weekday_width
    assert widget.grid_layout.rowMinimumHeight(1) == expected_period_height
    assert widget.minimumWidth() >= Config.DEFAULT_WINDOW_SIZE[0]
    assert widget.minimumHeight() >= Config.DEFAULT_WINDOW_SIZE[1]

    widget.deleteLater()


def test_smaller_saved_size_is_clamped_to_widget_minimum(
    qapplication, monkeypatch
):
    manager = SettingsManager.get_instance()
    manager.header_font_size = 24
    manager.cell_font_size = 24
    manager.widget_size = {"width": 10, "height": 10}
    widget = _create_widget(monkeypatch, manager, dpi_scale=2.0)

    assert widget.size() == widget.minimumSize()
    assert widget.width() > manager.widget_size["width"]
    assert widget.height() > manager.widget_size["height"]

    widget.deleteLater()


def test_normal_saved_size_is_preserved(qapplication, monkeypatch):
    manager = SettingsManager.get_instance()
    manager.widget_size = {"width": 800, "height": 650}
    widget = _create_widget(monkeypatch, manager, dpi_scale=1.0)

    assert widget.size() == QtCore.QSize(800, 650)

    widget.deleteLater()


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
    if SettingsManager._instance is not None:
        SettingsManager._instance.flush_pending_widget_settings()
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
    manager.flush_pending_widget_settings()

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


def test_multiple_widget_save_requests_are_merged_into_one_write(monkeypatch):
    application = QtCore.QCoreApplication.instance() or QtCore.QCoreApplication([])
    manager = SettingsManager.get_instance()
    writes = []
    monkeypatch.setattr(
        manager,
        "_write_widget_settings_atomically",
        lambda snapshot: writes.append(snapshot),
    )

    manager.save_widget_settings()
    manager.widget_size = {"width": 700, "height": 500}
    manager.save_widget_settings()
    manager.widget_size = {"width": 800, "height": 600}
    manager.save_widget_settings()
    assert manager._widget_settings_save_timer.isActive()

    manager._widget_settings_save_timer.timeout.emit()

    assert len(writes) == 1
    assert writes[0]["size"] == {"width": 800, "height": 600}
    assert not manager._widget_settings_save_timer.isActive()
    assert application is QtCore.QCoreApplication.instance()


def test_position_then_auto_start_save_preserves_both_latest_values():
    manager = SettingsManager.get_instance()
    manager.save_widget_position(410, 520, 800, 600)
    manager.set_auto_start(True)

    manager.flush_pending_widget_settings()

    with open(get_widget_settings_file_path(), encoding="utf-8") as settings_file:
        saved = json.load(settings_file)
    assert saved["position"] == {"x": 410, "y": 520}
    assert saved["size"] == {"width": 800, "height": 600}
    assert saved["auto_start_enabled"] is True


def test_flush_writes_pending_settings_before_debounce_timeout(tmp_path):
    manager = SettingsManager.get_instance()
    manager.save_widget_position(510, 620, 900, 700)
    settings_path = tmp_path / "widget_settings.json"
    assert not settings_path.exists()

    manager.flush_pending_widget_settings()

    assert settings_path.exists()
    assert json.loads(settings_path.read_text(encoding="utf-8"))["position"] == {
        "x": 510,
        "y": 620,
    }


def test_flush_without_pending_settings_is_a_safe_no_op():
    manager = SettingsManager.get_instance()

    manager.flush_pending_widget_settings()

    assert manager._pending_widget_settings is None


def test_atomic_widget_settings_write_produces_valid_final_json(tmp_path):
    manager = SettingsManager.get_instance()
    manager.save_widget_position(610, 720, 1000, 800)

    manager.flush_pending_widget_settings()

    settings_path = tmp_path / "widget_settings.json"
    saved = json.loads(settings_path.read_text(encoding="utf-8"))
    assert saved["position"] == {"x": 610, "y": 720}
    assert list(tmp_path.glob(".widget_settings_*.tmp")) == []


def test_failed_atomic_replace_preserves_existing_valid_file(tmp_path, monkeypatch):
    settings_path = tmp_path / "widget_settings.json"
    original = {
        "position": {"x": 10, "y": 20},
        "size": {"width": 400, "height": 300},
        "is_position_locked": False,
        "screen_info": None,
        "auto_start_enabled": False,
    }
    settings_path.write_text(json.dumps(original), encoding="utf-8")
    manager = SettingsManager.get_instance()
    manager.save_widget_position(710, 820, 1100, 900)

    def fail_replace(source, destination):
        raise OSError("simulated replace failure")

    with monkeypatch.context() as replace_patch:
        replace_patch.setattr("utils.settings_manager.os.replace", fail_replace)
        manager.flush_pending_widget_settings()

    assert json.loads(settings_path.read_text(encoding="utf-8")) == original
    assert manager._pending_widget_settings is not None
    assert list(tmp_path.glob(".widget_settings_*.tmp")) == []

    manager.flush_pending_widget_settings()

    saved = json.loads(settings_path.read_text(encoding="utf-8"))
    assert saved["position"] == {"x": 710, "y": 820}
    assert saved["size"] == {"width": 1100, "height": 900}
    assert manager._pending_widget_settings is None


def test_create_backup_flushes_pending_widget_settings(tmp_path):
    manager = SettingsManager.get_instance()
    manager.save_widget_position(810, 920, 1200, 1000)
    assert manager._pending_widget_settings is not None

    success, backup_path = manager.create_backup()

    assert success is True
    backup_settings_path = os.path.join(backup_path, "widget_settings.json")
    with open(backup_settings_path, encoding="utf-8") as backup_file:
        backed_up = json.load(backup_file)
    assert backed_up["position"] == {"x": 810, "y": 920}
    assert backed_up["size"] == {"width": 1200, "height": 1000}
    assert manager._pending_widget_settings is None


def test_create_backup_without_name_uses_existing_automatic_name_format():
    manager = SettingsManager.get_instance()

    success, backup_path = manager.create_backup()

    assert success is True
    assert re.fullmatch(r"backup_\d{8}_\d{6}", os.path.basename(backup_path))


def test_create_backup_with_explicit_name_succeeds():
    manager = SettingsManager.get_instance()

    success, backup_path = manager.create_backup("명시적이름")

    assert success is True
    assert os.path.basename(backup_path) == "명시적이름"


def test_explicit_backup_name_preserves_description_format():
    manager = SettingsManager.get_instance()

    success, backup_path = manager.create_backup("설명형식확인")

    assert success is True
    with open(os.path.join(backup_path, "description.txt"), encoding="utf-8") as file:
        description = file.read()
    assert re.fullmatch(
        r"시간표 백업 - \d{4}년 \d{2}월 \d{2}일 \d{2}:\d{2}:\d{2}",
        description,
    )


def test_restore_backup_cannot_be_overwritten_by_an_older_pending_snapshot(tmp_path):
    backup_name = "restore_pending_contract"
    backup_path = tmp_path / "backups" / backup_name
    backup_path.mkdir(parents=True)
    restored_settings = {
        "position": {"x": 31, "y": 42},
        "size": {"width": 430, "height": 320},
        "is_position_locked": True,
        "screen_info": {"geometry": [0, 0, 1920, 1080], "name": "Restored"},
        "auto_start_enabled": True,
    }
    (backup_path / "widget_settings.json").write_text(
        json.dumps(restored_settings),
        encoding="utf-8",
    )
    manager = SettingsManager.get_instance()
    manager.save_widget_position(910, 1020, 1300, 1100)
    assert manager._pending_widget_settings is not None

    success, message = manager.restore_backup(backup_name)
    manager._widget_settings_save_timer.timeout.emit()

    assert success is True, message
    final_path = tmp_path / "widget_settings.json"
    assert json.loads(final_path.read_text(encoding="utf-8")) == restored_settings
    assert manager._pending_widget_settings is None
    assert not manager._widget_settings_save_timer.isActive()


def test_create_backup_stops_when_pending_widget_flush_fails(tmp_path, monkeypatch):
    settings_path = tmp_path / "widget_settings.json"
    original = {"position": {"x": 1, "y": 2}}
    settings_path.write_text(json.dumps(original), encoding="utf-8")
    manager = SettingsManager.get_instance()
    manager.save_widget_position(1010, 1120, 1400, 1200)

    monkeypatch.setattr(
        manager,
        "_write_widget_settings_atomically",
        lambda snapshot: (_ for _ in ()).throw(OSError("simulated write failure")),
    )
    success, message = manager.create_backup("must_not_exist")

    assert success is False
    assert "위젯 설정" in message
    assert manager._pending_widget_settings is not None
    assert json.loads(settings_path.read_text(encoding="utf-8")) == original
    assert not (tmp_path / "backups" / "must_not_exist").exists()


def test_restore_backup_stops_when_pending_widget_flush_fails(tmp_path, monkeypatch):
    settings_path = tmp_path / "widget_settings.json"
    original = {"position": {"x": 3, "y": 4}}
    settings_path.write_text(json.dumps(original), encoding="utf-8")
    backup_name = "must_not_restore"
    backup_path = tmp_path / "backups" / backup_name
    backup_path.mkdir(parents=True)
    backup_settings = {"position": {"x": 5, "y": 6}}
    (backup_path / "widget_settings.json").write_text(
        json.dumps(backup_settings),
        encoding="utf-8",
    )
    manager = SettingsManager.get_instance()
    manager.save_widget_position(1110, 1220, 1500, 1300)

    monkeypatch.setattr(
        manager,
        "_write_widget_settings_atomically",
        lambda snapshot: (_ for _ in ()).throw(OSError("simulated write failure")),
    )
    success, message = manager.restore_backup(backup_name)

    assert success is False
    assert "위젯 설정" in message
    assert manager._pending_widget_settings is not None
    assert json.loads(settings_path.read_text(encoding="utf-8")) == original
    assert json.loads(
        (backup_path / "widget_settings.json").read_text(encoding="utf-8")
    ) == backup_settings

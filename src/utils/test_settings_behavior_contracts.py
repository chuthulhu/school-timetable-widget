"""M2 legacy settings behavior characterization, not .NET bug requirements.

Real Qt controls/Widget and TEMP JSON; native X, IME and Windows pixel metrics
are separate evidence in docs/SETTINGS-BEHAVIOR-SPEC.md. OS effects are stubbed.
"""

import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest
from PyQt5 import QtCore, QtGui, QtWidgets, QtTest

from gui import widget as widget_module
from gui.dialogs.settings_dialog import SettingsDialog
from notifications.notification_manager import NotificationManager
from utils import auto_start
from utils.settings_manager import SettingsManager


@pytest.fixture
def scene(tmp_path, monkeypatch):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    monkeypatch.setenv("SCHOOL_TIMETABLE_DATA_DIR", str(tmp_path))
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    monkeypatch.setattr(SettingsManager, "_instance", None)
    monkeypatch.setattr(NotificationManager, "_instance", None)
    monkeypatch.setattr(auto_start, "enable_auto_start", lambda **kw: True)
    monkeypatch.setattr(auto_start, "disable_auto_start", lambda **kw: True)
    monkeypatch.setattr(NotificationManager, "check_notifications", lambda *a: None)
    real_time = QtCore.QTime

    class Clock(real_time):
        @staticmethod
        def currentTime():
            return real_time(8, 10)

    monkeypatch.setattr(QtCore, "QTime", Clock)
    monkeypatch.setattr(widget_module, "datetime", SimpleNamespace(
        datetime=SimpleNamespace(now=lambda: datetime.datetime(2026, 9, 7))))
    sm = SettingsManager.get_instance()
    # Use a font actually present in this Qt font database, without changing
    # QApplication font/style. Missing Korean font fallback is separate evidence.
    combo = QtWidgets.QFontComboBox()
    family = combo.currentFont().family()
    combo.deleteLater()
    sm.header_font_family = sm.cell_font_family = sm.font_family = family
    sm.header_font_size, sm.cell_font_size, sm.font_size = 11, 10, 11
    sm.widget_size = {"width": 550, "height": 520}
    sm.widget_position = {"x": 200, "y": 180}
    sm.timetable_data = {"월": {str(i): "Physics\nLab A" for i in range(1, 8)}}
    sm.save_style_settings()
    sm.save_widget_position(200, 180, 550, 520)
    sm.flush_pending_widget_settings()
    nm = NotificationManager.get_instance()
    nm.save_notification_settings()
    w = widget_module.Widget(sm, nm)
    w.show()  # Offscreen only: realize layout and settle owned geometry timers.
    QtTest.QTest.qWait(350)
    w.timer.stop()
    dialogs = []

    def open_dialog():
        d = SettingsDialog(w)
        d.settings_applied.connect(w.update_styles)
        d.show()
        dialogs.append(d)
        return d

    yield SimpleNamespace(sm=sm, nm=nm, w=w, open=open_dialog, path=tmp_path)
    for d in dialogs:
        d.hide()
        d.deleteLater()
    for timer in w.findChildren(QtCore.QTimer):
        timer.stop()
    w.timer.stop()
    w.hide()
    w.deleteLater()  # Avoid application-wide closeEvent/quit.
    sm._widget_settings_save_timer.stop()
    sm._widget_settings_save_timer.deleteLater()
    QtCore.QCoreApplication.sendPostedEvents(None, QtCore.QEvent.DeferredDelete)
    # monkeypatch restores singleton references, environment and process clock.


def disk(scene, name="style_settings.json"):
    return json.loads((scene.path / name).read_text(encoding="utf-8"))


def assert_font(scene, d, size):
    assert scene.sm.cell_font_size == d.cell_font_size.value() == size
    assert f"font-size: {size}pt" in scene.w.cell_widgets[(1, 1)].styleSheet()


def choose_color(monkeypatch, button, rgba=(18, 52, 86, 255)):
    # Exercise the real ColorButton accepted-result path, not a native picker.
    def accepted(picker):
        picker.setCurrentColor(QtGui.QColor(*rgba))
        return QtWidgets.QDialog.Accepted
    monkeypatch.setattr(QtWidgets.QColorDialog, "exec_", accepted)
    button.click()


@pytest.mark.parametrize("setting", ["font", "color"])
def test_normal_appearance_preview_changes_widget_without_persisting(scene, monkeypatch, setting):
    d = scene.open()
    before = disk(scene)
    if setting == "font":
        d.cell_font_size.setValue(24)
        assert_font(scene, d, 24)
    else:
        choose_color(monkeypatch, d.cell_bg_btn)
        assert scene.sm.cell_bg_color == "#123456"
        assert "rgba(18, 52, 86," in scene.w.cell_widgets[(1, 1)].styleSheet()
    assert disk(scene) == before


@pytest.mark.parametrize("action", ["cancel", "close"])
def test_legacy_font_preview_reject_restores_baseline_without_save(scene, action):
    d = scene.open()
    before = disk(scene)
    d.cell_font_size.setValue(24)
    assert_font(scene, d, 24)
    d.cancel_btn.click() if action == "cancel" else d.close()
    assert not d.isVisible()
    assert d.result() == QtWidgets.QDialog.Rejected
    assert_font(scene, d, 10)
    assert disk(scene) == before


@pytest.mark.parametrize("additional_preview", [False, True])
def test_legacy_apply_does_not_refresh_cancel_rollback_baseline(scene, additional_preview):
    d = scene.open()
    d.cell_font_size.setValue(18)
    d.apply_btn.click()
    assert d.isVisible()
    assert_font(scene, d, 18)
    assert disk(scene)["cell_font_size"] == 18
    if additional_preview:
        d.cell_font_size.setValue(24)
    d.reject()  # Qt reject, NOT a native title-bar click.
    assert_font(scene, d, 10)
    assert disk(scene)["cell_font_size"] == 18
    reopened = scene.open()
    assert_font(scene, reopened, 10)  # Reopen reads memory, not disk.


def test_ok_persists_and_closes_accepted(scene):
    d = scene.open()
    d.cell_font_size.setValue(18)
    d.ok_btn.click()
    assert not d.isVisible()
    assert d.result() == QtWidgets.QDialog.Accepted
    assert disk(scene)["cell_font_size"] == 18
    assert_font(scene, d, 18)


def test_legacy_theme_immediately_saves_whole_style_despite_cancel(scene):
    d = scene.open()
    d.cell_font_size.setValue(18)
    d.apply_btn.click()
    d.reject()
    d = scene.open()
    assert disk(scene)["cell_font_size"] == 18
    assert_font(scene, d, 10)
    d.theme_selector.select_theme("dark")  # No Apply after theme selection.
    saved = disk(scene)
    assert saved["theme"] == scene.sm.theme == "dark"
    assert saved["cell_font_size"] == 10
    assert "rgba(57, 57, 84," in scene.w.cell_widgets[(1, 1)].styleSheet()
    d.reject()
    assert scene.sm.theme == "light"
    assert disk(scene) == saved


def test_legacy_opacity_rollback_signal_reentry_retains_preview_values(scene):
    d = scene.open()
    before = disk(scene)
    for name in ("header", "cell", "current_period", "border"):
        getattr(d, name + "_opacity_slider").setValue(50)
    assert [getattr(scene.sm, n + "_opacity") for n in
            ("header", "cell", "current_period", "border")] == [127] * 4
    d.reject()
    assert [getattr(scene.sm, n + "_opacity") for n in
            ("header", "cell", "current_period", "border")] == [119, 124, 124, 124]
    assert disk(scene) == before


def test_legacy_color_picker_alpha_is_lost_in_persisted_rgb(scene, monkeypatch):
    d = scene.open()
    choose_color(monkeypatch, d.cell_bg_btn, (18, 52, 86, 50))
    assert d.cell_bg_btn.color == scene.sm.cell_bg_color == "#123456"
    d.apply_btn.click()
    assert disk(scene)["cell_bg_color"] == "#123456"


def test_constrained_size_apply_and_reopened_settings_show_settled_actual(scene):
    d = scene.open()
    before = QtCore.QSize(scene.w.size())
    d.widget_height.setValue(150)
    assert scene.w.size() == before  # Only the dialog's size preview changes.
    d.apply_btn.click()
    QtTest.QTest.qWait(350)
    scene.sm.flush_pending_widget_settings()
    actual = scene.w.size()
    assert actual.height() > 150
    assert disk(scene, "widget_settings.json")["size"] == {
        "width": actual.width(), "height": actual.height()}
    assert d.widget_height.value() == 150  # Existing dialog is stale.
    d.reject()
    reopened = scene.open()
    assert reopened.widget_height.value() == actual.height()
    assert reopened.widget_width.value() == actual.width()


def test_restart_process_loads_persisted_apply_after_runtime_reject(scene, monkeypatch):
    d = scene.open()
    d.cell_font_size.setValue(18)
    d.apply_btn.click()
    d.reject()
    assert_font(scene, d, 10)
    monkeypatch.setenv("PYTHONPATH", str(Path(__file__).resolve().parents[1]))
    code = (
        "import json; from PyQt5.QtCore import QCoreApplication; "
        "from utils.settings_manager import SettingsManager; "
        "app=QCoreApplication([]); sm=SettingsManager.get_instance(); "
        "print(json.dumps({'font':sm.cell_font_size,'theme':sm.theme})); "
        "sm._widget_settings_save_timer.stop()"
    )
    result = subprocess.run([sys.executable, "-B", "-c", code],
                            capture_output=True, text=True, timeout=30,
                            env=os.environ.copy(), check=True)
    assert json.loads(result.stdout) == {"font": 18, "theme": "light"}


def test_legacy_position_reset_does_not_move_or_rollback_but_apply_persists(scene, monkeypatch):
    d = scene.open()
    before = disk(scene, "widget_settings.json")
    position = QtCore.QPoint(scene.w.pos())
    monkeypatch.setattr(QtWidgets.QMessageBox, "exec_", lambda self: QtWidgets.QMessageBox.Yes)
    monkeypatch.setattr(QtWidgets.QMessageBox, "information", lambda *a: QtWidgets.QMessageBox.Ok)
    d.reset_widget_position()
    assert scene.sm.widget_position == {"x": 100, "y": 100}
    assert scene.w.pos() == position
    assert disk(scene, "widget_settings.json") == before
    d.reject()
    assert scene.sm.widget_position == {"x": 100, "y": 100}
    d = scene.open()
    d.apply_btn.click()
    scene.sm.flush_pending_widget_settings()
    assert disk(scene, "widget_settings.json")["position"] == {"x": 100, "y": 100}
    assert scene.w.pos() == position


def test_legacy_font_preview_increases_layout_requirement_without_resize(scene):
    d = scene.open()
    before_size = QtCore.QSize(scene.w.size())
    before_hfw = scene.w.layout().heightForWidth(scene.w.width())
    d.cell_font_size.setValue(24)
    QtTest.QTest.qWait(50)
    assert scene.w.layout().heightForWidth(scene.w.width()) > before_hfw
    assert scene.w.size() == before_size

"""M3 legacy characterization, NOT .NET bug-compatibility requirements.

TEMP JSON, real offscreen Qt objects, deterministic owned-timer callbacks and
subprocess reload. No native input, camera, QR image decoding or OS effects.
Existing seven backup/flush/naming contracts remain in test_v101_recovery_contracts.
"""

import base64
import datetime
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from types import ModuleType, SimpleNamespace

import pytest
from PyQt5 import QtCore, QtGui, QtWidgets

from gui import widget as widget_module
from gui.dialogs.backup_dialog import BackupRestoreDialog
from gui.dialogs.settings_dialog import SettingsDialog
from gui.dialogs.time_dialog import TimeRangeDialog
from gui.dialogs.timetable_dialog import TimetableEditDialog
from notifications.notification_manager import NotificationManager
from utils import auto_start
from utils.exceptions import DataError
from utils.settings_manager import SettingsManager


FILES = ("widget_settings.json", "style_settings.json", "timetable_data.json",
         "time_settings.json", "notification_settings.json")
HOURS = (9, 10, 11, 12, 14, 15, 16)


def profile(tag, family):
    """Independent non-identifying inputs, not production-generated expectations."""
    a = tag == "A"
    return {
        "widget_settings.json": {
            "position": {"x": 30 if a else 60, "y": 30 if a else 60},
            "size": {"width": 600 if a else 700, "height": 550 if a else 600},
            "is_position_locked": a, "screen_info": None, "auto_start_enabled": False,
        },
        "style_settings.json": {
            "theme": "light" if a else "dark",
            "font_family": family, "font_size": 10 if a else 12,
            "header_font_family": family, "header_font_size": 10 if a else 12,
            "cell_font_family": family, "cell_font_size": 10 if a else 12,
            "header_bg_color": "#FFFFFF" if a else "#222222",
            "header_text_color": "#000000" if a else "#FFFFFF",
            "cell_bg_color": "#EEEEEE" if a else "#333333",
            "cell_text_color": "#000000" if a else "#FFFFFF",
            "current_period_color": "#FFD700" if a else "#FFB400",
            "border_color": "#000000" if a else "#CCCCCC",
            "header_opacity": 180, "cell_opacity": 120,
            "current_period_opacity": 150, "border_opacity": 200,
        },
        "timetable_data.json": {"월": {"1": "PROFILE-" + tag}},
        "time_settings.json": {
            str(i): {"start": f"{8 if a and i == 1 else h:02d}:00",
                     "end": f"{8 if a and i == 1 else h:02d}:50"}
            for i, h in enumerate(HOURS, 1)
        },
        "notification_settings.json": {
            "notification_enabled": a, "next_period_warning": a,
            "warning_minutes": 3 if a else 9,
        },
    }


def write_files(path, data):
    path.mkdir(parents=True, exist_ok=True)
    for name, value in data.items():
        (path / name).write_text(json.dumps(value, ensure_ascii=False, indent=2),
                                 encoding="utf-8")


def read(path, name):
    return json.loads((path / name).read_text(encoding="utf-8"))


def file_bytes(path):
    return {name: (path / name).read_bytes() for name in FILES}


def settle_widget(w):
    """Dispatch owned callbacks explicitly; no 40/250ms wall-clock assumption."""
    for _ in range(5):
        QtCore.QCoreApplication.processEvents()
        if not w._dpi_transition_pending:
            break
        w._dpi_correction_timer.stop()
        w._dpi_correction_timer.timeout.emit()
    assert not w._dpi_transition_pending
    w.timer.stop()


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
    messages = []
    for method in ("information", "warning", "critical"):
        monkeypatch.setattr(QtWidgets.QMessageBox, method,
                            lambda *a, method=method: messages.append((method, a[1:])))
    monkeypatch.setattr(QtWidgets.QMessageBox, "question",
                        lambda *a: QtWidgets.QMessageBox.Yes)
    combo = QtWidgets.QFontComboBox()
    family = combo.currentFont().family()
    combo.deleteLater()
    a, b = profile("A", family), profile("B", family)
    write_files(tmp_path, a)
    sm = SettingsManager.get_instance()
    nm = NotificationManager.get_instance()
    managers, widgets, dialogs = [sm], [], []

    def make_widget():
        w = widget_module.Widget(sm, nm)
        widgets.append(w)
        w.show()  # Offscreen layout realization; production window flags retained.
        settle_widget(w)
        return w

    def dialog(cls, w):
        d = cls(w)
        dialogs.append(d)
        return d

    def fresh_manager():
        monkeypatch.setattr(SettingsManager, "_instance", None)
        fresh = SettingsManager.get_instance()
        managers.append(fresh)
        return fresh

    yield SimpleNamespace(path=tmp_path, sm=sm, nm=nm, a=a, b=b, app=app,
                          widget=make_widget, dialog=dialog, fresh=fresh_manager,
                          messages=messages)
    # Do not call closeEvent/quit on the shared QApplication or commit stale data.
    for d in dialogs:
        for timer in d.findChildren(QtCore.QTimer):
            timer.stop()
        if hasattr(d, "timer"):
            d.timer.stop()
        d.hide()
        d.deleteLater()
    for w in widgets:
        for timer in w.findChildren(QtCore.QTimer):
            timer.stop()
        w.timer.stop()
        w._disconnect_screen_signals()
        w.hide()
        w.deleteLater()
    for manager in managers:
        manager._widget_settings_save_timer.stop()
        manager._widget_settings_save_timer.deleteLater()
    QtCore.QCoreApplication.sendPostedEvents(None, QtCore.QEvent.DeferredDelete)


def restore_ui(scene, w, name="A"):
    d = scene.dialog(BackupRestoreDialog, w)
    row = next(r for r in range(d.table.rowCount()) if d.table.item(r, 0).text() == name)
    d.table.selectRow(row)
    d.restore_selected()
    assert scene.messages[-1][0] == "information"


def roundtrip(scene):
    w = scene.widget()
    # Persist actual admissible A geometry, not a platform-dependent pixel target.
    w.save_widget_position()
    scene.sm.flush_pending_widget_settings()
    a_bytes = file_bytes(scene.path)
    a_size = QtCore.QSize(w.size())
    assert scene.sm.create_backup("A")[0]
    backup = scene.path / "backups" / "A"
    assert {p.name for p in backup.iterdir()} == set(FILES) | {"description.txt"}
    assert file_bytes(backup) == a_bytes
    write_files(scene.path, scene.b)
    scene.sm.load_all_settings()
    scene.nm.load_notification_settings()
    w.update_timetable_display()
    w.update_styles()
    w.update_current_period()
    w.apply_user_requested_size(a_size.width() + 80, a_size.height() + 40)
    settle_widget(w)
    scene.sm.flush_pending_widget_settings()
    assert all(file_bytes(scene.path)[name] != a_bytes[name] for name in FILES)
    assert w.cell_widgets[(1, 1)].text() == "PROFILE-B"
    assert scene.nm.warning_minutes == 9
    b_size, b_preferred = QtCore.QSize(w.size()), QtCore.QSizeF(w._design_preferred_size)
    assert b_size != a_size
    restore_ui(scene, w)
    return w, a_bytes, a_size, b_size, b_preferred


def test_full_profile_backup_restore_ui_has_deferred_geometry_and_notification(scene):
    w, expected, a_size, b_size, b_preferred = roundtrip(scene)
    assert file_bytes(scene.path) == expected
    assert scene.sm.widget_size == {"width": a_size.width(), "height": a_size.height()}
    assert scene.sm.theme == "light" and scene.sm.cell_font_size == 10
    assert w.cell_widgets[(1, 1)].text() == "PROFILE-A"
    assert "font-size: 10pt" in w.cell_widgets[(1, 1)].styleSheet()
    assert scene.sm.time_ranges[1]["start"] == QtCore.QTime(8, 0)
    assert w.current_period == 1
    assert w.size() == b_size and w._design_preferred_size == b_preferred
    assert scene.nm.warning_minutes == 9
    assert read(scene.path, "notification_settings.json")["warning_minutes"] == 3


def test_restart_process_loads_all_restored_profile_classes(scene):
    w, expected, _, _, _ = roundtrip(scene)
    # Safe persistence portion of normal cleanup; no main/tray/OS startup.
    w.finalize_pending_user_save()
    scene.sm.flush_pending_widget_settings()
    assert file_bytes(scene.path) == expected
    code = """
import json
from PyQt5.QtCore import QCoreApplication
from utils.settings_manager import SettingsManager
from notifications.notification_manager import NotificationManager
from utils.paths import get_style_settings_file_path
app = QCoreApplication([])
sm = SettingsManager.get_instance()
nm = NotificationManager.get_instance()
with open(get_style_settings_file_path(), encoding='utf-8') as source:
    style_keys = json.load(source)
print(json.dumps({
    'widget': sm._create_widget_settings_snapshot(),
    'style': {k: getattr(sm, k) for k in style_keys},
    'timetable': sm.timetable_data,
    'time': {str(k): {n: t.toString('HH:mm') for n, t in v.items()} for k, v in sm.time_ranges.items()},
    'notification': {'notification_enabled': nm.notification_enabled,
                     'next_period_warning': nm.next_period_warning,
                     'warning_minutes': nm.warning_minutes}}))
sm._widget_settings_save_timer.stop()
"""
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1])
    result = subprocess.run([sys.executable, "-B", "-c", code], env=env,
                            capture_output=True, text=True, timeout=30, check=True)
    restored = json.loads(result.stdout)
    for key, name in zip(("widget", "style", "timetable", "time", "notification"), FILES):
        assert restored[key] == json.loads(expected[name])


def test_partial_backup_replaces_present_files_and_keeps_missing_files(scene):
    assert scene.sm.create_backup("A")[0]
    (scene.path / "backups/A/notification_settings.json").unlink()
    write_files(scene.path, scene.b)
    scene.sm.load_all_settings()
    scene.nm.load_notification_settings()
    sentinel = scene.path / "unrelated.txt"
    sentinel.write_text("B-only", encoding="utf-8")
    scene.b["timetable_data.json"]["B-only"] = {"1": "extra"}
    write_files(scene.path, {"timetable_data.json": scene.b["timetable_data.json"]})
    before_notification = (scene.path / "notification_settings.json").read_bytes()
    assert scene.sm.restore_backup("A")[0]
    for name in FILES[:-1]:
        assert (scene.path / name).read_bytes() == (scene.path / "backups/A" / name).read_bytes()
    assert (scene.path / "notification_settings.json").read_bytes() == before_notification
    assert "B-only" not in scene.sm.timetable_data
    assert sentinel.read_text(encoding="utf-8") == "B-only"


def test_legacy_partial_style_disk_replace_differs_from_runtime_and_fresh_load(scene):
    partial = {"cell_font_size": 18}
    write_files(scene.path / "backups/partial", {"style_settings.json": partial})
    scene.sm.theme = "dark"
    assert scene.sm.restore_backup("partial")[0]
    assert read(scene.path, "style_settings.json") == partial
    assert scene.sm.cell_font_size == 18 and scene.sm.theme == "dark"
    fresh = scene.fresh()
    assert fresh.cell_font_size == 18 and fresh.theme == "light"


def test_legacy_partial_time_keeps_runtime_extra_period_but_not_fresh_load(scene):
    partial = {"1": {"start": "07:30", "end": "08:20"}}
    write_files(scene.path / "backups/partial", {"time_settings.json": partial})
    scene.sm.time_ranges[9] = {"start": QtCore.QTime(19, 0), "end": QtCore.QTime(19, 50)}
    assert scene.sm.restore_backup("partial")[0]
    assert read(scene.path, "time_settings.json") == partial
    assert scene.sm.time_ranges[1]["start"] == QtCore.QTime(7, 30)
    assert 9 in scene.sm.time_ranges
    fresh = scene.fresh()
    assert 9 not in fresh.time_ranges
    assert fresh.time_ranges[1]["start"] == QtCore.QTime(7, 30)


def test_backup_snapshot_distinguishes_preview_theme_and_apply(scene):
    w = scene.widget()
    d = scene.dialog(SettingsDialog, w)
    d.settings_applied.connect(w.update_styles)
    d.cell_font_size.setValue(18)
    assert scene.sm.cell_font_size == 18
    assert scene.sm.create_backup("preview")[0]
    assert read(scene.path / "backups/preview", "style_settings.json")["cell_font_size"] == 10
    d.theme_selector.select_theme("dark")
    assert scene.sm.create_backup("theme")[0]
    themed = read(scene.path / "backups/theme", "style_settings.json")
    assert themed["theme"] == "dark" and themed["cell_font_size"] == 18
    d.cell_font_size.setValue(16)
    d.apply_btn.click()
    settle_widget(w)
    assert scene.sm.create_backup("applied")[0]
    assert read(scene.path / "backups/applied", "style_settings.json")["cell_font_size"] == 16


def test_backup_contains_committed_timetable_and_time_editor_values(scene):
    w = scene.widget()
    td = scene.dialog(TimetableEditDialog, w)
    td.table.setItem(0, 0, QtWidgets.QTableWidgetItem("SAVED-EDIT\n교실"))
    td.save_timetable()
    times = scene.dialog(TimeRangeDialog, w)
    times.time_widgets[1]["start"].setTime(QtCore.QTime(7, 15))
    times.save_time_ranges()
    assert scene.sm.create_backup("edit")[0]
    assert read(scene.path / "backups/edit", "timetable_data.json")["월"]["1"] == "SAVED-EDIT\n교실"
    assert read(scene.path / "backups/edit", "time_settings.json")["1"]["start"] == "07:15"


def test_legacy_characterization_widget_pending_can_overwrite_restored_geometry(scene):
    w = scene.widget()
    w.save_widget_position()
    scene.sm.flush_pending_widget_settings()
    assert scene.sm.create_backup("A")[0]
    a_file = (scene.path / "widget_settings.json").read_bytes()
    a_size = QtCore.QSize(w.size())
    local = QtCore.QPointF(w.width() - 5, w.height() - 5)
    global_pos = QtCore.QPointF(w.mapToGlobal(local.toPoint()))
    w.handle_mouse_press(QtGui.QMouseEvent(QtCore.QEvent.MouseButtonPress, local, global_pos,
                                         QtCore.Qt.LeftButton, QtCore.Qt.LeftButton, QtCore.Qt.NoModifier))
    delta = QtCore.QPointF(90, 40)
    w.handle_mouse_move(QtGui.QMouseEvent(QtCore.QEvent.MouseMove, local + delta, global_pos + delta,
                                        QtCore.Qt.NoButton, QtCore.Qt.LeftButton, QtCore.Qt.NoModifier))
    w.handle_mouse_release(QtGui.QMouseEvent(QtCore.QEvent.MouseButtonRelease, local, global_pos,
                                           QtCore.Qt.LeftButton, QtCore.Qt.NoButton, QtCore.Qt.NoModifier))
    assert w._save_after_dpi_transition and w._commit_user_resize
    assert scene.sm._pending_widget_settings is None
    assert scene.sm.create_backup("pre-manager")[0]
    assert (scene.path / "backups/pre-manager/widget_settings.json").read_bytes() == a_file
    assert scene.sm.restore_backup("A")[0]
    assert (scene.path / "widget_settings.json").read_bytes() == a_file
    # Advance the real Widget callback, then the real manager callback, without sleep.
    w._dpi_correction_timer.stop()
    w._dpi_correction_timer.timeout.emit()
    assert scene.sm._pending_widget_settings is not None
    scene.sm._widget_settings_save_timer.stop()
    scene.sm._widget_settings_save_timer.timeout.emit()
    assert w.width() > a_size.width() and w.height() > a_size.height()
    assert read(scene.path, "widget_settings.json")["size"] == {
        "width": w.width(), "height": w.height()}
    assert (scene.path / "widget_settings.json").read_bytes() != a_file


@pytest.mark.parametrize("kind,success", [("missing", False), ("empty", True), ("file", True)])
def test_legacy_backup_path_presence_does_not_validate_contents(scene, kind, success):
    before = file_bytes(scene.path)
    backup = scene.path / "backups/candidate"
    backup.parent.mkdir()
    if kind == "empty":
        backup.mkdir()
    elif kind == "file":
        backup.write_text("not a directory", encoding="utf-8")
    assert scene.sm.restore_backup("candidate")[0] is success
    assert file_bytes(scene.path) == before


def test_legacy_malformed_style_restore_copies_files_then_aborts_reload(scene):
    assert scene.sm.create_backup("bad")[0]
    backup = scene.path / "backups/bad"
    corrupt = b'{"theme": '
    (backup / "style_settings.json").write_bytes(corrupt)
    write_files(scene.path, scene.b)
    scene.sm.load_all_settings()
    assert not scene.sm.restore_backup("bad")[0]
    assert not (scene.path / "style_settings.json").exists()
    moved = list((scene.path / "backups").glob("style_settings_backup_style_settings.json_*"))
    assert len(moved) == 1 and moved[0].read_bytes() == corrupt
    assert read(scene.path, "timetable_data.json") == scene.a["timetable_data.json"]
    assert scene.sm.timetable_data == scene.b["timetable_data.json"]
    assert scene.sm.theme == "dark"  # The first loader stopped load_all_settings.


def test_legacy_malformed_style_startup_aborts_before_other_profile_loaders(scene, monkeypatch):
    (scene.path / "style_settings.json").write_text("{BAD", encoding="utf-8")
    original = file_bytes(scene.path)
    monkeypatch.setattr(SettingsManager, "_instance", None)
    reached = []
    monkeypatch.setattr(SettingsManager, "load_time_settings", lambda self: reached.append("time"))
    # Track the failed constructor's timer as well (no singleton owns it).
    timers = []
    real_timer = QtCore.QTimer

    def timer(*a, **kw):
        result = real_timer(*a, **kw)
        timers.append(result)
        return result

    monkeypatch.setattr(QtCore, "QTimer", timer)
    with pytest.raises(DataError):
        SettingsManager.get_instance()
    assert reached == [] and SettingsManager._instance is None
    for name in FILES:
        if name != "style_settings.json":
            assert (scene.path / name).read_bytes() == original[name]
    for item in timers:
        item.stop()
        item.deleteLater()


def test_legacy_malformed_timetable_restore_reports_success_with_empty_memory(scene):
    assert scene.sm.create_backup("bad")[0]
    corrupt = b'{"broken": '
    (scene.path / "backups/bad/timetable_data.json").write_bytes(corrupt)
    assert scene.sm.restore_backup("bad")[0]
    assert scene.sm.timetable_data == {}
    assert (scene.path / "timetable_data.json").read_bytes() == corrupt
    assert read(scene.path, "time_settings.json") == scene.a["time_settings.json"]


def fail_time_copy(monkeypatch):
    real_copy = shutil.copy2

    def copy(source, target, *a, **kw):
        if Path(source).name == "time_settings.json":
            raise OSError("injected second-file read/copy failure")
        return real_copy(source, target, *a, **kw)

    monkeypatch.setattr(shutil, "copy2", copy)


def test_legacy_backup_copy_failure_leaves_partial_folder(scene, monkeypatch):
    before = file_bytes(scene.path)
    fail_time_copy(monkeypatch)
    assert not scene.sm.create_backup("failed")[0]
    backup = scene.path / "backups/failed"
    assert {p.name for p in backup.iterdir()} == {"timetable_data.json"}
    assert (backup / "timetable_data.json").read_bytes() == before["timetable_data.json"]
    assert file_bytes(scene.path) == before


def test_legacy_restore_copy_failure_leaves_partial_disk_and_previous_memory(scene, monkeypatch):
    assert scene.sm.create_backup("A")[0]
    write_files(scene.path, scene.b)
    scene.sm.load_all_settings()
    before = file_bytes(scene.path)
    fail_time_copy(monkeypatch)
    assert not scene.sm.restore_backup("A")[0]
    assert read(scene.path, "timetable_data.json") == scene.a["timetable_data.json"]
    for name in FILES:
        if name != "timetable_data.json":
            assert (scene.path / name).read_bytes() == before[name]
    assert scene.sm.timetable_data == scene.b["timetable_data.json"]
    assert scene.sm.theme == "dark"


def test_legacy_duplicate_backup_name_retains_old_file_missing_from_current_profile(scene):
    assert scene.sm.create_backup("same")[0]
    backup = scene.path / "backups/same"
    old_notification = (backup / "notification_settings.json").read_bytes()
    (scene.path / "notification_settings.json").unlink()
    scene.sm.update_timetable_data(scene.b["timetable_data.json"])
    assert scene.sm.create_backup("same")[0]
    assert read(backup, "timetable_data.json") == scene.b["timetable_data.json"]
    assert (backup / "notification_settings.json").read_bytes() == old_notification


@pytest.fixture
def sharing(monkeypatch):
    """Load unchanged modules privately, stubbing ONLY unused image dependencies.

    No optional-package installation, skip or canonical module-cache pollution.
    Payload methods run unchanged; encoder/image/camera behavior is not tested.
    """
    numpy = ModuleType("numpy")
    pillow = ModuleType("PIL")
    pillow.Image = ModuleType("PIL.Image")
    qr = ModuleType("qrcode")
    captured = []

    class PayloadCaptured(Exception):
        pass

    class Encoder:
        def __init__(self, **kw):
            pass

        def add_data(self, value):
            captured.append(value)
            raise PayloadCaptured("Stopped at QR encoder boundary; no image test")

    qr.QRCode = Encoder
    qr.constants = SimpleNamespace(ERROR_CORRECT_M=0)
    modules = []
    with monkeypatch.context() as imports:
        for name, module in (("numpy", numpy), ("PIL", pillow), ("qrcode", qr)):
            imports.setitem(sys.modules, name, module)
        for name in ("import_dialog", "qr_share_dialog"):
            path = Path(__file__).resolve().parents[1] / "gui/dialogs" / (name + ".py")
            spec = importlib.util.spec_from_file_location("_m3_" + name, path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            modules.append(module)
    return SimpleNamespace(ImportDialog=modules[0].ImportDialog,
                           QRShareDialog=modules[1].QRShareDialog, captured=captured)


def import_selection(monkeypatch, timetable=True, time=True):
    def accept(d):
        for box in d.findChildren(QtWidgets.QCheckBox):
            box.setChecked(timetable if box.text() == "시간표 데이터" else time)
        return QtWidgets.QDialog.Accepted
    monkeypatch.setattr(QtWidgets.QDialog, "exec_", accept)


def test_sharing_production_envelope_serializes_decodes_and_imports(scene, sharing, monkeypatch):
    w = scene.widget()
    # Invoke production serializer without scheduling the dialog's image timer.
    producer = SimpleNamespace(settings_manager=scene.sm,
                               share_timetable=SimpleNamespace(isChecked=lambda: True),
                               share_time_settings=SimpleNamespace(isChecked=lambda: True))
    sharing.QRShareDialog.generate_qr_code(producer)
    assert len(sharing.captured) == 1
    encoded = sharing.captured[0]
    envelope = {"timetable": scene.a["timetable_data.json"],
                "time_settings": scene.a["time_settings.json"]}
    assert json.loads(base64.b64decode(encoded).decode("utf-8")) == envelope
    write_files(scene.path, scene.b)
    scene.sm.load_all_settings()
    before = file_bytes(scene.path)
    d = scene.dialog(sharing.ImportDialog, w)
    d.process_qr_data(encoded.encode("ascii"))
    assert d.imported_data == envelope and d.import_btn.isEnabled()
    import_selection(monkeypatch)
    d.apply_imported_data()
    assert read(scene.path, "timetable_data.json") == envelope["timetable"]
    assert read(scene.path, "time_settings.json") == envelope["time_settings"]
    assert w.cell_widgets[(1, 1)].text() == "PROFILE-A"
    for name in ("style_settings.json", "widget_settings.json", "notification_settings.json"):
        assert (scene.path / name).read_bytes() == before[name]


@pytest.mark.parametrize("select_timetable", [True, False])
def test_json_import_selection_replaces_timetable_or_merges_time(scene, sharing, monkeypatch, select_timetable):
    w = scene.widget()
    d = scene.dialog(sharing.ImportDialog, w)
    payload = {"timetable": {"화": {"2": "가져오기\n실험"}},
               "time_settings": {"1": {"start": "07:15", "end": "08:00"}}}
    source = scene.path / "sharing.json"
    source.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(QtWidgets.QFileDialog, "getOpenFileName", lambda *a: (str(source), ""))
    d.open_json_file()
    assert d.imported_data == payload
    before = file_bytes(scene.path)
    import_selection(monkeypatch, timetable=select_timetable, time=not select_timetable)
    d.apply_imported_data()
    changed = "timetable_data.json" if select_timetable else "time_settings.json"
    assert {n for n in FILES if (scene.path / n).read_bytes() != before[n]} == {changed}
    if select_timetable:
        assert scene.sm.timetable_data == payload["timetable"]
        assert read(scene.path, changed) == payload["timetable"]
        assert w.cell_widgets[(1, 1)].text() == ""
        assert w.cell_widgets[(2, 2)].text() == "가져오기\n실험"
    else:
        expected = {**scene.a["time_settings.json"], **payload["time_settings"]}
        assert read(scene.path, changed) == expected
        assert scene.sm.time_ranges[1]["start"] == QtCore.QTime(7, 15)


def test_legacy_import_time_failure_leaves_timetable_committed_without_refresh(scene, sharing, monkeypatch):
    w = scene.widget()
    d = scene.dialog(sharing.ImportDialog, w)
    data = {"월": {"1": "PARTIAL-IMPORT"}}
    d.imported_data = {"timetable": data,
                       "time_settings": {"1": {"start": "bad", "end": "08:00"}}}
    before = (scene.path / "time_settings.json").read_bytes()
    import_selection(monkeypatch)
    with pytest.raises(ValueError):
        d.apply_imported_data()
    assert read(scene.path, "timetable_data.json") == scene.sm.timetable_data == data
    assert (scene.path / "time_settings.json").read_bytes() == before
    assert w.cell_widgets[(1, 1)].text() == "PROFILE-A"
    assert not any(kind == "information" for kind, _ in scene.messages)


def test_legacy_json_parse_failure_retains_previous_payload_and_apply_state(scene, sharing, monkeypatch):
    w = scene.widget()
    d = scene.dialog(sharing.ImportDialog, w)
    source = scene.path / "sharing.json"
    previous = {"timetable": {"월": {"1": "PREVIOUS-IMPORT"}}}
    source.write_text(json.dumps(previous), encoding="utf-8")
    monkeypatch.setattr(QtWidgets.QFileDialog, "getOpenFileName", lambda *a: (str(source), ""))
    d.open_json_file()
    source.write_text("{BAD", encoding="utf-8")
    d.open_json_file()
    assert d.imported_data == previous and d.import_btn.isEnabled()
    assert "오류" in d.result_text.toPlainText()
    import_selection(monkeypatch, timetable=True, time=False)
    d.apply_imported_data()
    assert read(scene.path, "timetable_data.json") == previous["timetable"]

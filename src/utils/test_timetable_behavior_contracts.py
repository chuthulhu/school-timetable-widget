"""M1 legacy behavior characterization, not .NET bug-compatibility requirements.

Real Qt objects run offscreen with isolated files and a process-local clock.
IME, native title-bar X and native typing/rendering evidence live in
docs/TIMETABLE-BEHAVIOR-SPEC.md; these tests do not impersonate those checks.
"""

import datetime
import json
import os
from types import SimpleNamespace

import pytest
from PyQt5 import QtCore, QtWidgets

from gui import widget as widget_module
from gui.dialogs.time_dialog import TimeRangeDialog
from gui.dialogs.timetable_dialog import TimetableEditDialog
from utils.settings_manager import SettingsManager


# Independent reference profile: do not derive expected values from production.
HOURS = (9, 10, 11, 12, 14, 15, 16)
DAYS = ("월", "화", "수", "목", "금")


@pytest.fixture(scope="module")
def qapp():
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    yield app


@pytest.fixture
def manager(tmp_path, monkeypatch, qapp):
    monkeypatch.setenv("SCHOOL_TIMETABLE_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(SettingsManager, "_instance", None)
    sm = SettingsManager.get_instance()
    yield sm
    sm._widget_settings_save_timer.stop()
    SettingsManager._instance = None


@pytest.fixture
def clock(monkeypatch):
    real_time = QtCore.QTime

    class Clock(real_time):
        value = real_time(8, 0)
        date = datetime.datetime(2026, 9, 7)

        @staticmethod
        def currentTime():
            return Clock.value

    monkeypatch.setattr(QtCore, "QTime", Clock)
    monkeypatch.setattr(widget_module, "datetime", SimpleNamespace(
        datetime=SimpleNamespace(now=lambda: Clock.date)))
    return Clock


@pytest.fixture
def widget(manager, clock, qapp):
    notification = SimpleNamespace(next_period_warning=True, warning_minutes=5,
                                   calls=[])
    notification.check_notifications = lambda *args: notification.calls.append(args[:2])
    w = widget_module.Widget(manager, notification)
    w.timer.stop()
    yield w
    # Cleanup without invoking application-wide quit/production exit handlers.
    for timer in w.findChildren(QtCore.QTimer):
        timer.stop()
    w.deleteLater()
    QtCore.QCoreApplication.sendPostedEvents(None, QtCore.QEvent.DeferredDelete)


def tick(widget, clock, hour, minute, second=0, day=7):
    clock.value = QtCore.QTime(hour, minute, second)
    clock.date = datetime.datetime(2026, 9, day)
    widget.update_current_period()
    widget.timer.stop()


def highlighted(widget):
    return {key for key, cell in widget.cell_widgets.items()
            if "font-weight: bold" in cell.styleSheet()}


def click_button(dialog, text):
    next(b for b in dialog.findChildren(QtWidgets.QPushButton)
         if b.text() == text).click()


def read_json(tmp_path, name):
    return json.loads((tmp_path / name).read_text(encoding="utf-8"))


@pytest.mark.parametrize("period,hour", list(enumerate(HOURS, 1)))
@pytest.mark.parametrize("minute,offset,inside", [
    (0, -1000, False), (0, 0, True), (0, 1000, True),
    (50, -1000, True), (50, 0, True), (50, 1000, False),
    (50, 1, False),
])
def test_current_period_exact_boundaries(manager, period, hour, minute, offset, inside):
    now = QtCore.QTime(hour, minute).addMSecs(offset)
    assert manager.get_current_period(now) == (period if inside else None)


@pytest.mark.parametrize("hour,minute", [(0, 0), (8, 59), (9, 55), (13, 0), (17, 0), (23, 59)])
def test_no_period_before_break_lunch_after(manager, hour, minute):
    assert manager.get_current_period(QtCore.QTime(hour, minute)) is None


@pytest.mark.parametrize("order,expected", [((2, 1), 2), ((1, 2), 1)])
@pytest.mark.parametrize("identical", [False, True])
def test_legacy_overlap_returns_first_dictionary_match(manager, order, expected, identical):
    ranges = {
        1: {"start": QtCore.QTime(9, 0), "end": QtCore.QTime(10, 30)},
        2: {"start": QtCore.QTime(9 if identical else 10, 0), "end": QtCore.QTime(10, 30)},
    }
    manager.time_ranges = {key: ranges[key] for key in order}
    assert manager.get_current_period(QtCore.QTime(10, 10)) == expected


def test_legacy_reversed_and_zero_duration_ranges(manager):
    manager.time_ranges = {1: {"start": QtCore.QTime(10, 0), "end": QtCore.QTime(9, 0)}}
    for now in (QtCore.QTime(9, 0), QtCore.QTime(9, 30), QtCore.QTime(10, 0)):
        assert manager.get_current_period(now) is None
    manager.time_ranges[1]["start"] = QtCore.QTime(9, 0)
    assert manager.get_current_period(QtCore.QTime(9, 0)) == 1
    assert manager.get_current_period(QtCore.QTime(9, 0).addMSecs(1)) is None


@pytest.mark.parametrize("day", range(7, 14))
def test_weekday_single_empty_cell_and_weekend_no_highlight(widget, clock, day):
    tick(widget, clock, 9, 10, day=day)
    assert widget.current_period == 1  # Calculation itself is date-independent.
    expected = {(1, day - 6)} if day <= 11 else set()
    assert highlighted(widget) == expected
    assert all(cell.text() == "" for cell in widget.cell_widgets.values())
    assert all("font-weight: bold" not in h.styleSheet()
               for h in (*widget.day_headers.values(), *widget.period_headers.values()))
    if expected:
        style = widget.cell_widgets[next(iter(expected))].styleSheet()
        assert "rgba(255, 215, 0, 0.5882352941176471)" in style
        assert "border: 2px solid" in style
    tick(widget, clock, 9, 55, day=day)
    assert widget.current_period is None
    assert highlighted(widget) == set()


def test_legacy_highlight_can_remain_when_only_weekday_changes(widget, clock):
    tick(widget, clock, 9, 10, day=11)
    tick(widget, clock, 9, 10, day=12)
    assert widget.current_day_idx is None
    assert highlighted(widget) == {(1, 5)}  # Observed bug, REDESIGN for .NET.
    tick(widget, clock, 9, 55, day=12)
    assert highlighted(widget) == set()


def test_midnight_then_next_morning_updates_day(widget, clock):
    tick(widget, clock, 23, 59, 59)
    tick(widget, clock, 0, 0, day=8)
    assert widget.current_day_idx == 2
    assert highlighted(widget) == set()
    tick(widget, clock, 9, 0, day=8)
    assert highlighted(widget) == {(1, 2)}


def test_legacy_break_scheduler_and_warning_callback_quirk(widget, clock):
    tick(widget, clock, 9, 0)
    tick(widget, clock, 9, 50, 1)
    widget.notification_manager.calls.clear()
    tick(widget, clock, 9, 55)
    assert widget.notification_manager.calls == []
    tick(widget, clock, 9, 59, 59)
    assert widget.timer.interval() == 60000  # Break schedules period 1, not period 2.


def test_timetable_save_preserves_content_and_reload(widget, manager, tmp_path):
    values = ("", "   ", "  국어  ", "물리학\n실험 A반!", "😀 & < >", "긴글" * 1000, "마지막")
    manager.timetable_data = {"extra": {"9": "not in editor"}}
    dialog = TimetableEditDialog(widget)
    assert dialog.table.selectionMode() == QtWidgets.QAbstractItemView.ContiguousSelection
    for row, value in enumerate(values):
        index = dialog.table.model().index(row, 0)
        delegate = dialog.table.itemDelegate()
        editor = delegate.createEditor(dialog.table, None, index)
        assert isinstance(editor, QtWidgets.QTextEdit)
        assert not editor.acceptRichText()
        editor.setPlainText(value)
        delegate.setModelData(editor, dialog.table.model(), index)
    click_button(dialog, "저장")
    expected = {day: {str(p): values[p - 1] if day == "월" else "" for p in range(1, 8)} for day in DAYS}
    assert dialog.result() == QtWidgets.QDialog.Accepted
    assert manager.timetable_data == expected
    assert read_json(tmp_path, "timetable_data.json") == expected
    assert [widget.cell_widgets[(p, 1)].text() for p in range(1, 8)] == list(values)
    SettingsManager._instance = None
    reloaded = SettingsManager.get_instance()
    assert reloaded.timetable_data == expected
    reopened = TimetableEditDialog(widget)
    assert [reopened.table.item(p, 0).text() for p in range(7)] == list(values)


@pytest.mark.parametrize("action", ["cancel", "close"])
def test_timetable_discard_keeps_memory_widget_and_file(widget, manager, tmp_path, action):
    manager.update_timetable_data({"월": {"1": "original"}})
    widget.update_timetable_display()
    path = tmp_path / "timetable_data.json"
    before, mtime = path.read_bytes(), path.stat().st_mtime_ns
    dialog = TimetableEditDialog(widget)
    dialog.table.item(0, 0).setText("discard\n변경")
    click_button(dialog, "취소") if action == "cancel" else dialog.close()
    assert dialog.result() == QtWidgets.QDialog.Rejected
    assert path.read_bytes() == before and path.stat().st_mtime_ns == mtime
    assert manager.timetable_data == {"월": {"1": "original"}}
    assert widget.cell_widgets[(1, 1)].text() == "original"
    assert TimetableEditDialog(widget).table.item(0, 0).text() == "original"


@pytest.mark.parametrize("action", ["save", "cancel", "close"])
def test_period_edit_persistence(widget, manager, tmp_path, action):
    manager.save_time_settings()
    path = tmp_path / "time_settings.json"
    before, mtime = path.read_bytes(), path.stat().st_mtime_ns
    dialog = TimeRangeDialog(widget)
    dialog.time_widgets[1]["start"].setTime(QtCore.QTime(8, 0))
    dialog.time_widgets[1]["end"].setTime(QtCore.QTime(8, 50))
    if action == "close":
        dialog.close()
    else:
        click_button(dialog, "저장" if action == "save" else "취소")
    hour = 8 if action == "save" else 9
    assert manager.time_ranges[1]["start"] == QtCore.QTime(hour, 0)
    assert read_json(tmp_path, "time_settings.json")["1"] == {"start": f"{hour:02}:00", "end": f"{hour:02}:50"}
    if action != "save":
        assert path.read_bytes() == before and path.stat().st_mtime_ns == mtime
    SettingsManager._instance = None
    assert SettingsManager.get_instance().time_ranges[1]["start"] == QtCore.QTime(hour, 0)


def test_time_dialog_accepted_path_recalculates_immediately(widget, clock, monkeypatch):
    tick(widget, clock, 8, 30)
    assert widget.current_period is None

    def save_interaction(dialog):
        dialog.time_widgets[1]["start"].setTime(QtCore.QTime(8, 0))
        dialog.time_widgets[1]["end"].setTime(QtCore.QTime(8, 50))
        click_button(dialog, "저장")
        return dialog.result()

    monkeypatch.setattr(TimeRangeDialog, "exec_", save_interaction)
    widget.show_time_dialog()  # Real production Accepted branch; no sleep/timer tick.
    assert widget.current_period == 1
    assert highlighted(widget) == {(1, 1)}


def test_legacy_auto_merge_save_overwrites_following_subject(widget, manager, tmp_path):
    manager.timetable_data = {"월": {"1": "A", "2": "A", "3": "B"}}
    dialog = TimetableEditDialog(widget)
    assert dialog.table.rowSpan(0, 0) == 2
    click_button(dialog, "저장")
    assert [read_json(tmp_path, "timetable_data.json")["월"][str(p)] for p in (1, 2, 3)] == ["A", "A", "A"]
    assert widget.cell_widgets[(3, 1)].text() == "A"


def test_legacy_manual_merge_overwrites_cell_outside_selection(widget, manager):
    manager.timetable_data = {"월": {"1": "A", "2": "B", "3": "C", "4": "D"}}
    dialog = TimetableEditDialog(widget)
    dialog.table.setRangeSelected(QtWidgets.QTableWidgetSelectionRange(0, 0, 1, 0), True)
    dialog.merge_selected_cells()
    click_button(dialog, "저장")
    assert [manager.timetable_data["월"][str(p)] for p in range(1, 5)] == ["A", "A", "A", "D"]


@pytest.mark.parametrize("start,span", [(6, 3), (1, 8)])
def test_legacy_final_span_is_oversized_and_split_raises(widget, manager, start, span):
    manager.timetable_data = {"월": {str(p): "A" for p in range(start, 8)}}
    dialog = TimetableEditDialog(widget)
    assert dialog.table.rowSpan(start - 1, 0) == span
    dialog.table.setCurrentCell(start - 1, 0)
    # Direct call catches the exception safely, outside Qt's signal dispatcher.
    with pytest.raises(AttributeError, match="setTextAlignment"):
        dialog.split_selected_cell()


def test_legacy_auto_merge_skips_second_block_after_empty_cell(widget, manager):
    manager.timetable_data = {"월": dict(zip(map(str, range(1, 8)), ["A", "A", "", "B", "B", "", ""]))}
    dialog = TimetableEditDialog(widget)
    assert dialog.table.rowSpan(0, 0) == 2
    assert dialog.table.rowSpan(3, 0) == 1
    assert dialog.table.rowSpan(4, 0) == 1


@pytest.mark.parametrize("raw,expected,error", [
    (None, {}, None), ("{}", {}, None), ("{", {}, None),
    ('{"월":{"1":"국어"}}', {"월": {"1": "국어"}}, None),
    ("[]", [], AttributeError), ('{"월":null}', {"월": None}, AttributeError),
    ('{"월":{"1":123}}', {"월": {"1": 123}}, TypeError),
])
def test_legacy_timetable_load_and_display_malformed_cases(widget, manager, tmp_path, caplog, raw, expected, error):
    if raw is not None:
        (tmp_path / "timetable_data.json").write_text(raw, encoding="utf-8")
    manager.load_timetable_data()
    assert manager.timetable_data == expected
    if raw == "{":
        assert "시간표 데이터 로드 오류" in caplog.text
    if error:
        with pytest.raises(error):
            widget.update_timetable_display()
    else:
        widget.update_timetable_display()
        assert widget.cell_widgets[(1, 1)].text() == expected.get("월", {}).get("1", "")
        assert widget.cell_widgets[(7, 5)].text() == ""


@pytest.mark.parametrize("raw", [None, "{}", "{"])
def test_time_missing_or_malformed_keeps_default_profile(manager, tmp_path, raw):
    if raw is not None:
        (tmp_path / "time_settings.json").write_text(raw, encoding="utf-8")
    manager.load_time_settings()
    assert [(r["start"].toString("HH:mm"), r["end"].toString("HH:mm"))
            for r in manager.time_ranges.values()] == [(f"{h:02}:00", f"{h:02}:50") for h in HOURS]


def test_legacy_time_partial_load_keeps_changes_before_missing_end(manager, tmp_path, caplog):
    data = {"1": {"start": "8:00", "end": "8:50"}, "2": {"start": "07:00"},
            "3": {"start": "06:00", "end": "06:50"}}
    (tmp_path / "time_settings.json").write_text(json.dumps(data), encoding="utf-8")
    manager.load_time_settings()
    assert manager.time_ranges[1]["start"] == QtCore.QTime(8, 0)
    assert manager.time_ranges[2]["start"] == QtCore.QTime(10, 0)
    assert manager.time_ranges[3]["start"] == QtCore.QTime(11, 0)
    assert "시간 설정 로드 오류" in caplog.text


def test_legacy_invalid_qtime_start_matches_before_class(manager, tmp_path):
    (tmp_path / "time_settings.json").write_text('{"1":{"start":"25:00","end":"09:50"}}', encoding="utf-8")
    manager.load_time_settings()
    assert not manager.time_ranges[1]["start"].isValid()
    assert manager.get_current_period(QtCore.QTime(0, 0)) == 1
    assert manager.get_current_period(QtCore.QTime(8, 0)) == 1


def test_legacy_current_period_highlight_border_increases_cell_hfw(widget, manager, clock):
    """Legacy visual/layout interaction; .NET REDESIGN, not MATCH."""
    import re

    manager.header_font_size = manager.cell_font_size = 13
    manager.header_font_family = manager.cell_font_family = "Arial"
    manager.timetable_data = {"월": {str(p): "x\nx" for p in range(1, 8)}}
    widget.update_timetable_display()
    screen = SimpleNamespace(logicalDotsPerInch=lambda: 120.0)
    cell = widget.cell_widgets[(1, 1)]

    def measure(hour):
        tick(widget, clock, hour, 10)
        widget.update_styles()
        # Model 125% font delivery using real QLabel layout, as in DPI contracts.
        for label in widget.findChildren(QtWidgets.QLabel):
            label.setStyleSheet(re.sub(r"font-size:\s*[\d.]+pt;", "font-size: 32px;", label.styleSheet()))
        widget.apply_minimum_cell_sizes(screen)
        widget.resize(590, 700)
        widget.layout().activate()
        margins = widget.layout().contentsMargins()
        return (cell.heightForWidth(cell.width()),
                widget.grid_layout.heightForWidth(590 - margins.left() - margins.right()),
                widget.layout().heightForWidth(590))

    normal = measure(8)
    assert highlighted(widget) == set()
    assert "border: 1px solid" in cell.styleSheet()
    active = measure(9)
    assert highlighted(widget) == {(1, 1)}
    assert "border: 2px solid" in cell.styleSheet()
    assert active == tuple(height + 2 for height in normal)
    assert measure(8) == normal

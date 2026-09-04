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
from types import SimpleNamespace

import pytest
from PyQt5 import QtCore, QtGui, QtTest, QtWidgets

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


class _SignalStub:
    def __init__(self):
        self.slots = []

    def connect(self, slot):
        self.slots.append(slot)

    def disconnect(self, slot):
        if slot not in self.slots:
            raise TypeError("slot is not connected")
        self.slots.remove(slot)

    def emit(self, *args):
        for slot in tuple(self.slots):
            slot(*args)


class _RuntimeScreenStub:
    def __init__(self, dpi, available=None):
        self.dpi = dpi
        self.logicalDotsPerInchChanged = _SignalStub()
        self._available = available or QtCore.QRect(0, 0, 1920, 1080)

    def logicalDotsPerInch(self):
        return self.dpi

    def availableGeometry(self):
        return self._available

    def set_dpi(self, dpi):
        self.dpi = dpi
        self.logicalDotsPerInchChanged.emit(dpi)


class _WindowHandleStub:
    def __init__(self, screen):
        self._screen = screen
        self.screenChanged = _SignalStub()

    def screen(self):
        return self._screen


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
    # Complete startup at the chosen screen's DPI before simulating runtime
    # transitions. Production normally schedules this from its first showEvent.
    widget._handle_screen_changed(_RuntimeScreenStub(96.0 * dpi_scale))
    _settle_events(QtWidgets.QApplication.instance())
    return widget


def _settle_events(application):
    # Exercise the real debounce and any superseding transition, not a direct
    # timeout call that bypasses font/style/layout delivery.
    QtTest.QTest.qWait(Widget.DPI_SETTLE_MS * 3 + 20)
    application.processEvents()


def _release_left_mouse(widget):
    QtWidgets.QApplication.sendEvent(
        widget,
        QtGui.QMouseEvent(
            QtCore.QEvent.MouseButtonRelease, QtCore.QPointF(1, 1),
            QtCore.Qt.LeftButton, QtCore.Qt.NoButton, QtCore.Qt.NoModifier,
        ),
    )


def _resize_widget_by_mouse(widget, width, height, release=True):
    """Exercise the production press/move/release path without OS mouse input."""
    start = QtCore.QPoint(widget.width() - 2, widget.height() - 2)
    global_start = widget.mapToGlobal(start)
    delta = QtCore.QPoint(width - widget.width(), height - widget.height())
    for event_type, local, global_pos, button in (
        (QtCore.QEvent.MouseButtonPress, start, global_start, QtCore.Qt.LeftButton),
        (QtCore.QEvent.MouseMove, start + delta, global_start + delta, QtCore.Qt.NoButton),
    ):
        QtWidgets.QApplication.sendEvent(
            widget,
            QtGui.QMouseEvent(
                event_type, QtCore.QPointF(local), QtCore.QPointF(global_pos),
                button, QtCore.Qt.LeftButton, QtCore.Qt.NoModifier,
            ),
        )
    if release:
        _release_left_mouse(widget)


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
    assert widget._design_preferred_size == QtCore.QSizeF(widget.size()) / 2.0
    assert widget.width() > manager.widget_size["width"]
    assert widget.height() > manager.widget_size["height"]

    widget.deleteLater()


def test_normal_saved_size_is_preserved(qapplication, monkeypatch):
    manager = SettingsManager.get_instance()
    manager.widget_size = {"width": 800, "height": 650}
    widget = _create_widget(monkeypatch, manager, dpi_scale=1.0)

    assert widget.size() == QtCore.QSize(800, 650)
    assert widget._design_preferred_size == QtCore.QSizeF(800, 650)

    widget.deleteLater()


def test_runtime_logical_dpi_change_recalculates_minimums(
    qapplication, monkeypatch
):
    manager = SettingsManager.get_instance()
    widget = _create_widget(monkeypatch, manager, dpi_scale=1.0)
    screen = _RuntimeScreenStub(96.0)
    widget._connect_dpi_screen(screen)
    old_cell_minimum = next(iter(widget.cell_widgets.values())).minimumSize()

    screen.set_dpi(144.0)
    _settle_events(qapplication)

    expected_width, expected_height = calculate_minimum_cell_size(
        manager.cell_font_size, 1.5
    )
    assert next(iter(widget.cell_widgets.values())).minimumSize() == QtCore.QSize(
        math.ceil(expected_width), math.ceil(expected_height)
    )
    assert next(iter(widget.cell_widgets.values())).minimumSize() != old_cell_minimum

    widget.deleteLater()


def test_show_connects_window_and_current_screen_signals(
    qapplication, monkeypatch
):
    manager = SettingsManager.get_instance()
    widget = _create_widget(monkeypatch, manager, dpi_scale=1.0)
    assert widget.windowHandle() is None

    widget.show()
    _settle_events(qapplication)

    window_handle = widget.windowHandle()
    assert window_handle is not None
    assert widget._screen_change_window is window_handle
    assert widget._dpi_screen is window_handle.screen()

    widget.hide()
    widget.deleteLater()


def test_runtime_dpi_change_scales_both_axes_of_a_sufficient_widget(
    qapplication, monkeypatch
):
    manager = SettingsManager.get_instance()
    manager.widget_size = {"width": 800, "height": 600}
    widget = _create_widget(monkeypatch, manager, dpi_scale=1.0)

    widget._handle_screen_changed(_RuntimeScreenStub(144.0))
    _settle_events(qapplication)

    assert widget.size() == QtCore.QSize(1200, 900)

    widget.deleteLater()


def test_runtime_dpi_scales_from_the_clamped_startup_size(
    qapplication, monkeypatch
):
    manager = SettingsManager.get_instance()
    manager.header_font_size = manager.cell_font_size = 10
    manager.widget_size = {"width": 500, "height": 1}
    widget = _create_widget(monkeypatch, manager, dpi_scale=1.0)
    assert widget.size() == QtCore.QSize(500, 300)

    widget._handle_screen_changed(_RuntimeScreenStub(144.0))
    _settle_events(qapplication)

    assert widget.size() == QtCore.QSize(750, 450)
    assert widget._design_preferred_size == QtCore.QSizeF(500, 300)

    widget.deleteLater()


def test_screen_change_uses_new_screen_and_disconnects_previous_dpi_signal(
    qapplication, monkeypatch
):
    manager = SettingsManager.get_instance()
    widget = _create_widget(monkeypatch, manager, dpi_scale=1.0)
    old_screen = _RuntimeScreenStub(96.0)
    new_screen = _RuntimeScreenStub(192.0)

    widget._handle_screen_changed(old_screen)
    widget._handle_screen_changed(new_screen)
    _settle_events(qapplication)

    expected_width, expected_height = calculate_minimum_cell_size(
        manager.cell_font_size, 2.0
    )
    assert next(iter(widget.cell_widgets.values())).minimumSize() == QtCore.QSize(
        math.ceil(expected_width), math.ceil(expected_height)
    )
    assert old_screen.logicalDotsPerInchChanged.slots == []
    assert new_screen.logicalDotsPerInchChanged.slots == [
        widget._handle_screen_dpi_changed
    ]

    old_screen.set_dpi(288.0)
    _settle_events(qapplication)
    assert next(iter(widget.cell_widgets.values())).minimumSize() == QtCore.QSize(
        math.ceil(expected_width), math.ceil(expected_height)
    )

    widget.deleteLater()


def test_repeated_screen_connection_and_dpi_event_do_not_rescale_applied_size(
    qapplication, monkeypatch
):
    manager = SettingsManager.get_instance()
    manager.widget_size = {"width": 800, "height": 600}
    widget = _create_widget(monkeypatch, manager, dpi_scale=1.0)
    screen = _RuntimeScreenStub(144.0)
    window_handle = _WindowHandleStub(screen)
    monkeypatch.setattr(widget, "windowHandle", lambda: window_handle)

    widget._connect_screen_signals()
    _settle_events(qapplication)
    size_after_first_event = widget.size()
    widget._connect_screen_signals()
    screen.logicalDotsPerInchChanged.emit(144.0)
    _settle_events(qapplication)

    assert window_handle.screenChanged.slots == [widget._handle_screen_changed]
    assert screen.logicalDotsPerInchChanged.slots == [
        widget._handle_screen_dpi_changed
    ]
    assert widget.size() == size_after_first_event == QtCore.QSize(1200, 900)

    widget.deleteLater()


def test_runtime_dpi_growth_stays_inside_available_screen_geometry(
    qapplication, monkeypatch
):
    manager = SettingsManager.get_instance()
    manager.widget_size = {"width": 500, "height": 1}
    widget = _create_widget(monkeypatch, manager, dpi_scale=1.0)
    widget.move(300, 250)
    screen = _RuntimeScreenStub(
        144.0,
        available=QtCore.QRect(0, 0, 900, 600),
    )

    widget._handle_screen_changed(screen)
    _settle_events(qapplication)

    available = screen.availableGeometry()
    assert widget.x() >= available.left()
    assert widget.y() >= available.top()
    assert widget.x() + widget.width() <= available.right() + 1
    assert widget.y() + widget.height() <= available.bottom() + 1

    widget.deleteLater()


def test_runtime_dpi_round_trip_does_not_accumulate_growth(
    qapplication, monkeypatch
):
    manager = SettingsManager.get_instance()
    manager.header_font_size = 10
    manager.cell_font_size = 10
    manager.widget_size = {
        "width": Config.DEFAULT_WINDOW_SIZE[0],
        "height": Config.DEFAULT_WINDOW_SIZE[1],
    }
    widget = _create_widget(monkeypatch, manager, dpi_scale=1.0)

    widget._handle_screen_changed(_RuntimeScreenStub(96.0))
    _settle_events(qapplication)
    starting_size = widget.size()

    widget._handle_screen_changed(_RuntimeScreenStub(144.0))
    _settle_events(qapplication)
    first_high_dpi_size = widget.size()
    expected_cell_minimum = QtCore.QSize(
        math.ceil(manager.cell_font_size * 3.0 * 1.5),
        math.ceil(manager.cell_font_size * 2.5 * 1.5),
    )
    assert next(iter(widget.cell_widgets.values())).minimumSize() == (
        expected_cell_minimum
    )
    assert starting_size == QtCore.QSize(400, 300)
    assert first_high_dpi_size == QtCore.QSize(600, 450)
    assert first_high_dpi_size != starting_size

    widget._handle_screen_changed(_RuntimeScreenStub(96.0))
    _settle_events(qapplication)
    assert widget.size() == starting_size
    assert widget._design_preferred_size == QtCore.QSizeF(starting_size)

    widget._handle_screen_changed(_RuntimeScreenStub(144.0))
    _settle_events(qapplication)
    assert widget.size() == first_high_dpi_size
    widget._handle_screen_changed(_RuntimeScreenStub(96.0))
    _settle_events(qapplication)
    assert widget.size() == starting_size
    assert widget._design_preferred_size == QtCore.QSizeF(starting_size)

    widget.deleteLater()


def test_runtime_dpi_growth_clamps_each_edge_on_negative_coordinate_screen(
    qapplication, monkeypatch
):
    manager = SettingsManager.get_instance()
    manager.header_font_size = 18
    manager.cell_font_size = 18
    manager.widget_size = {
        "width": Config.DEFAULT_WINDOW_SIZE[0],
        "height": Config.DEFAULT_WINDOW_SIZE[1],
    }
    available = QtCore.QRect(-1920, -200, 1600, 900)

    for edge in ("left", "top", "right", "bottom"):
        widget = _create_widget(monkeypatch, manager, dpi_scale=1.0)
        starting_size = widget.size()
        safe_x = available.left() + 100
        safe_y = available.top() + 100
        start_positions = {
            "left": QtCore.QPoint(available.left() - 75, safe_y),
            "top": QtCore.QPoint(safe_x, available.top() - 75),
            "right": QtCore.QPoint(
                available.right() - starting_size.width() + 1,
                safe_y,
            ),
            "bottom": QtCore.QPoint(
                safe_x,
                available.bottom() - starting_size.height() + 1,
            ),
        }
        widget.move(start_positions[edge])

        widget._handle_screen_changed(
            _RuntimeScreenStub(144.0, available=available)
        )
        _settle_events(qapplication)

        assert widget.width() > starting_size.width()
        assert widget.height() > starting_size.height()
        assert widget.x() >= available.left()
        assert widget.y() >= available.top()
        assert widget.x() + widget.width() <= available.right() + 1
        assert widget.y() + widget.height() <= available.bottom() + 1
        if edge == "left":
            assert widget.x() == available.left()
        elif edge == "top":
            assert widget.y() == available.top()
        elif edge == "right":
            assert widget.x() == available.right() - widget.width() + 1
        else:
            assert widget.y() == available.bottom() - widget.height() + 1

        widget.deleteLater()


def test_hide_show_reconnects_only_when_window_handle_changes(
    qapplication, monkeypatch
):
    manager = SettingsManager.get_instance()
    widget = _create_widget(monkeypatch, manager, dpi_scale=1.0)
    first_screen = _RuntimeScreenStub(96.0)
    second_screen = _RuntimeScreenStub(144.0)
    first_handle = _WindowHandleStub(first_screen)
    second_handle = _WindowHandleStub(second_screen)
    active_handle = {"value": first_handle}
    monkeypatch.setattr(
        widget,
        "windowHandle",
        lambda: active_handle["value"],
    )

    widget.show()
    widget.hide()
    active_handle["value"] = second_handle
    widget.show()
    widget.hide()
    widget.show()
    _settle_events(qapplication)

    assert first_handle.screenChanged.slots == []
    assert second_handle.screenChanged.slots == [widget._handle_screen_changed]
    assert first_screen.logicalDotsPerInchChanged.slots == []
    assert second_screen.logicalDotsPerInchChanged.slots == [
        widget._handle_screen_dpi_changed
    ]
    assert widget._screen_change_window is second_handle
    assert widget._dpi_screen is second_screen

    widget.hide()
    widget.deleteLater()


def test_deferred_dpi_restores_native_shrink_before_signal(qapplication, monkeypatch):
    manager = SettingsManager.get_instance()
    manager.widget_size = {"width": 580, "height": 592}
    widget = _create_widget(monkeypatch, manager, dpi_scale=1.0)
    monkeypatch.setattr(widget, "apply_minimum_cell_sizes", lambda screen: widget.setMinimumSize(400, 312))

    widget.resize(464, 474)  # Windows has already changed geometry before the signal.
    widget._handle_screen_changed(_RuntimeScreenStub(96.0))
    assert widget.size() == QtCore.QSize(464, 474)
    assert widget._design_preferred_size == QtCore.QSizeF(580, 592)

    _settle_events(qapplication)

    assert widget.size() == QtCore.QSize(580, 592)
    assert widget._design_preferred_size == QtCore.QSizeF(580, 592)
    assert manager._pending_widget_settings is None
    widget.deleteLater()


def test_deferred_dpi_restores_native_shrink_after_signal(qapplication, monkeypatch):
    manager = SettingsManager.get_instance()
    manager.widget_size = {"width": 580, "height": 592}
    widget = _create_widget(monkeypatch, manager, dpi_scale=1.0)
    monkeypatch.setattr(widget, "apply_minimum_cell_sizes", lambda screen: widget.setMinimumSize(400, 312))

    widget._handle_screen_changed(_RuntimeScreenStub(96.0))
    assert widget.size() == QtCore.QSize(580, 592)
    widget.resize(464, 474)  # Native geometry arrives after the handler returned.
    _settle_events(qapplication)

    assert widget.size() == QtCore.QSize(580, 592)
    assert widget._design_preferred_size == QtCore.QSizeF(580, 592)
    assert manager._pending_widget_settings is None
    widget.deleteLater()


def test_deferred_dpi_round_trip_ignores_native_scale_transients(qapplication, monkeypatch):
    manager = SettingsManager.get_instance()
    manager.widget_size = {"width": 400, "height": 320}
    widget = _create_widget(monkeypatch, manager, dpi_scale=1.0)

    def apply_minimum(screen):
        # Fixed transition contracts; the real font/grid formula is tested above.
        widget.setMinimumSize(400, 312 if screen.dpi == 96.0 else 376)

    monkeypatch.setattr(widget, "apply_minimum_cell_sizes", apply_minimum)
    for dpi, native_size, expected in (
        (96.0, (400, 320), (400, 320)),
        (120.0, (500, 470), (500, 400)),
        (96.0, (400, 320), (400, 320)),
        (120.0, (500, 470), (500, 400)),
    ):
        screen = _RuntimeScreenStub(dpi)
        widget._handle_screen_changed(screen)
        widget.setMinimumSize(400, 312)
        widget.resize(*native_size)
        _settle_events(qapplication)
        assert widget.size() == QtCore.QSize(*expected)
        assert widget._design_preferred_size == QtCore.QSizeF(400, 320)

    assert manager._pending_widget_settings is None
    widget.deleteLater()


def test_user_resize_release_updates_preferred_size(qapplication, monkeypatch):
    manager = SettingsManager.get_instance()
    manager.widget_size = {"width": 580, "height": 592}
    widget = _create_widget(monkeypatch, manager, dpi_scale=1.0)

    _resize_widget_by_mouse(widget, 500, 500, release=False)
    assert widget.size() == QtCore.QSize(500, 500)
    assert widget._design_preferred_size == QtCore.QSizeF(580, 592)
    _release_left_mouse(widget)
    assert widget._design_preferred_size == QtCore.QSizeF(580, 592)
    assert manager._pending_widget_settings is None
    _settle_events(qapplication)
    assert widget._design_preferred_size == QtCore.QSizeF(500, 500)
    assert manager._pending_widget_settings["size"] == {"width": 500, "height": 500}

    widget._handle_screen_changed(_RuntimeScreenStub(96.0))
    widget.resize(464, 474)
    _settle_events(qapplication)

    assert widget.size() == QtCore.QSize(500, 500)
    assert widget._design_preferred_size == QtCore.QSizeF(500, 500)
    widget.deleteLater()


def test_deferred_dpi_expands_only_minimum_required_axis(qapplication, monkeypatch):
    manager = SettingsManager.get_instance()
    manager.widget_size = {"width": 500, "height": 400}
    widget = _create_widget(monkeypatch, manager, dpi_scale=1.0)
    monkeypatch.setattr(widget, "apply_minimum_cell_sizes", lambda screen: widget.setMinimumSize(420, 550))

    widget._handle_screen_changed(_RuntimeScreenStub(120.0))
    _settle_events(qapplication)

    assert widget.size() == QtCore.QSize(625, 550)  # Only height exceeds scaled 625x500.
    assert widget._design_preferred_size == QtCore.QSizeF(500, 400)
    assert manager._pending_widget_settings is None
    widget.deleteLater()


def test_deferred_dpi_coalesces_screen_and_dpi_signals(qapplication, monkeypatch):
    manager = SettingsManager.get_instance()
    manager.widget_size = {"width": 580, "height": 592}
    widget = _create_widget(monkeypatch, manager, dpi_scale=1.0)
    screen = _RuntimeScreenStub(96.0)
    handle = _WindowHandleStub(screen)
    monkeypatch.setattr(widget, "windowHandle", lambda: handle)
    monkeypatch.setattr(widget, "apply_minimum_cell_sizes", lambda screen: widget.setMinimumSize(400, 312))
    widget._connect_screen_signals()
    _settle_events(qapplication)

    widget.resize(464, 474)
    widget.move(1800, 900)
    resizes, moves = [], []
    resize, move = widget.resize, widget.move

    def record_resize(size):
        resizes.append(QtCore.QSize(size))
        resize(size)

    def record_move(pos):
        moves.append(QtCore.QPoint(pos))
        move(pos)

    monkeypatch.setattr(widget, "resize", record_resize)
    monkeypatch.setattr(widget, "move", record_move)
    timeouts = QtTest.QSignalSpy(widget._dpi_correction_timer.timeout)
    handle.screenChanged.emit(screen)
    handle.screenChanged.emit(screen)
    screen.set_dpi(120.0)
    _settle_events(qapplication)
    _settle_events(qapplication)

    assert len(timeouts) == 1
    assert resizes == [QtCore.QSize(725, 740)]
    assert moves == [QtCore.QPoint(1195, 340)]
    assert widget.size() == QtCore.QSize(725, 740)
    assert not widget._dpi_transition_pending
    assert manager._pending_widget_settings is None
    widget.deleteLater()


def test_deferred_dpi_reads_current_window_screen(qapplication, monkeypatch):
    manager = SettingsManager.get_instance()
    manager.widget_size = {"width": 580, "height": 592}
    widget = _create_widget(monkeypatch, manager, dpi_scale=1.0)
    old_screen = _RuntimeScreenStub(192.0)
    current_screen = _RuntimeScreenStub(96.0)
    handle = _WindowHandleStub(old_screen)
    monkeypatch.setattr(widget, "windowHandle", lambda: handle)
    applied = []

    def apply_minimum(screen):
        applied.append(screen)
        widget.setMinimumSize(900, 900) if screen is old_screen else widget.setMinimumSize(400, 312)

    monkeypatch.setattr(widget, "apply_minimum_cell_sizes", apply_minimum)
    widget._connect_screen_signals()
    # The native window has moved again before the queued correction runs.
    handle._screen = current_screen
    _settle_events(qapplication)

    assert applied == [current_screen]
    assert widget._dpi_screen is current_screen
    assert old_screen.logicalDotsPerInchChanged.slots == []
    assert widget.size() == QtCore.QSize(580, 592)
    widget.deleteLater()


def test_deferred_dpi_discards_superseded_correction(qapplication, monkeypatch):
    manager = SettingsManager.get_instance()
    manager.widget_size = {"width": 580, "height": 592}
    widget = _create_widget(monkeypatch, manager, dpi_scale=1.0)
    old_screen = _RuntimeScreenStub(192.0)
    new_screen = _RuntimeScreenStub(96.0)
    handle = _WindowHandleStub(old_screen)
    monkeypatch.setattr(widget, "windowHandle", lambda: handle)
    applied = []

    def apply_minimum(screen):
        applied.append(screen)
        if screen is old_screen:
            widget.setMinimumSize(620, 650)
            # A nested transition must invalidate the in-flight old correction.
            handle._screen = new_screen
            handle.screenChanged.emit(new_screen)
        else:
            widget.setMinimumSize(400, 312)

    monkeypatch.setattr(widget, "apply_minimum_cell_sizes", apply_minimum)
    widget._connect_screen_signals()
    _settle_events(qapplication)
    _settle_events(qapplication)
    widget._apply_deferred_dpi_correction()  # A late callback is now a no-op.

    assert applied == [old_screen, new_screen]
    assert widget._dpi_screen is new_screen
    assert widget.size() == QtCore.QSize(580, 592)
    assert widget._design_preferred_size == QtCore.QSizeF(580, 592)
    assert not widget._dpi_transition_pending
    widget.deleteLater()


def test_deferred_dpi_defers_drag_release_save(qapplication, monkeypatch, tmp_path):
    manager = SettingsManager.get_instance()
    manager.widget_size = {"width": 580, "height": 592}
    widget = _create_widget(monkeypatch, manager, dpi_scale=1.0)
    QtWidgets.QApplication.sendEvent(
        widget,
        QtGui.QMouseEvent(
            QtCore.QEvent.MouseButtonPress, QtCore.QPointF(10, 10),
            QtCore.Qt.LeftButton, QtCore.Qt.LeftButton, QtCore.Qt.NoModifier,
        ),
    )
    assert widget.dragging and not widget.resizing
    widget._handle_screen_changed(_RuntimeScreenStub(96.0))
    widget.resize(464, 474)
    _release_left_mouse(widget)

    assert widget._design_preferred_size == QtCore.QSizeF(580, 592)
    assert manager._pending_widget_settings is None
    assert widget._save_after_dpi_transition
    _settle_events(qapplication)
    manager.flush_pending_widget_settings()

    saved = json.loads((tmp_path / "widget_settings.json").read_text(encoding="utf-8"))
    assert saved["size"] == {"width": 580, "height": 592}
    assert not widget._save_after_dpi_transition
    widget.deleteLater()


def test_deferred_dpi_waits_for_user_resize_release(qapplication, monkeypatch):
    manager = SettingsManager.get_instance()
    manager.widget_size = {"width": 580, "height": 592}
    widget = _create_widget(monkeypatch, manager, dpi_scale=1.0)
    _resize_widget_by_mouse(widget, 500, 500, release=False)
    widget._handle_screen_changed(_RuntimeScreenStub(96.0))
    widget.resize(464, 474)
    _settle_events(qapplication)

    assert widget._design_preferred_size == QtCore.QSizeF(580, 592)
    assert widget._dpi_transition_pending
    assert not widget._dpi_correction_timer.isActive()
    _release_left_mouse(widget)
    assert widget._design_preferred_size == QtCore.QSizeF(580, 592)
    assert manager._pending_widget_settings is None
    _settle_events(qapplication)

    assert widget.size() == QtCore.QSize(500, 500)
    assert widget._design_preferred_size == QtCore.QSizeF(500, 500)
    assert manager._pending_widget_settings["size"] == {"width": 500, "height": 500}
    assert not widget._dpi_transition_pending
    widget.deleteLater()


def test_deferred_dpi_cleanup_cancels_pending_callback(qapplication, monkeypatch):
    manager = SettingsManager.get_instance()
    manager.widget_size = {"width": 580, "height": 592}
    widget = _create_widget(monkeypatch, manager, dpi_scale=1.0)
    widget.resize(464, 474)
    widget._handle_screen_changed(_RuntimeScreenStub(96.0))

    widget._disconnect_screen_signals()
    _settle_events(qapplication)

    assert not widget._dpi_correction_timer.isActive()
    assert not widget._dpi_transition_pending
    assert widget._dpi_screen is None
    assert widget.size() == QtCore.QSize(464, 474)
    assert manager._pending_widget_settings is None
    widget.deleteLater()



def _install_dpi_acceptance_boundary(monkeypatch, widget, low, high):
    """Model HFW above minimumSize; record the real top-level query boundary."""
    constraint = {"size": QtCore.QSize(*low)}
    queries = []

    def apply_minimum(screen):
        widget.setMinimumSize(400, 312)
        constraint["size"] = QtCore.QSize(*(low if screen.dpi == 96 else high))

    def closest(top_level, requested):
        assert top_level is widget
        assert top_level.layout() is not None
        queries.append(QtCore.QSize(requested))
        return requested.expandedTo(constraint["size"])

    monkeypatch.setattr(widget, "apply_minimum_cell_sizes", apply_minimum)
    monkeypatch.setattr(QtWidgets.QLayout, "closestAcceptableSize", closest)
    return queries


@pytest.mark.parametrize("high_hfw, expected_height", ((579, 591), (620, 620)))
def test_dpi_design_preferred_and_applied_hfw_round_trips(
    qapplication, monkeypatch, high_hfw, expected_height
):
    manager = SettingsManager.get_instance()
    manager.widget_size = {"width": 480, "height": 473}
    widget = _create_widget(monkeypatch, manager, dpi_scale=1.0)
    queries = _install_dpi_acceptance_boundary(
        monkeypatch, widget, (480, 473), (480, high_hfw)
    )
    requests = []
    resize = widget.resize

    def record_resize(size):
        requests.append(QtCore.QSize(size))
        resize(size)

    monkeypatch.setattr(widget, "resize", record_resize)
    for dpi, expected in (
        (96, (480, 473)), (120, (600, expected_height)), (96, (480, 473)),
        (120, (600, expected_height)), (96, (480, 473)),
    ):
        requests.clear()
        widget._handle_screen_changed(_RuntimeScreenStub(dpi))
        _settle_events(qapplication)
        assert widget.size() == QtCore.QSize(*expected)
        assert widget._design_preferred_size == QtCore.QSizeF(480, 473)
        assert widget.minimumHeight() < widget.height()  # Real HFW boundary wins.
        assert all(size == QtCore.QSize(*expected) for size in requests)
        assert not widget._dpi_correction_timer.isActive()
        assert manager._pending_widget_settings is None
    assert queries == [
        QtCore.QSize(480, 473), QtCore.QSize(600, 591), QtCore.QSize(480, 473),
        QtCore.QSize(600, 591), QtCore.QSize(480, 473),
    ]
    widget.deleteLater()


@pytest.mark.parametrize(
    ("resize_dpi", "chosen"),
    ((96, (500, 520)), (120, (625, 650))),
)
def test_dpi_user_resize_becomes_design_preferred_after_settle(
    qapplication, monkeypatch, resize_dpi, chosen
):
    manager = SettingsManager.get_instance()
    manager.widget_size = {"width": 415, "height": 473}
    widget = _create_widget(monkeypatch, manager, dpi_scale=1.0)
    _install_dpi_acceptance_boundary(monkeypatch, widget, (415, 473), (500, 620))
    widget._handle_screen_changed(_RuntimeScreenStub(resize_dpi))
    _settle_events(qapplication)
    _resize_widget_by_mouse(widget, *chosen)
    assert widget._design_preferred_size == QtCore.QSizeF(415, 473)
    assert manager._pending_widget_settings is None
    _settle_events(qapplication)
    assert widget.size() == QtCore.QSize(*chosen)
    assert widget._design_preferred_size == QtCore.QSizeF(500, 520)
    assert manager._pending_widget_settings["size"] == dict(zip(("width", "height"), chosen))
    manager.flush_pending_widget_settings()

    for dpi, expected in ((120, (625, 650)), (96, (500, 520)), (120, (625, 650))):
        widget._handle_screen_changed(_RuntimeScreenStub(dpi))
        _settle_events(qapplication)
        assert widget.size() == QtCore.QSize(*expected)
        assert widget._design_preferred_size == QtCore.QSizeF(500, 520)
        assert manager._pending_widget_settings is None
    widget.deleteLater()


def test_dpi_user_resize_below_hfw_commits_allowed_design_size(qapplication, monkeypatch):
    manager = SettingsManager.get_instance()
    manager.widget_size = {"width": 600, "height": 650}
    widget = _create_widget(monkeypatch, manager, dpi_scale=1.0)
    _install_dpi_acceptance_boundary(monkeypatch, widget, (415, 473), (500, 620))
    _resize_widget_by_mouse(widget, 500, 520, release=False)
    widget._handle_screen_changed(_RuntimeScreenStub(120))
    widget.resize(625, 650)  # Native transient must not become the preference.
    _release_left_mouse(widget)
    _settle_events(qapplication)
    assert widget.size() == QtCore.QSize(500, 620)
    assert widget._design_preferred_size == QtCore.QSizeF(400, 496)
    assert manager._pending_widget_settings["size"] == {"width": 500, "height": 620}
    for dpi, expected in ((96, (415, 496)), (120, (500, 620))):
        widget._handle_screen_changed(_RuntimeScreenStub(dpi))
        _settle_events(qapplication)
        assert widget.size() == QtCore.QSize(*expected)
        assert widget._design_preferred_size == QtCore.QSizeF(400, 496)
    widget.deleteLater()


class _HfwCell(QtWidgets.QLabel):
    """Platform-independent wrapped-content boundary inside the real grid."""
    def __init__(self):
        super().__init__()
        self.content_height = 56
        policy = self.sizePolicy()
        policy.setHeightForWidth(True)
        self.setSizePolicy(policy)

    def minimumSizeHint(self):
        return QtCore.QSize(20, 20)

    def sizeHint(self):
        return QtCore.QSize(40, 20)

    def heightForWidth(self, width):
        return self.content_height + 1000 // max(1, width)


def test_dpi_real_root_hfw_restores_header_without_surplus(qapplication, monkeypatch):
    manager = SettingsManager.get_instance()
    manager.header_font_size = manager.cell_font_size = 10
    manager.widget_size = {"width": 415, "height": 473}
    widget = _create_widget(monkeypatch, manager, dpi_scale=1.0)
    cells = []
    for row in range(1, 8):
        cell = _HfwCell()
        original = widget.cell_widgets[(row, 1)]
        widget.grid_layout.removeWidget(original)
        original.deleteLater()
        widget.grid_layout.addWidget(cell, row, 1)
        widget.cell_widgets[(row, 1)] = cell
        cells.append(cell)
    widget.show()  # Only the offscreen Qt platform is used.
    screen = _RuntimeScreenStub(96)
    handle = _WindowHandleStub(screen)
    monkeypatch.setattr(widget, "windowHandle", lambda: handle)
    apply_minimum = widget.apply_minimum_cell_sizes

    def apply_content_constraints(current):
        for cell in cells:
            cell.content_height = 56 if current.dpi == 96 else 70
            # Leave cached item HFW hints populated: production refresh must
            # invalidate them, not this fixture.
        apply_minimum(current)

    monkeypatch.setattr(widget, "apply_minimum_cell_sizes", apply_content_constraints)
    widget._handle_screen_changed(screen)
    _settle_events(qapplication)
    preferred = QtCore.QSizeF(widget._design_preferred_size)
    starting = widget.size()
    # Inspect laid-out children: Qt's HFW queries can mutate cellRect caches
    # without changing the actual child geometry.
    header_height = widget.day_headers[1].height()
    body_height = cells[0].height()
    assert widget.layout().hasHeightForWidth()
    assert widget.layout().minimumHeightForWidth(starting.width()) > widget.minimumHeight()
    assert widget.layout().minimumHeightForWidth(405) > widget.layout().minimumHeightForWidth(500)

    screen.set_dpi(120)
    _settle_events(qapplication)
    assert widget.height() > starting.height()
    assert cells[0].height() > body_height
    assert widget.size() == QtWidgets.QLayout.closestAcceptableSize(widget, QtCore.QSize(519, 591))
    screen.set_dpi(96)
    widget.resize(starting.width(), starting.height() + 8)
    _settle_events(qapplication)
    assert widget.size() == starting == QtWidgets.QLayout.closestAcceptableSize(widget, preferred.toSize())
    assert widget.day_headers[1].height() == header_height
    assert cells[0].height() == body_height
    assert widget._design_preferred_size == preferred
    assert manager._pending_widget_settings is None
    assert not widget._dpi_correction_timer.isActive()
    widget.hide()
    widget.deleteLater()


def test_dpi_drag_waits_for_release_styles_and_last_layout_event(qapplication, monkeypatch):
    manager = SettingsManager.get_instance()
    manager.widget_size = {"width": 415, "height": 473}
    widget = _create_widget(monkeypatch, manager, dpi_scale=1.0)
    queries = _install_dpi_acceptance_boundary(monkeypatch, widget, (415, 473), (415, 579))
    QtWidgets.QApplication.sendEvent(widget, QtGui.QMouseEvent(
        QtCore.QEvent.MouseButtonPress, QtCore.QPointF(10, 10),
        QtCore.Qt.LeftButton, QtCore.Qt.LeftButton, QtCore.Qt.NoModifier,
    ))
    widget._handle_screen_changed(_RuntimeScreenStub(120))
    _settle_events(qapplication)
    assert widget.dragging and queries == []
    assert not widget._dpi_correction_timer.isActive()
    styles = []
    update_styles = widget.update_styles

    def restore_styles():
        styles.append(True)
        update_styles()

    monkeypatch.setattr(widget, "update_styles", restore_styles)
    _release_left_mouse(widget)
    assert styles == [True]
    generation = widget._dpi_transition_generation
    for receiver, event_type in (
        (widget, QtCore.QEvent.LayoutRequest),
        (widget.day_headers[1], QtCore.QEvent.FontChange),
        (widget.day_headers[1], QtCore.QEvent.StyleChange),
    ):
        QtTest.QTest.qWait(Widget.DPI_SETTLE_MS // 2)
        QtWidgets.QApplication.sendEvent(receiver, QtCore.QEvent(event_type))
        assert queries == []  # Each late event extends the debounce.
    assert widget._dpi_transition_generation > generation
    _settle_events(qapplication)
    assert queries == [QtCore.QSize(519, 591)]
    assert widget.size() == QtCore.QSize(519, 591)
    assert widget._design_preferred_size == QtCore.QSizeF(415, 473)
    assert manager._pending_widget_settings["size"] == {"width": 519, "height": 591}
    assert not widget._dpi_transition_pending
    assert not widget._dpi_correction_timer.isActive()
    widget.deleteLater()



def test_dpi_second_gesture_preserves_unsettled_user_resize(qapplication, monkeypatch):
    manager = SettingsManager.get_instance()
    manager.widget_size = {"width": 415, "height": 473}
    widget = _create_widget(monkeypatch, manager, dpi_scale=1.0)
    _install_dpi_acceptance_boundary(monkeypatch, widget, (415, 473), (500, 620))
    _resize_widget_by_mouse(widget, 500, 520)
    QtWidgets.QApplication.sendEvent(widget, QtGui.QMouseEvent(
        QtCore.QEvent.MouseButtonPress, QtCore.QPointF(10, 10),
        QtCore.Qt.LeftButton, QtCore.Qt.LeftButton, QtCore.Qt.NoModifier,
    ))
    widget._handle_screen_changed(_RuntimeScreenStub(120))
    widget.resize(625, 650)
    _settle_events(qapplication)
    assert widget.dragging and widget._commit_user_resize
    assert widget._design_preferred_size == QtCore.QSizeF(415, 473)
    assert manager._pending_widget_settings is None
    _release_left_mouse(widget)
    _settle_events(qapplication)
    assert widget.size() == QtCore.QSize(500, 620)
    assert widget._design_preferred_size == QtCore.QSizeF(400, 496)
    assert manager._pending_widget_settings["size"] == {"width": 500, "height": 620}
    widget.deleteLater()


def test_dpi_shrink_clamps_negative_screen_position(qapplication, monkeypatch):
    manager = SettingsManager.get_instance()
    manager.widget_size = {"width": 415, "height": 473}
    widget = _create_widget(monkeypatch, manager, dpi_scale=1.0)
    _install_dpi_acceptance_boundary(monkeypatch, widget, (415, 473), (415, 579))
    available = QtCore.QRect(-1920, -200, 1600, 900)
    widget._handle_screen_changed(_RuntimeScreenStub(120, available))
    _settle_events(qapplication)
    widget.move(-2000, -300)
    widget._handle_screen_changed(_RuntimeScreenStub(96, available))
    _settle_events(qapplication)
    assert widget.size() == QtCore.QSize(415, 473)
    assert widget.pos() == available.topLeft()
    assert widget._design_preferred_size == QtCore.QSizeF(415, 473)
    widget.deleteLater()


def test_design_dpi_startup_initializes_once_from_legacy_geometry(qapplication, monkeypatch):
    manager = SettingsManager.get_instance()
    manager.widget_size = {"width": 600, "height": 591}
    monkeypatch.setattr(Widget, "_get_initial_dpi_scale", lambda self: 1.25)
    widget = Widget(settings_manager=manager, notification_manager=_NotificationStub())
    widget.timer.stop()
    screen = _RuntimeScreenStub(120)
    handle = _WindowHandleStub(screen)
    monkeypatch.setattr(widget, "windowHandle", lambda: handle)
    assert widget._design_preferred_size is None

    widget.show()
    _settle_events(qapplication)
    assert widget.size() == QtCore.QSize(600, 591)
    assert isinstance(widget._design_preferred_size, QtCore.QSizeF)
    assert widget._design_preferred_size == QtCore.QSizeF(480, 472.8)
    assert manager.widget_size == {"width": 600, "height": 591}
    assert manager._pending_widget_settings is None

    screen.set_dpi(96)
    _settle_events(qapplication)
    widget.hide()
    widget.show()
    _settle_events(qapplication)
    assert widget.size() == QtCore.QSize(480, 473)
    assert widget._design_preferred_size == QtCore.QSizeF(480, 472.8)
    assert manager._pending_widget_settings is None
    widget.hide()
    widget.deleteLater()


def test_design_dpi_startup_includes_real_wrapped_content(qapplication, monkeypatch):
    manager = SettingsManager.get_instance()
    manager.header_font_size = manager.cell_font_size = 13
    manager.widget_size = {"width": 480, "height": 320}
    manager.timetable_data = {"월": {str(row): "Lesson\nRoom" for row in range(1, 8)}}
    widget = _create_widget(monkeypatch, manager, dpi_scale=1.25)
    assert widget.height() > 320
    assert widget._design_preferred_size == QtCore.QSizeF(widget.size()) / 1.25
    assert manager.widget_size == {"width": 480, "height": 320}
    assert manager._pending_widget_settings is None
    widget.deleteLater()


def test_design_dpi_fractional_round_trips_do_not_drift(qapplication, monkeypatch):
    manager = SettingsManager.get_instance()
    manager.widget_size = {"width": 601, "height": 593}
    widget = _create_widget(monkeypatch, manager, dpi_scale=1.25)
    design = QtCore.QSizeF(480.8, 474.4)
    assert widget._design_preferred_size == design
    # Fixed, independently rounded targets; do not multiply previous actual.
    for _ in range(4):
        for dpi, expected in (
            (96, (481, 474)), (144, (721, 712)), (132, (661, 652)),
            (110, (551, 544)), (120, (601, 593)),
        ):
            widget._handle_screen_changed(_RuntimeScreenStub(dpi))
            _settle_events(qapplication)
            assert widget.size() == QtCore.QSize(*expected)
            assert widget._design_preferred_size == design
            assert not widget._dpi_transition_pending
    assert manager._pending_widget_settings is None
    widget.deleteLater()


def test_design_dpi_rounds_half_up_without_device_pixel_ratio(qapplication, monkeypatch):
    manager = SettingsManager.get_instance()
    manager.widget_size = {"width": 481, "height": 475}
    widget = _create_widget(monkeypatch, manager, dpi_scale=1.0)
    screen = _RuntimeScreenStub(144)

    def forbidden_dpr():
        raise AssertionError("Design geometry must not be scaled by DPR again")

    screen.devicePixelRatio = forbidden_dpr
    widget._handle_screen_changed(screen)
    _settle_events(qapplication)
    assert widget.size() == QtCore.QSize(722, 713)
    assert widget._design_preferred_size == QtCore.QSizeF(481, 475)
    widget.deleteLater()


def test_design_dpi_real_labels_restore_rows_after_font_and_geometry_history(
    qapplication, monkeypatch
):
    manager = SettingsManager.get_instance()
    manager.header_font_size = manager.cell_font_size = 13
    manager.widget_size = {"width": 480, "height": 320}
    manager.timetable_data = {"월": {str(row): "Lesson\nRoom" for row in range(1, 8)}}
    widget = _create_widget(monkeypatch, manager, dpi_scale=1.0)
    screen = _RuntimeScreenStub(96)
    monkeypatch.setattr(widget, "windowHandle", lambda: _WindowHandleStub(screen))
    apply_minimum = widget.apply_minimum_cell_sizes

    def simulate_screen_font(current):
        widget.update_styles()
        # Offscreen cannot change a physical screen's font DPI. Use real QLabel
        # font/style/layout events with proportional pixel fonts for this boundary.
        pixels = 20 if current.dpi == 96 else 25
        for label in widget.findChildren(QtWidgets.QLabel):
            label.setStyleSheet(re.sub(
                r"font-size:\s*[\d.]+pt;", f"font-size: {pixels}px;", label.styleSheet()
            ))
        apply_minimum(current)

    monkeypatch.setattr(widget, "apply_minimum_cell_sizes", simulate_screen_font)
    widget.show()
    _settle_events(qapplication)
    design = QtCore.QSizeF(widget._design_preferred_size)
    starting = widget.size()

    def row_heights():
        return [widget.day_headers[1].height()] + [
            widget.cell_widgets[(row, 1)].height() for row in range(1, 8)
        ]

    starting_rows = row_heights()
    screen.set_dpi(120)
    _settle_events(qapplication)
    assert widget.width() == 600
    assert widget.height() > starting.height()
    assert widget.cell_widgets[(1, 1)].height() > starting_rows[1]
    # Exercise HFW caches at widths seen during a native transition, including
    # a too-narrow intermediate width, before returning to the initial screen.
    for width in (380, 480, 580):
        widget.grid_layout.heightForWidth(width)
        widget.layout().heightForWidth(width + 20)
    widget.resize(starting.width(), starting.height() + 8)
    screen.set_dpi(96)
    _settle_events(qapplication)
    assert widget.size() == starting
    assert row_heights() == starting_rows
    assert widget._design_preferred_size == design
    assert not widget._dpi_transition_pending
    assert not widget._dpi_correction_timer.isActive()
    assert manager._pending_widget_settings is None
    # Returning to 96 DPI must restore the original design margin/spacing.
    assert widget.layout().contentsMargins() == QtCore.QMargins(10, 10, 10, 10)
    assert widget.grid_layout.spacing() == 4
    widget.hide()
    widget.deleteLater()


@pytest.mark.parametrize(
    "scale, margins, spacing",
    (
        (1.0, (10, 10, 10, 10), 4),
        (1.1, (11, 11, 11, 11), 4),
        (1.125, (11, 11, 12, 12), 5),
        (110 / 96, (11, 11, 12, 12), 5),
        (1.25, (12, 12, 13, 13), 5),
        (1.375, (14, 14, 14, 14), 6),
        (1.5, (15, 15, 15, 15), 6),
    ),
)
def test_dpi_layout_spacing_applies_at_startup(qapplication, monkeypatch, scale, margins, spacing):
    manager = SettingsManager.get_instance()
    manager.widget_size = {"width": 800, "height": 700}
    monkeypatch.setattr(Widget, "_get_initial_dpi_scale", lambda self: scale)
    widget = Widget(settings_manager=manager, notification_manager=_NotificationStub())
    widget.timer.stop()
    # Check construction before showEvent or any runtime normalization.
    assert widget.layout().contentsMargins() == QtCore.QMargins(*margins)
    assert widget.grid_layout.horizontalSpacing() == spacing
    assert widget.grid_layout.verticalSpacing() == spacing
    assert widget.minimumSize() == widget.layout().minimumSize().expandedTo(
        QtCore.QSize(*Config.DEFAULT_WINDOW_SIZE)
    )
    widget.deleteLater()


def test_dpi_layout_spacing_round_trips_from_design_units(qapplication, monkeypatch):
    manager = SettingsManager.get_instance()
    manager.widget_size = {"width": 600, "height": 600}
    widget = _create_widget(monkeypatch, manager, dpi_scale=1.0)
    screen = _RuntimeScreenStub(96)
    widget._connect_dpi_screen(screen)
    for _ in range(3):
        for dpi, margins, spacing in (
            (120, (12, 12, 13, 13), 5),
            (105.6, (11, 11, 11, 11), 4),
            (132, (14, 14, 14, 14), 6),
            (144, (15, 15, 15, 15), 6),
            (110, (11, 11, 12, 12), 5),
            (96, (10, 10, 10, 10), 4),
        ):
            screen.set_dpi(dpi)
            _settle_events(qapplication)
            assert widget.layout().contentsMargins() == QtCore.QMargins(*margins)
            assert widget.grid_layout.horizontalSpacing() == spacing
            assert widget.grid_layout.verticalSpacing() == spacing
            assert widget._design_preferred_size == QtCore.QSizeF(600, 600)
            assert not widget._dpi_transition_pending
    assert manager._pending_widget_settings is None
    widget.deleteLater()


def test_dpi_stale_label_hints_refresh_all_labels_before_widget_minimum(qapplication, monkeypatch):
    manager = SettingsManager.get_instance()
    manager.header_font_size = manager.cell_font_size = 13
    manager.header_font_family = manager.cell_font_family = "Arial"
    manager.widget_size = {"width": 472, "height": 473}
    manager.timetable_data = {"월": {str(r): "x\nx" for r in range(1, 8)}}
    widget = _create_widget(monkeypatch, manager, dpi_scale=1.0)
    screen = _RuntimeScreenStub(96)
    monkeypatch.setattr(widget, "windowHandle", lambda: _WindowHandleStub(screen))
    widget.show()
    _settle_events(qapplication)
    labels = widget.findChildren(QtWidgets.QLabel)
    assert len(labels) == 48
    for label in labels:
        label.setStyleSheet(re.sub(r"font-size:\s*[\d.]+pt;", "font-size: 20px;", label.styleSheet()))
    widget.apply_minimum_cell_sizes(screen)

    def semantics(label):
        return (label.text(), label.wordWrap(), label.font().toString(), label.styleSheet(),
                label.alignment(), label.sizePolicy(), label.contentsMargins())

    def hints(label):
        return (label.sizeHint(), label.minimumSizeHint())

    initial_semantics = [semantics(label) for label in labels]
    initial_hints = [hints(label) for label in labels]
    root, grid = widget.layout(), widget.grid_layout
    initial_grid = (grid.heightForWidth(452), grid.minimumHeightForWidth(452))
    initial_root = root.minimumHeightForWidth(472)
    header_item = grid.itemAtPosition(0, 1)
    initial_item_hint = header_item.sizeHint()
    # Warm real QLabel hints with 125% minima and the already returned 96% font,
    # as can happen before the deferred correction after native FontChange.
    widget.apply_minimum_cell_sizes(_RuntimeScreenStub(120))
    for label in labels:
        QtWidgets.QApplication.sendEvent(label, QtCore.QEvent(QtCore.QEvent.StyleChange))
    high_hints = [hints(label) for label in labels]
    assert widget.day_headers[1].sizeHint().height() == 41
    for before, high in zip(initial_hints, high_hints):
        assert high != before  # Includes period/body widths and empty labels.

    def old_item_only_refresh():
        for label in labels:
            label.ensurePolished()
            label.updateGeometry()

    with monkeypatch.context() as old:
        old.setattr(widget, "_refresh_timetable_label_size_hints", old_item_only_refresh)
        widget.apply_minimum_cell_sizes(screen)
        assert all(label.minimumHeight() == 33 for label in labels)
        assert grid.rowMinimumHeight(0) == 33
        assert widget.day_headers[1].heightForWidth(72) == 33
        assert widget.day_headers[1].sizeHint().height() == 41
        assert header_item.minimumSize().height() == 33
        assert header_item.sizeHint().height() == 41
        assert grid.heightForWidth(452) == initial_grid[0] + 8
        assert grid.minimumHeightForWidth(452) == initial_grid[1]
        assert root.minimumHeightForWidth(472) == initial_root + 8

    # The production call must refresh every label before measuring the outer
    # minimum, not merely fix hints later at closestAcceptableSize.
    minimum_size = root.minimumSize
    measured = []

    def current_layout_minimum():
        assert [hints(label) for label in labels] == initial_hints
        measured.append(True)
        return minimum_size()

    monkeypatch.setattr(root, "minimumSize", current_layout_minimum)
    widget.apply_minimum_cell_sizes(screen)
    assert measured
    assert [hints(label) for label in labels] == initial_hints
    assert [semantics(label) for label in labels] == initial_semantics
    assert header_item.sizeHint() == initial_item_hint
    assert (grid.heightForWidth(452), grid.minimumHeightForWidth(452)) == initial_grid
    assert root.minimumHeightForWidth(472) == initial_root
    requested = QtCore.QSize(472, initial_root)
    assert QtWidgets.QLayout.closestAcceptableSize(widget, requested) == requested
    assert widget.minimumSize() == minimum_size().expandedTo(QtCore.QSize(*Config.DEFAULT_WINDOW_SIZE))
    widget.hide()
    widget.deleteLater()


def test_dpi_real_label_design_geometry_scales_and_recovers(qapplication, monkeypatch):
    manager = SettingsManager.get_instance()
    manager.header_font_size = manager.cell_font_size = 13
    manager.header_font_family = manager.cell_font_family = "Arial"
    manager.widget_size = {"width": 472, "height": 501}
    manager.timetable_data = {"월": {str(r): "x\nx" for r in range(1, 8)}}
    widget = _create_widget(monkeypatch, manager, dpi_scale=1.0)
    screen = _RuntimeScreenStub(96)
    monkeypatch.setattr(widget, "windowHandle", lambda: _WindowHandleStub(screen))
    apply_minimum = widget.apply_minimum_cell_sizes

    def simulate_native_font_before_minimum(current):
        # Pixel fonts model native font delivery; production QSS remains intact.
        widget.update_styles()
        pixels = 25 if current.dpi == 96 else 32
        for label in widget.findChildren(QtWidgets.QLabel):
            label.setStyleSheet(re.sub(r"font-size:\s*[\d.]+pt;", f"font-size: {pixels}px;", label.styleSheet()))
        apply_minimum(current)

    monkeypatch.setattr(widget, "apply_minimum_cell_sizes", simulate_native_font_before_minimum)
    widget.show()
    _settle_events(qapplication)
    design = QtCore.QSizeF(widget._design_preferred_size)

    def geometry():
        rows = [widget.day_headers[0].height()] + [widget.period_headers[r].height() for r in range(1, 8)]
        columns = [widget.day_headers[c].width() for c in range(6)]
        vertical_gaps = [widget.period_headers[1].y() - widget.day_headers[0].geometry().bottom() - 1]
        vertical_gaps += [widget.period_headers[r + 1].y() - widget.period_headers[r].geometry().bottom() - 1 for r in range(1, 7)]
        horizontal_gaps = [widget.day_headers[c + 1].x() - widget.day_headers[c].geometry().right() - 1 for c in range(5)]
        return rows, columns, vertical_gaps, horizontal_gaps

    initial = geometry()
    assert initial[0][0] == widget.day_headers[1].sizeHint().height()
    starting = widget.size()
    for _ in range(2):
        screen.set_dpi(120)
        _settle_events(qapplication)
        rows, columns, vgaps, hgaps = geometry()
        assert widget.size() == widget._scaled_design_size(screen)
        assert all(abs(high - low * 1.25) <= 1 for low, high in zip(initial[0], rows)), (initial[0], rows)
        assert all(abs(high - low * 1.25) <= 1 for low, high in zip(initial[1], columns))
        assert vgaps == [5] * 7
        assert hgaps == [5] * 5
        assert rows[0] <= widget.day_headers[1].sizeHint().height() + 1
        screen.set_dpi(96)
        _settle_events(qapplication)
        assert widget.size() == starting
        assert geometry() == initial
        assert widget._design_preferred_size == design
        assert not widget._dpi_transition_pending
        assert not widget._dpi_correction_timer.isActive()
    assert manager._pending_widget_settings is None
    widget.hide()
    widget.deleteLater()



def _apply_settings_dialog_size(monkeypatch, widget, width, height):
    """Run the real dialog apply path, isolating notification/startup side effects."""
    from gui.dialogs.settings_dialog import SettingsDialog
    from utils import auto_start

    notification = widget.notification_manager
    monkeypatch.setattr(notification, "notification_enabled", True, raising=False)
    for name in ("set_notification_enabled", "set_next_period_warning",
                 "set_warning_minutes", "save_notification_settings"):
        monkeypatch.setattr(notification, name, lambda *args: None, raising=False)
    monkeypatch.setattr(auto_start, "enable_auto_start", lambda **kwargs: True)
    monkeypatch.setattr(auto_start, "disable_auto_start", lambda **kwargs: True)
    dialog = SettingsDialog(widget)
    dialog.settings_applied.connect(widget.update_styles)
    dialog.widget_width.setValue(width)
    dialog.widget_height.setValue(height)
    dialog.apply_settings()
    return dialog


@pytest.mark.parametrize("dpi", (96, 120))
def test_settings_size_survives_show_and_dpi_round_trip(qapplication, monkeypatch, tmp_path, dpi):
    manager = SettingsManager.get_instance()
    manager.widget_size = {"width": 600, "height": 500}
    widget = _create_widget(monkeypatch, manager, dpi_scale=dpi / 96)
    screen = _RuntimeScreenStub(dpi)
    handle = _WindowHandleStub(screen)
    monkeypatch.setattr(widget, "windowHandle", lambda: handle)
    widget.show()
    _settle_events(qapplication)
    previous = QtCore.QSizeF(widget._design_preferred_size)
    dialog = _apply_settings_dialog_size(monkeypatch, widget, 700, 550)
    _settle_events(qapplication)
    expected_design = QtCore.QSizeF(700, 550) / (dpi / 96)
    assert widget.size() == QtCore.QSize(700, 550)
    assert widget._design_preferred_size == expected_design != previous
    assert manager.widget_size == {"width": 700, "height": 550}
    manager.flush_pending_widget_settings()
    assert json.loads((tmp_path / "widget_settings.json").read_text(encoding="utf-8"))["size"] == manager.widget_size
    widget.hide()
    widget.show()
    _settle_events(qapplication)
    assert widget.size() == QtCore.QSize(700, 550)
    targets = ((120, (875, 688)), (96, (700, 550))) if dpi == 96 else (
        (96, (560, 440)), (120, (700, 550)))
    for current_dpi, expected in targets:
        screen.set_dpi(current_dpi)
        widget.resize(650, 600)  # Native transient is still not a user request.
        _settle_events(qapplication)
        assert widget.size() == QtCore.QSize(*expected)
        assert widget._design_preferred_size == expected_design
        assert manager._pending_widget_settings is None
    dialog.deleteLater()
    widget.hide()
    widget.deleteLater()


def test_settings_size_commits_real_hfw_actual(qapplication, monkeypatch, tmp_path):
    manager = SettingsManager.get_instance()
    manager.header_font_size = manager.cell_font_size = 13
    manager.widget_size = {"width": 600, "height": 500}
    manager.timetable_data = {"월": {str(row): "Lesson\nRoom\nFloor\nSection" for row in range(1, 8)}}
    widget = _create_widget(monkeypatch, manager, dpi_scale=1.0)
    screen = _RuntimeScreenStub(96)
    monkeypatch.setattr(widget, "windowHandle", lambda: _WindowHandleStub(screen))
    widget.show()
    _settle_events(qapplication)
    dialog = _apply_settings_dialog_size(monkeypatch, widget, 700, 350)
    _settle_events(qapplication)
    actual = QtCore.QSize(widget.size())
    assert actual.height() > 350
    assert actual == QtWidgets.QLayout.closestAcceptableSize(widget, QtCore.QSize(700, 350))
    assert widget._design_preferred_size == QtCore.QSizeF(actual)
    manager.flush_pending_widget_settings()
    saved = json.loads((tmp_path / "widget_settings.json").read_text(encoding="utf-8"))
    assert saved["size"] == {"width": actual.width(), "height": actual.height()}
    # A later normalization must not keep requesting the impossible 700x350.
    requests = []
    resize = widget.resize
    monkeypatch.setattr(widget, "resize", lambda size: (requests.append(size), resize(size))[-1])
    screen.set_dpi(96)
    _settle_events(qapplication)
    assert widget.size() == actual and requests == []
    assert manager._pending_widget_settings is None
    dialog.deleteLater()
    widget.hide()
    widget.deleteLater()


def _shutdown_application(monkeypatch, widget, manager):
    """Use common production cleanup without terminating test threads/processes."""
    main = importlib.import_module("main")
    application = main.ApplicationManager.__new__(main.ApplicationManager)
    application._cleanup_done = False
    application.app = QtWidgets.QApplication.instance()
    application.widget = widget
    application.settings_manager = manager
    monkeypatch.setattr(main, "kill_all_threads", lambda: None)
    monkeypatch.setattr(main, "psutil", SimpleNamespace(
        Process=lambda pid: SimpleNamespace(children=lambda **kwargs: []),
        wait_procs=lambda *args, **kwargs: ([], []),
    ))
    monkeypatch.setattr(main, "multiprocessing", SimpleNamespace(active_children=lambda: []))
    return application


@pytest.mark.parametrize("mode", ("resize", "second_gesture", "move", "settings", "settled", "none", "automatic"))
def test_shutdown_save_common_cleanup_before_settle(qapplication, monkeypatch, tmp_path, mode):
    manager = SettingsManager.get_instance()
    manager.widget_size = {"width": 500, "height": 500}
    widget = _create_widget(monkeypatch, manager, dpi_scale=1.0)
    screen = _RuntimeScreenStub(96)
    monkeypatch.setattr(widget, "windowHandle", lambda: _WindowHandleStub(screen))
    widget.show()
    _settle_events(qapplication)
    writes = []
    writer = manager._write_widget_settings_atomically

    def record_write(snapshot):
        assert not widget._save_after_dpi_transition
        writes.append(snapshot)
        writer(snapshot)

    monkeypatch.setattr(manager, "_write_widget_settings_atomically", record_write)
    expected = {"width": 650, "height": 530}
    if mode in ("resize", "second_gesture", "settled"):
        _resize_widget_by_mouse(widget, 650, 530)
        if mode == "settled":
            _settle_events(qapplication)
        else:
            widget.resize(600, 620)  # Native geometry after the user's release.
            if mode == "second_gesture":
                QtWidgets.QApplication.sendEvent(widget, QtGui.QMouseEvent(
                    QtCore.QEvent.MouseButtonPress, QtCore.QPointF(10, 10),
                    QtCore.Qt.LeftButton, QtCore.Qt.LeftButton, QtCore.Qt.NoModifier,
                ))
                assert widget.dragging
    elif mode in ("move", "automatic"):
        screen.set_dpi(120)
        widget.resize(580, 620)
        widget.move(120, 130)
        if mode == "move":
            widget.save_widget_position()
        expected = {"width": 625, "height": 625}
    elif mode == "settings":
        _apply_settings_dialog_size(monkeypatch, widget, 650, 530)
    if mode in ("resize", "second_gesture", "move", "settings"):
        assert widget._save_after_dpi_transition
    # No closeEvent and no waiting for the 40ms timer: the tray uses this order.
    widget.hide()
    application = _shutdown_application(monkeypatch, widget, manager)
    application.cleanup_resources()
    application.cleanup_resources()
    widget.finalize_pending_user_save()
    if mode in ("none", "automatic"):
        assert writes == []
        assert manager.widget_size == {"width": 500, "height": 500}
        assert widget._design_preferred_size == QtCore.QSizeF(500, 500)
    else:
        assert len(writes) == 1
        saved = json.loads((tmp_path / "widget_settings.json").read_text(encoding="utf-8"))
        assert saved["size"] == expected
        assert saved["position"] == {"x": widget.x(), "y": widget.y()}
        assert not widget._save_after_dpi_transition
        assert not widget._dpi_correction_timer.isActive()
        if mode == "move":
            assert widget._design_preferred_size == QtCore.QSizeF(500, 500)
        else:
            assert widget._design_preferred_size == QtCore.QSizeF(650, 530)
    assert manager._pending_widget_settings is None
    widget._disconnect_screen_signals()
    widget.deleteLater()


def test_shutdown_save_flushes_manager_even_if_widget_finalize_fails(qapplication, monkeypatch, tmp_path):
    manager = SettingsManager.get_instance()
    widget = _create_widget(monkeypatch, manager, dpi_scale=1.0)
    manager.save_widget_position(100, 110, 650, 530)
    def fail_finalize():
        raise RuntimeError("simulated widget failure")
    monkeypatch.setattr(widget, "finalize_pending_user_save", fail_finalize)
    application = _shutdown_application(monkeypatch, widget, manager)
    application.cleanup_resources()
    saved = json.loads((tmp_path / "widget_settings.json").read_text(encoding="utf-8"))
    assert saved["size"] == {"width": 650, "height": 530}
    assert manager._pending_widget_settings is None
    widget.deleteLater()


def test_dpi_hint_scope_excludes_unrelated_child_label(qapplication, monkeypatch):
    widget = _create_widget(monkeypatch, SettingsManager.get_instance(), dpi_scale=1.0)
    unrelated = QtWidgets.QLabel("Dialog label", widget)
    policy = unrelated.sizePolicy()
    policy.setHeightForWidth(True)  # Refreshing this unwrapped label would erase it.
    unrelated.setSizePolicy(policy)
    semantics = (unrelated.text(), unrelated.wordWrap(), unrelated.sizePolicy(), unrelated.font(), unrelated.styleSheet())
    labels = list(widget.day_headers.values()) + list(widget.period_headers.values()) + list(widget.cell_widgets.values())
    refreshed = []
    for label in labels:
        original = label.setWordWrap
        monkeypatch.setattr(label, "setWordWrap", lambda wrap, label=label, original=original: (refreshed.append(label), original(wrap))[-1])
    widget._refresh_timetable_label_size_hints()
    assert refreshed == labels and len(refreshed) == 48
    assert (unrelated.text(), unrelated.wordWrap(), unrelated.sizePolicy(), unrelated.font(), unrelated.styleSheet()) == semantics
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

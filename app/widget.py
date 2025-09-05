from PyQt5 import QtWidgets, QtCore
from typing import Dict, Tuple

from infra.settings import load_config, save_config
from core.schedule import get_current_period
from app.dialogs.edit_config_dialog import EditConfigDialog
from infra.theme import get_stylesheet


class TimetableWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            QtCore.Qt.WindowStaysOnBottomHint |
            QtCore.Qt.Tool |
            QtCore.Qt.FramelessWindowHint
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)

        self.config, _ = load_config()
        self._build_ui()
        self._apply_position()

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self._update_current_period)
        self.timer.start(60_000)
        self._update_current_period()

        self.dragging = False
        self.resizing = False
        self.drag_start = None
        self.resize_start = None
        self.initial_size = self.size()
        # Context menu for editing config
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(0)

        self.grid = QtWidgets.QGridLayout()
        self.grid.setSpacing(4)

        # Headers
        self.day_headers: Dict[int, QtWidgets.QLabel] = {}
        self.period_headers: Dict[int, QtWidgets.QLabel] = {}
        self.cells: Dict[Tuple[int, int], QtWidgets.QLabel] = {}

        # Top-left empty cell
        self.grid.addWidget(QtWidgets.QLabel(""), 0, 0)

        # Day headers (columns)
        for c, day in enumerate(self.config.days, start=1):
            lbl = QtWidgets.QLabel(day.label)
            lbl.setAlignment(QtCore.Qt.AlignCenter)
            lbl.setProperty("role", "dayHeader")
            self.grid.addWidget(lbl, 0, c)
            self.day_headers[c] = lbl

        # Determine max number of periods across config
        max_periods = len(self.config.periods)

        # Period headers (rows) and cells
        for r, p in enumerate(self.config.periods, start=1):
            ph = QtWidgets.QLabel(p.label)
            ph.setAlignment(QtCore.Qt.AlignCenter)
            ph.setProperty("role", "periodHeader")
            self.grid.addWidget(ph, r, 0)
            self.period_headers[r] = ph

            for c, day in enumerate(self.config.days, start=1):
                cell = QtWidgets.QLabel()
                cell.setAlignment(QtCore.Qt.AlignCenter)
                cell.setWordWrap(True)
                cell.setProperty("role", "cell")
                self.grid.addWidget(cell, r, c)
                self.cells[(r, c)] = cell

        layout.addLayout(self.grid)
        self.setLayout(layout)
        self._render_cells()
        self.setStyleSheet(get_stylesheet(self.config))

    def show_context_menu(self, pos):
        menu = QtWidgets.QMenu(self)
        edit_cfg = menu.addAction("요일/교시/시간 편집")
        edit_cfg.triggered.connect(self.open_edit_config)
        menu.addSeparator()
        exit_act = menu.addAction("종료")
        exit_act.triggered.connect(QtWidgets.QApplication.instance().quit)
        menu.exec_(self.mapToGlobal(pos))

    def open_edit_config(self):
        dlg = EditConfigDialog(self, config=self.config)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            self.config = dlg.get_updated_config()
            save_config(self.config)
            self._rebuild_grid()
            self._update_current_period()

    def _rebuild_grid(self):
        # Clear existing grid widgets
        while self.grid.count():
            item = self.grid.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
        self.day_headers.clear()
        self.period_headers.clear()
        self.cells.clear()

        # Top-left empty
        self.grid.addWidget(QtWidgets.QLabel(""), 0, 0)

        # Days
        for c, day in enumerate(self.config.days, start=1):
            lbl = QtWidgets.QLabel(day.label)
            lbl.setAlignment(QtCore.Qt.AlignCenter)
            lbl.setProperty("role", "dayHeader")
            self.grid.addWidget(lbl, 0, c)
            self.day_headers[c] = lbl

        # Periods and cells
        for r, p in enumerate(self.config.periods, start=1):
            ph = QtWidgets.QLabel(p.label)
            ph.setAlignment(QtCore.Qt.AlignCenter)
            ph.setProperty("role", "periodHeader")
            self.grid.addWidget(ph, r, 0)
            self.period_headers[r] = ph

            for c, day in enumerate(self.config.days, start=1):
                cell = QtWidgets.QLabel()
                cell.setAlignment(QtCore.Qt.AlignCenter)
                cell.setWordWrap(True)
                cell.setProperty("role", "cell")
                self.grid.addWidget(cell, r, c)
                self.cells[(r, c)] = cell

        self._render_cells()
        self.setStyleSheet(get_stylesheet(self.config))

    def _apply_position(self):
        pos = self.config.ui.position
        self.move(pos.x, pos.y)
        self.resize(pos.width, pos.height)

    def _render_cells(self):
        # Fill timetable
        day_index = {d.id: idx for idx, d in enumerate(self.config.days, start=1)}
        period_index = {p.id: idx for idx, p in enumerate(self.config.periods, start=1)}

        for d in self.config.days:
            for pid, subject in (self.config.timetable.get(d.id, {}) or {}).items():
                r = period_index.get(pid)
                c = day_index.get(d.id)
                if r and c and (r, c) in self.cells:
                    self.cells[(r, c)].setText(str(subject))

    def _update_current_period(self):
        # Determine today id using Python weekday (0=Mon)
        weekday = QtCore.QDate.currentDate().dayOfWeek()  # 1=Mon ... 7=Sun
        day_map = {1: "mon", 2: "tue", 3: "wed", 4: "thu", 5: "fri", 6: "sat", 7: "sun"}
        today_id = day_map.get(weekday, None)
        if today_id is None:
            return

        now = QtCore.QTime.currentTime()
        current_pid = None
        # Only highlight if today exists in config
        valid_day_ids = {d.id for d in self.config.days}
        if today_id in valid_day_ids:
            current_pid = get_current_period(self.config, today_id, now)

        # Apply styles: simple highlight via background role (minimal MVP)
        day_index = {d.id: idx for idx, d in enumerate(self.config.days, start=1)}
        period_index = {p.id: idx for idx, p in enumerate(self.config.periods, start=1)}

        for (r, c), w in self.cells.items():
            w.setProperty("current", False)
            w.style().unpolish(w)
            w.style().polish(w)

        if current_pid is not None and today_id in day_index:
            r = period_index.get(current_pid)
            c = day_index.get(today_id)
            if r and c and (r, c) in self.cells:
                w = self.cells[(r, c)]
                w.setProperty("current", True)
                w.style().unpolish(w)
                w.style().polish(w)

    # Basic drag/resize
    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            pos = event.pos()
            if pos.x() >= self.rect().width() - 20 and pos.y() >= self.rect().height() - 20:
                self.resizing = True
                self.resize_start = event.globalPos()
                self.initial_size = self.size()
                self.setCursor(QtCore.Qt.SizeFDiagCursor)
            else:
                self.dragging = True
                self.drag_start = event.globalPos() - self.frameGeometry().topLeft()
                self.setCursor(QtCore.Qt.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.resizing:
            diff = event.globalPos() - self.resize_start
            new_w = max(self.minimumWidth(), self.initial_size.width() + diff.x())
            new_h = max(self.minimumHeight(), self.initial_size.height() + diff.y())
            self.resize(new_w, new_h)
        elif self.dragging and event.buttons() == QtCore.Qt.LeftButton and not self.config.ui.position.lock:
            self.move(event.globalPos() - self.drag_start)
        else:
            if event.pos().x() >= self.rect().width() - 20 and event.pos().y() >= self.rect().height() - 20:
                self.setCursor(QtCore.Qt.SizeFDiagCursor)
            else:
                self.setCursor(QtCore.Qt.ArrowCursor)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.resizing = False
            self.dragging = False
            self.setCursor(QtCore.Qt.ArrowCursor)
            # save position
            pos = self.pos()
            size = self.size()
            self.config.ui.position.x = pos.x()
            self.config.ui.position.y = pos.y()
            self.config.ui.position.width = size.width()
            self.config.ui.position.height = size.height()
            save_config(self.config)
        super().mouseReleaseEvent(event)



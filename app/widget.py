from PyQt5 import QtWidgets, QtCore
from typing import Dict, Tuple, Any, Optional, cast

from infra.settings import load_config, save_config
from core.schedule import get_current_period
from app.dialogs.edit_config_dialog import EditConfigDialog
from infra.theme import get_stylesheet


# Pylance에서 Qt 상수/속성 인식 문제를 줄이기 위해 Any로 캐스팅된 별칭 사용
Qt = cast(Any, QtCore.Qt)


class TimetableWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # 창 플래그/속성
        self.setWindowFlags(
            Qt.WindowStaysOnBottomHint | Qt.Tool | Qt.FramelessWindowHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)

        # 설정 로드 및 UI 구성
        self.config, _ = load_config()
        self._build_ui()
        self._apply_position()

        # 타이머로 현재 교시 하이라이트 업데이트
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self._update_current_period)
        self.timer.start(60_000)
        self._update_current_period()

        # 상호작용 상태
        self.dragging = False
        self.resizing = False
        self.drag_start: Optional[QtCore.QPoint] = None
        self.resize_start: Optional[QtCore.QPoint] = None
        self.initial_size = self.size()

        # 컨텍스트 메뉴
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(0)

        self.grid = QtWidgets.QGridLayout()
        self.grid.setSpacing(4)

        # 헤더/셀 컨테이너
        self.day_headers: Dict[int, QtWidgets.QLabel] = {}
        self.period_headers: Dict[int, QtWidgets.QLabel] = {}
        self.cells: Dict[Tuple[int, int], QtWidgets.QLabel] = {}

        # 좌상단 빈 셀
        self.grid.addWidget(QtWidgets.QLabel(""), 0, 0)

        # 요일 헤더(열)
        for c, day in enumerate(self.config.days, start=1):
            lbl = QtWidgets.QLabel(day.label)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setProperty("role", "dayHeader")
            self.grid.addWidget(lbl, 0, c)
            self.day_headers[c] = lbl

        # 교시 헤더(행) 및 셀
        for r, p in enumerate(self.config.periods, start=1):
            ph = QtWidgets.QLabel(p.label)
            ph.setAlignment(Qt.AlignCenter)
            ph.setProperty("role", "periodHeader")
            self.grid.addWidget(ph, r, 0)
            self.period_headers[r] = ph

            for c, _day in enumerate(self.config.days, start=1):
                cell = QtWidgets.QLabel()
                cell.setAlignment(Qt.AlignCenter)
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
        edit_cfg = menu.addAction("시간/요일/시간표 설정")
        if edit_cfg is not None:
            edit_cfg.triggered.connect(self.open_edit_config)
        menu.addSeparator()
        exit_act = menu.addAction("종료")
        if exit_act is not None:
            app = QtWidgets.QApplication.instance()
            if app is not None:
                exit_act.triggered.connect(app.quit)
        menu.exec_(self.mapToGlobal(pos))

    def open_edit_config(self):
        dlg = EditConfigDialog(self, config=self.config)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            self.config = dlg.get_updated_config()
            save_config(self.config)
            self._rebuild_grid()
            self._update_current_period()

    def _rebuild_grid(self):
        # 기존 위젯 제거
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item is None:
                continue
            w = item.widget()
            if w is not None:
                w.setParent(None)
        self.day_headers.clear()
        self.period_headers.clear()
        self.cells.clear()

        # 좌상단 빈 셀
        self.grid.addWidget(QtWidgets.QLabel(""), 0, 0)

        # 요일 헤더
        for c, day in enumerate(self.config.days, start=1):
            lbl = QtWidgets.QLabel(day.label)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setProperty("role", "dayHeader")
            self.grid.addWidget(lbl, 0, c)
            self.day_headers[c] = lbl

        # 교시 헤더와 셀
        for r, p in enumerate(self.config.periods, start=1):
            ph = QtWidgets.QLabel(p.label)
            ph.setAlignment(Qt.AlignCenter)
            ph.setProperty("role", "periodHeader")
            self.grid.addWidget(ph, r, 0)
            self.period_headers[r] = ph

            for c, _day in enumerate(self.config.days, start=1):
                cell = QtWidgets.QLabel()
                cell.setAlignment(Qt.AlignCenter)
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
        # 시간표 채우기
        day_index = {d.id: idx for idx, d in enumerate(self.config.days, start=1)}
        period_index = {p.id: idx for idx, p in enumerate(self.config.periods, start=1)}

        for d in self.config.days:
            for pid, subject in (self.config.timetable.get(d.id, {}) or {}).items():
                r = period_index.get(pid)
                c = day_index.get(d.id)
                if r and c and (r, c) in self.cells:
                    self.cells[(r, c)].setText(str(subject))

    def _update_current_period(self):
        # 오늘 요일 ID 계산 (1=Mon ... 7=Sun)
        weekday = QtCore.QDate.currentDate().dayOfWeek()
        day_map = {1: "mon", 2: "tue", 3: "wed", 4: "thu", 5: "fri", 6: "sat", 7: "sun"}
        today_id = day_map.get(weekday, None)
        if today_id is None:
            return

        now = QtCore.QTime.currentTime()
        current_pid = None

        valid_day_ids = {d.id for d in self.config.days}
        if today_id in valid_day_ids:
            current_pid = get_current_period(self.config, today_id, now)

        day_index = {d.id: idx for idx, d in enumerate(self.config.days, start=1)}
        period_index = {p.id: idx for idx, p in enumerate(self.config.periods, start=1)}

        for (_r, _c), w in self.cells.items():
            w.setProperty("current", False)
            st = w.style()
            if st is not None:
                st.unpolish(w)
                st.polish(w)

        if current_pid is not None and today_id in day_index:
            r = period_index.get(current_pid)
            c = day_index.get(today_id)
            if r and c and (r, c) in self.cells:
                w = self.cells[(r, c)]
                w.setProperty("current", True)
                st = w.style()
                if st is not None:
                    st.unpolish(w)
                    st.polish(w)

    # 드래그/리사이즈
    def mousePressEvent(self, a0):
        if a0 and a0.button() == Qt.LeftButton:
            pos = a0.pos()
            if pos.x() >= self.rect().width() - 20 and pos.y() >= self.rect().height() - 20:
                self.resizing = True
                self.resize_start = a0.globalPos()
                self.initial_size = self.size()
                self.setCursor(Qt.SizeFDiagCursor)
            else:
                self.dragging = True
                self.drag_start = a0.globalPos() - self.frameGeometry().topLeft()
                self.setCursor(Qt.ClosedHandCursor)
        super().mousePressEvent(a0)

    def mouseMoveEvent(self, a0):
        if a0 is None:
            super().mouseMoveEvent(a0)
            return
        if self.resizing:
            if self.resize_start is None:
                return
            diff = a0.globalPos() - self.resize_start
            new_w = max(self.minimumWidth(), self.initial_size.width() + diff.x())
            new_h = max(self.minimumHeight(), self.initial_size.height() + diff.y())
            self.resize(new_w, new_h)
        elif self.dragging and a0 and a0.buttons() == Qt.LeftButton and not self.config.ui.position.lock:
            if self.drag_start is None:
                return
            self.move(a0.globalPos() - self.drag_start)
        else:
            if a0 and a0.pos().x() >= self.rect().width() - 20 and a0.pos().y() >= self.rect().height() - 20:
                self.setCursor(Qt.SizeFDiagCursor)
            else:
                self.setCursor(Qt.ArrowCursor)
        super().mouseMoveEvent(a0)

    def mouseReleaseEvent(self, a0):
        if a0 and a0.button() == Qt.LeftButton:
            self.resizing = False
            self.dragging = False
            self.setCursor(Qt.ArrowCursor)
            # 위치 저장
            pos = self.pos()
            size = self.size()
            self.config.ui.position.x = pos.x()
            self.config.ui.position.y = pos.y()
            self.config.ui.position.width = size.width()
            self.config.ui.position.height = size.height()
            save_config(self.config)
        super().mouseReleaseEvent(a0)

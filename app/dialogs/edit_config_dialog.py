from __future__ import annotations

import re
import copy
from PyQt5 import QtWidgets, QtCore

from core.model import AppConfig, Day, Period


TIME_RE = re.compile(r"^([01]?\d|2[0-3]):[0-5]\d$")


class EditConfigDialog(QtWidgets.QDialog):
    """스키마 v2 기반: 요일/교시/시간 편집 스켈레톤."""

    def __init__(self, parent=None, config: AppConfig | None = None):
        super().__init__(parent)
        self.setWindowTitle("구성 편집")
        self.setModal(True)
        self.resize(640, 480)

        # 작업용 복사본 (취소 시 원본 보존)
        self._original = config
        self._working: AppConfig = copy.deepcopy(config)

        self.tabs = QtWidgets.QTabWidget(self)
        self._init_days_tab()
        self._init_periods_tab()

        btn_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel, parent=self
        )
        btn_box.accepted.connect(self._on_accept)
        btn_box.rejected.connect(self.reject)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.tabs)
        layout.addWidget(btn_box)
        self.setLayout(layout)

    # --- Days tab ---
    def _init_days_tab(self):
        w = QtWidgets.QWidget()
        vbox = QtWidgets.QVBoxLayout(w)

        self.days_table = QtWidgets.QTableWidget()
        self.days_table.setColumnCount(2)
        self.days_table.setHorizontalHeaderLabels(["id", "label"])
        self.days_table.horizontalHeader().setStretchLastSection(True)
        vbox.addWidget(self.days_table)

        btns = QtWidgets.QHBoxLayout()
        add_btn = QtWidgets.QPushButton("추가")
        del_btn = QtWidgets.QPushButton("삭제")
        add_btn.clicked.connect(self._add_day)
        del_btn.clicked.connect(self._del_day)
        btns.addWidget(add_btn)
        btns.addWidget(del_btn)
        btns.addStretch(1)
        vbox.addLayout(btns)

        self.tabs.addTab(w, "요일")
        self._reload_days_table()

    def _reload_days_table(self):
        data = self._working.days
        self.days_table.setRowCount(len(data))
        for r, d in enumerate(data):
            self.days_table.setItem(r, 0, QtWidgets.QTableWidgetItem(d.id))
            self.days_table.setItem(r, 1, QtWidgets.QTableWidgetItem(d.label))

    def _add_day(self):
        r = self.days_table.rowCount()
        self.days_table.insertRow(r)
        self.days_table.setItem(r, 0, QtWidgets.QTableWidgetItem(""))
        self.days_table.setItem(r, 1, QtWidgets.QTableWidgetItem(""))

    def _del_day(self):
        rows = sorted({i.row() for i in self.days_table.selectedIndexes()}, reverse=True)
        for r in rows:
            self.days_table.removeRow(r)

    # --- Periods tab ---
    def _init_periods_tab(self):
        w = QtWidgets.QWidget()
        vbox = QtWidgets.QVBoxLayout(w)

        self.periods_table = QtWidgets.QTableWidget()
        self.periods_table.setColumnCount(4)
        self.periods_table.setHorizontalHeaderLabels(["id", "label", "start(HH:MM)", "end(HH:MM)"])
        self.periods_table.horizontalHeader().setStretchLastSection(True)
        vbox.addWidget(self.periods_table)

        btns = QtWidgets.QHBoxLayout()
        add_btn = QtWidgets.QPushButton("추가")
        del_btn = QtWidgets.QPushButton("삭제")
        add_btn.clicked.connect(self._add_period)
        del_btn.clicked.connect(self._del_period)
        btns.addWidget(add_btn)
        btns.addWidget(del_btn)
        btns.addStretch(1)
        vbox.addLayout(btns)

        self.tabs.addTab(w, "교시/시간")
        self._reload_periods_table()

    def _reload_periods_table(self):
        data = self._working.periods
        self.periods_table.setRowCount(len(data))
        for r, p in enumerate(data):
            self.periods_table.setItem(r, 0, QtWidgets.QTableWidgetItem(p.id))
            self.periods_table.setItem(r, 1, QtWidgets.QTableWidgetItem(p.label))
            self.periods_table.setItem(r, 2, QtWidgets.QTableWidgetItem(p.start))
            self.periods_table.setItem(r, 3, QtWidgets.QTableWidgetItem(p.end))

    def _add_period(self):
        r = self.periods_table.rowCount()
        self.periods_table.insertRow(r)
        for c in range(4):
            self.periods_table.setItem(r, c, QtWidgets.QTableWidgetItem(""))

    def _del_period(self):
        rows = sorted({i.row() for i in self.periods_table.selectedIndexes()}, reverse=True)
        for r in rows:
            self.periods_table.removeRow(r)

    # --- Accept ---
    def _on_accept(self):
        # collect days
        days: list[Day] = []
        day_ids = set()
        for r in range(self.days_table.rowCount()):
            id_item = self.days_table.item(r, 0)
            label_item = self.days_table.item(r, 1)
            d_id = (id_item.text().strip() if id_item else "")
            d_label = (label_item.text().strip() if label_item else "")
            if not d_id or not d_label:
                QtWidgets.QMessageBox.warning(self, "검증 오류", "요일의 id와 label은 비워둘 수 없습니다.")
                return
            if d_id in day_ids:
                QtWidgets.QMessageBox.warning(self, "검증 오류", f"요일 id 중복: {d_id}")
                return
            day_ids.add(d_id)
            days.append(Day(id=d_id, label=d_label))

        # collect periods
        periods: list[Period] = []
        period_ids = set()
        for r in range(self.periods_table.rowCount()):
            id_item = self.periods_table.item(r, 0)
            label_item = self.periods_table.item(r, 1)
            start_item = self.periods_table.item(r, 2)
            end_item = self.periods_table.item(r, 3)
            p_id = (id_item.text().strip() if id_item else "")
            p_label = (label_item.text().strip() if label_item else "")
            p_start = (start_item.text().strip() if start_item else "")
            p_end = (end_item.text().strip() if end_item else "")
            if not p_id or not p_label:
                QtWidgets.QMessageBox.warning(self, "검증 오류", "교시의 id와 label은 비워둘 수 없습니다.")
                return
            if p_id in period_ids:
                QtWidgets.QMessageBox.warning(self, "검증 오류", f"교시 id 중복: {p_id}")
                return
            if not TIME_RE.match(p_start) or not TIME_RE.match(p_end):
                QtWidgets.QMessageBox.warning(self, "검증 오류", f"시간 형식이 올바르지 않습니다: {p_start}~{p_end}")
                return
            period_ids.add(p_id)
            periods.append(Period(id=p_id, label=p_label, start=p_start, end=p_end))

        # apply to working config
        self._working.days = days
        self._working.periods = periods

        # 성공
        self.accept()

    def get_updated_config(self) -> AppConfig:
        return self._working



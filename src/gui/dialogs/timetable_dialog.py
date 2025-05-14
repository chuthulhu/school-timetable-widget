from PyQt5 import QtWidgets, QtCore

# 다중행 편집을 위한 커스텀 delegate
class MultiLineDelegate(QtWidgets.QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QtWidgets.QTextEdit(parent)
        editor.setAcceptRichText(False)  # 순수 텍스트만 입력
        return editor

    def setEditorData(self, editor, index):
        text = index.model().data(index, QtCore.Qt.EditRole)
        editor.setPlainText(text)
    
    def setModelData(self, editor, model, index):
        text = editor.toPlainText()
        model.setData(index, text, QtCore.Qt.EditRole)
    
    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

class TimetableEditDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent, QtCore.Qt.WindowStaysOnTopHint)
        self.parent = parent
        self.settings_manager = parent.settings_manager
        self.setWindowTitle("시간표 편집")
        self.setMinimumHeight(400)
        
        # 현재 시간표 데이터 복사본 사용
        self.timetable_data = {}
        for day_idx, day in enumerate(['월', '화', '수', '목', '금']):
            self.timetable_data[day] = {}
            for period in range(1, 8):  # 1~7교시
                value = self.settings_manager.timetable_data.get(day, {}).get(str(period), "")
                self.timetable_data[day][str(period)] = value
                
        self.setup_ui()
    
    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout()
        
        # 설명 레이블
        info_label = QtWidgets.QLabel("각 요일과 교시에 맞는 과목을 입력하세요. 다중 교시 블록은 '합치기' 버튼을 사용하세요.")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # 툴바 추가
        toolbar = QtWidgets.QToolBar()
        merge_action = toolbar.addAction("선택 셀 합치기")
        merge_action.triggered.connect(self.merge_selected_cells)
        split_action = toolbar.addAction("셀 나누기")
        split_action.triggered.connect(self.split_selected_cell)
        layout.addWidget(toolbar)
        
        self.table = QtWidgets.QTableWidget(7, 5)  # 7행(교시), 5열(요일)
        self.table.setHorizontalHeaderLabels(['월', '화', '수', '목', '금'])
        self.table.setVerticalHeaderLabels([f"{i}교시" for i in range(1, 8)])
        
        # 테이블 셀 크기 조정
        header = self.table.horizontalHeader()
        for i in range(header.count()):
            header.setSectionResizeMode(i, QtWidgets.QHeaderView.Stretch)
        
        # 셀 선택 모드 변경
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.ContiguousSelection)
        
        # 기존 데이터로 테이블 채우기
        for day_idx, day in enumerate(['월', '화', '수', '목', '금']):
            for period in range(1, 8):
                item = QtWidgets.QTableWidgetItem(self.timetable_data.get(day, {}).get(str(period), ""))
                item.setTextAlignment(QtCore.Qt.AlignCenter)
                self.table.setItem(period-1, day_idx, item)
        
        # 다중행 입력을 위한 delegate 적용
        delegate = MultiLineDelegate(self.table)
        self.table.setItemDelegate(delegate)
        
        # 블록 교시 표시
        self.apply_cell_spans()

        layout.addWidget(self.table)
        self.table.resizeRowsToContents()
        
        button_layout = QtWidgets.QHBoxLayout()
        save_btn = QtWidgets.QPushButton("저장")
        save_btn.clicked.connect(self.save_timetable)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QtWidgets.QPushButton("취소")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def merge_selected_cells(self):
        """선택된 셀 합치기"""
        # 선택된 범위 가져오기
        selected_ranges = self.table.selectedRanges()
        if not selected_ranges:
            return
        
        for cell_range in selected_ranges:
            # 단일 열에서만 합치기 가능 (같은 요일의 여러 교시)
            if cell_range.leftColumn() != cell_range.rightColumn():
                QtWidgets.QMessageBox.warning(self, "알림", "같은 요일의 인접한 교시만 합칠 수 있습니다.")
                continue
            
            # 첫 번째 셀의 내용을 사용
            top_row = cell_range.topRow()
            col = cell_range.leftColumn()
            span_rows = cell_range.rowCount()
            
            # 이미 합쳐진 셀이 있는지 확인
            has_span = False
            for row in range(top_row, top_row + span_rows):
                if self.table.rowSpan(row, col) > 1 or self.table.rowSpan(row, col) == 0:
                    has_span = True
                    break
            
            if has_span:
                QtWidgets.QMessageBox.warning(self, "알림", "이미 합쳐진 셀이 포함되어 있습니다.")
                continue
            
            # 첫 번째 셀의 내용 가져오기
            first_item = self.table.item(top_row, col)
            content = first_item.text() if first_item else ""
            
            # 셀 병합
            self.table.setSpan(top_row, col, span_rows, 1)
            
            # 내용 설정
            self.table.setItem(top_row, col, QtWidgets.QTableWidgetItem(content))
            self.table.item(top_row, col).setTextAlignment(QtCore.Qt.AlignCenter)
    
    def split_selected_cell(self):
        """합쳐진 셀 분할"""
        # 선택된 셀 가져오기
        selected_items = self.table.selectedItems()
        if not selected_items:
            return
        
        for item in selected_items:
            row = item.row()
            col = self.table.column(item)
            
            # 현재 스팬 확인
            row_span = self.table.rowSpan(row, col)
            
            if row_span <= 1:
                continue  # 합쳐진 셀이 아님
            
            # 텍스트 내용 저장
            content = item.text()
            
            # 스팬 제거
            self.table.setSpan(row, col, 1, 1)
            
            # 분할된 각 셀에 내용 설정
            for r in range(row, row + row_span):
                self.table.setItem(r, col, QtWidgets.QTableWidgetItem(content if r == row else ""))
                self.table.item(r, col).setTextAlignment(QtCore.Qt.AlignCenter)
    
    def apply_cell_spans(self):
        """시간표 데이터에서 블록 교시 정보를 가져와 테이블에 적용"""
        # 블록 데이터 처리 (미구현: 시간표 데이터에 블록 정보 저장 형식 정의 필요)
        # 예시: 시간표에서 같은 요일의 연속 교시에 같은 과목이 있으면 자동으로 합치기
        for day_idx, day in enumerate(['월', '화', '수', '목', '금']):
            start_row = None
            current_subject = None
            span_count = 0
            
            # 각 교시 확인
            for period in range(1, 8):
                subject = self.timetable_data.get(day, {}).get(str(period), "")
                
                # 같은 과목이 계속되는 경우
                if subject and subject == current_subject:
                    span_count += 1
                
                # 다른 과목이거나 마지막 교시인 경우
                if (subject != current_subject or period == 7) and start_row is not None:
                    # 여러 교시에 걸친 경우만 처리
                    if span_count > 1:
                        # 마지막 같은 과목인 경우 포함
                        if period == 7 and subject == current_subject:
                            self.table.setSpan(start_row-1, day_idx, span_count+1, 1)
                        else:
                            self.table.setSpan(start_row-1, day_idx, span_count, 1)
                    
                    # 다음 블록 시작
                    start_row = period if subject else None
                    current_subject = subject
                    span_count = 1
                
                # 새로운 과목 시작
                elif subject and current_subject is None:
                    start_row = period
                    current_subject = subject
                    span_count = 1
                
                # 빈 셀인 경우
                elif not subject:
                    start_row = None
                    current_subject = None
                    span_count = 0
    
    def save_timetable(self):
        """테이블에서 데이터 가져와서 저장"""
        updated_data = {}
        
        # 각 요일에 대해
        for day_idx, day in enumerate(['월', '화', '수', '목', '금']):
            updated_data[day] = {}
            
            # 각 교시에 대해
            for period in range(1, 8):
                row = period - 1
                
                # 이 셀이 표시되는지 확인 (병합된 셀의 일부가 아닌 경우만)
                is_visible_cell = self.table.rowSpan(row, day_idx) > 0
                
                if is_visible_cell:
                    # 병합된 셀이면 첫 번째 셀의 내용 가져오기
                    span_row = row
                    while span_row > 0 and self.table.rowSpan(span_row - 1, day_idx) > 1:
                        span_row -= 1
                    
                    item = self.table.item(span_row, day_idx)
                    text = item.text() if item else ""
                    updated_data[day][str(period)] = text
                else:
                    # 병합된 셀 내부는 상위 셀과 같은 내용으로 설정
                    for check_row in range(row, -1, -1):
                        if self.table.rowSpan(check_row, day_idx) > 0:
                            span_row = check_row
                            item = self.table.item(span_row, day_idx)
                            text = item.text() if item else ""
                            updated_data[day][str(period)] = text
                            break
        
        # 설정 관리자를 통해 시간표 데이터 업데이트
        self.settings_manager.update_timetable_data(updated_data)
        
        # 부모 위젯에 시간표 갱신 요청
        self.parent.update_timetable_display()
        self.accept()
    
    # 대화상자 크기에 맞춰 테이블 셀 크기를 조정하는 함수
    def adjust_table_cell_sizes(self):
        row_count = self.table.rowCount()
        col_count = self.table.columnCount()
        available_width = self.table.viewport().width()
        available_height = self.table.viewport().height()
        # 셀 크기는 가로, 세로 중 더 작은 값을 사용하여 정사각형으로 설정
        cell_size = min(available_width / col_count, available_height / row_count)
        for row in range(row_count):
            self.table.setRowHeight(row, int(cell_size))
        for col in range(col_count):
            self.table.setColumnWidth(col, int(cell_size))
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.adjust_table_cell_sizes()

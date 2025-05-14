from PyQt5 import QtWidgets, QtCore

class TimeRangeDialog(QtWidgets.QDialog):
    """시간 설정 다이얼로그 클래스"""
    def __init__(self, parent=None):
        super().__init__(parent, QtCore.Qt.WindowStaysOnTopHint)
        self.parent = parent
        self.settings_manager = parent.settings_manager
        self.setWindowTitle("교시별 시간 설정")
        self.setup_ui()
    
    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout()
        
        # 시간 설정 안내
        info_label = QtWidgets.QLabel("각 교시의 시작 시간과 종료 시간을 설정하세요.")
        layout.addWidget(info_label)
        
        # 시간 설정 폼
        form_layout = QtWidgets.QFormLayout()
        self.time_widgets = {}
        
        for period in range(1, 8):  # 1교시부터 7교시까지
            # 시간 범위 설정을 위한 레이아웃
            period_layout = QtWidgets.QHBoxLayout()
            
            # 시작 시간
            start_time = self.settings_manager.time_ranges.get(period, {}).get("start", QtCore.QTime(9, 0))
            start_time_edit = QtWidgets.QTimeEdit(start_time)
            start_time_edit.setDisplayFormat("HH:mm")
            period_layout.addWidget(QtWidgets.QLabel("시작:"))
            period_layout.addWidget(start_time_edit)
            
            # 간격 추가
            period_layout.addSpacing(10)
            
            # 종료 시간
            end_time = self.settings_manager.time_ranges.get(period, {}).get("end", QtCore.QTime(9, 50))
            end_time_edit = QtWidgets.QTimeEdit(end_time)
            end_time_edit.setDisplayFormat("HH:mm")
            period_layout.addWidget(QtWidgets.QLabel("종료:"))
            period_layout.addWidget(end_time_edit)
            
            form_layout.addRow(f"{period}교시:", period_layout)
            
            # 위젯 저장
            self.time_widgets[period] = {
                "start": start_time_edit,
                "end": end_time_edit
            }
        
        layout.addLayout(form_layout)
        
        # 버튼 레이아웃
        button_layout = QtWidgets.QHBoxLayout()
        
        save_btn = QtWidgets.QPushButton("저장")
        save_btn.clicked.connect(self.save_time_ranges)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QtWidgets.QPushButton("취소")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def save_time_ranges(self):
        # 설정된 시간 범위를 설정 관리자에 저장
        for period, widgets in self.time_widgets.items():
            start_time = widgets["start"].time()
            end_time = widgets["end"].time()
            
            self.settings_manager.time_ranges[period] = {
                "start": start_time,
                "end": end_time
            }
        
        # 설정을 파일에 저장
        self.settings_manager.save_time_settings()
        
        # 설정을 저장하고 다이얼로그 닫기
        self.accept()

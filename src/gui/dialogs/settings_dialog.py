from PyQt5 import QtWidgets, QtGui, QtCore
from ..components.color_button import ColorButton, FontComboBox
from ..components.theme_selector import ThemeSelector
import logging

# 로거 설정
logger = logging.getLogger(__name__)

class SettingsDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent, QtCore.Qt.WindowStaysOnTopHint)
        self.parent = parent
        self.settings_manager = parent.settings_manager
        self.setWindowTitle("설정")
        self.setStyleSheet("background-color: white;")  # 배경색을 흰색으로 고정
        self.setup_ui()
    
    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout()
        
        # 탭 위젯 생성
        self.tab_widget = QtWidgets.QTabWidget()
        self.tab_widget.setStyleSheet("QTabBar::tab { padding: 8px 16px; }")
        
        # === 테마 탭 ===
        self.setup_theme_tab()
        
        # === 색상 탭 ===
        self.setup_color_tab()
        
        # === 폰트 탭 ===
        self.setup_font_tab()
        
        # === 알림 탭 ===
        self.setup_notification_tab()
        
        # === 위젯 크기 탭 ===
        self.setup_widget_size_tab()
        
        # 탭 위젯 추가
        layout.addWidget(self.tab_widget)
        
        # 버튼 영역
        buttons_layout = QtWidgets.QHBoxLayout()
        
        self.apply_btn = QtWidgets.QPushButton("적용")
        self.apply_btn.clicked.connect(self.apply_settings)
        buttons_layout.addWidget(self.apply_btn)
        
        self.ok_btn = QtWidgets.QPushButton("확인")
        self.ok_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(self.ok_btn)
        
        # 취소 버튼 추가
        self.cancel_btn = QtWidgets.QPushButton("취소")
        self.cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(buttons_layout)
        self.setLayout(layout)
        
        # 설정 컨트롤 초기값 로드
        self.update_controls_from_settings()
    
    def setup_theme_tab(self):
        """테마 설정 탭 구성"""
        theme_tab = QtWidgets.QWidget()
        theme_layout = QtWidgets.QVBoxLayout()
        
        # 테마 설명
        desc_label = QtWidgets.QLabel("테마를 선택하면 미리 정의된 색상 및 투명도 설정이 적용됩니다.")
        desc_label.setWordWrap(True)
        theme_layout.addWidget(desc_label)
        
        # 테마 선택기 컴포넌트 추가
        self.theme_selector = ThemeSelector(self)
        self.theme_selector.themeChanged.connect(self.on_theme_changed)
        theme_layout.addWidget(self.theme_selector)
        
        theme_layout.addStretch()
        theme_tab.setLayout(theme_layout)
        self.tab_widget.addTab(theme_tab, "테마")
    
    def setup_color_tab(self):
        """색상 설정 탭 구성"""
        color_tab = QtWidgets.QWidget()
        color_layout = QtWidgets.QVBoxLayout()
        
        # 색상 설정 그룹
        color_group = QtWidgets.QGroupBox("색상 설정")
        color_form_layout = QtWidgets.QFormLayout()
        
        # 모든 색상 버튼 설정
        self.header_bg_btn = ColorButton(self.settings_manager.header_bg_color, self)
        color_form_layout.addRow("헤더 배경색:", self.header_bg_btn)
        
        self.header_text_btn = ColorButton(self.settings_manager.header_text_color, self)
        color_form_layout.addRow("헤더 텍스트색:", self.header_text_btn)
        
        self.cell_bg_btn = ColorButton(self.settings_manager.cell_bg_color, self)
        color_form_layout.addRow("셀 배경색:", self.cell_bg_btn)
        
        self.cell_text_btn = ColorButton(self.settings_manager.cell_text_color, self)
        color_form_layout.addRow("셀 텍스트색:", self.cell_text_btn)
        
        self.current_period_btn = ColorButton(self.settings_manager.current_period_color, self)
        color_form_layout.addRow("현재 교시 강조색:", self.current_period_btn)
        
        self.border_btn = ColorButton(self.settings_manager.border_color, self)
        color_form_layout.addRow("테두리색:", self.border_btn)
        
        color_group.setLayout(color_form_layout)
        color_layout.addWidget(color_group)
        
        # 투명도 설정 그룹
        opacity_group = QtWidgets.QGroupBox("투명도 설정")
        opacity_layout = QtWidgets.QFormLayout()
        
        # 투명도 슬라이더 생성 유틸리티 함수
        def create_opacity_slider_with_label(initial_value):
            slider_layout = QtWidgets.QHBoxLayout()
            slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
            slider.setRange(0, 100)  # 0-100% 범위로 변경
            slider.setValue(int(initial_value * 100 / 255))  # 0-255 값을 0-100%로 변환
            slider_layout.addWidget(slider, 7)  # 슬라이더에 더 많은 공간 할당
            # 현재 값 표시 레이블
            value_label = QtWidgets.QLabel(f"{slider.value()}%")
            value_label.setMinimumWidth(40)
            value_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            slider_layout.addWidget(value_label, 1)
            # 슬라이더 값이 변경될 때 레이블 업데이트
            slider.valueChanged.connect(lambda val: value_label.setText(f"{val}%"))
            
            return slider_layout, slider
        
        # 각 투명도 슬라이더 생성
        header_slider_layout, self.header_opacity = create_opacity_slider_with_label(self.settings_manager.header_opacity)
        opacity_layout.addRow("헤더 투명도:", header_slider_layout)
        
        cell_slider_layout, self.cell_opacity = create_opacity_slider_with_label(self.settings_manager.cell_opacity)
        opacity_layout.addRow("셀 투명도:", cell_slider_layout)
        
        current_period_slider_layout, self.current_period_opacity = create_opacity_slider_with_label(self.settings_manager.current_period_opacity)
        opacity_layout.addRow("현재 교시 투명도:", current_period_slider_layout)
        
        border_slider_layout, self.border_opacity = create_opacity_slider_with_label(self.settings_manager.border_opacity)
        opacity_layout.addRow("테두리 투명도:", border_slider_layout)
        
        opacity_group.setLayout(opacity_layout)
        color_layout.addWidget(opacity_group)
        
        color_layout.addStretch()
        color_tab.setLayout(color_layout)
        self.tab_widget.addTab(color_tab, "색상")
        
    def setup_font_tab(self):
        """폰트 설정 탭 구성"""
        font_tab = QtWidgets.QWidget()
        font_layout = QtWidgets.QVBoxLayout()
        
        # 헤더 폰트 설정 그룹
        header_font_group = QtWidgets.QGroupBox("헤더 폰트 설정")
        header_font_layout = QtWidgets.QFormLayout()
        
        # 헤더 폰트 선택 콤보박스
        self.header_font_combo = FontComboBox(self.settings_manager.header_font_family, self)
        header_font_layout.addRow("헤더 폰트:", self.header_font_combo)
        
        # 헤더 폰트 크기 선택 스핀박스
        self.header_font_size = QtWidgets.QSpinBox()
        self.header_font_size.setRange(6, 24)
        self.header_font_size.setValue(self.settings_manager.header_font_size)
        header_font_layout.addRow("헤더 폰트 크기:", self.header_font_size)
        
        header_font_group.setLayout(header_font_layout)
        font_layout.addWidget(header_font_group)
        
        # 셀 폰트 설정 그룹
        cell_font_group = QtWidgets.QGroupBox("셀 폰트 설정")
        cell_font_layout = QtWidgets.QFormLayout()
        
        # 셀 폰트 선택 콤보박스
        self.cell_font_combo = FontComboBox(self.settings_manager.cell_font_family, self)
        cell_font_layout.addRow("셀 폰트:", self.cell_font_combo)
        
        # 셀 폰트 크기 선택 스핀박스
        self.cell_font_size = QtWidgets.QSpinBox()
        self.cell_font_size.setRange(6, 24)
        self.cell_font_size.setValue(self.settings_manager.cell_font_size)
        cell_font_layout.addRow("셀 폰트 크기:", self.cell_font_size)
        
        cell_font_group.setLayout(cell_font_layout)
        font_layout.addWidget(cell_font_group)
        
        # 폰트 미리보기
        preview_group = QtWidgets.QGroupBox("미리보기")
        preview_layout = QtWidgets.QVBoxLayout()
        
        # 헤더 미리보기
        self.header_font_preview = QtWidgets.QLabel("월 화 수 목 금")
        self.header_font_preview.setAlignment(QtCore.Qt.AlignCenter)
        self.header_font_preview.setStyleSheet("padding: 5px; background-color: #6464C8; color: white; border: 1px solid #CCCCCC;")
        preview_layout.addWidget(QtWidgets.QLabel("헤더 미리보기:"))
        preview_layout.addWidget(self.header_font_preview)
        
        # 셀 미리보기
        self.cell_font_preview = QtWidgets.QLabel("1교시: 국어\n2교시: 수학\n3교시: 영어")
        self.cell_font_preview.setAlignment(QtCore.Qt.AlignCenter)
        self.cell_font_preview.setStyleSheet("padding: 5px; background-color: white; color: black; border: 1px solid #CCCCCC;")
        preview_layout.addWidget(QtWidgets.QLabel("셀 미리보기:"))
        preview_layout.addWidget(self.cell_font_preview)
        
        preview_group.setLayout(preview_layout)
        font_layout.addWidget(preview_group)
        
        # 폰트 변경 시 미리보기 업데이트
        self.header_font_combo.currentFontChanged.connect(self.update_font_preview)
        self.header_font_size.valueChanged.connect(self.update_font_preview)
        self.cell_font_combo.currentFontChanged.connect(self.update_font_preview)
        self.cell_font_size.valueChanged.connect(self.update_font_preview)
        
        # 기존 폰트 설정 (호환성 유지)
        self.font_combo = self.header_font_combo
        self.font_size = self.header_font_size
        
        self.update_font_preview()  # 초기 미리보기 설정
        
        font_layout.addStretch()
        font_tab.setLayout(font_layout)
        self.tab_widget.addTab(font_tab, "폰트")
    
    def setup_notification_tab(self):
        """알림 설정 탭 구성"""
        notification_tab = QtWidgets.QWidget()
        notification_layout = QtWidgets.QVBoxLayout()
        
        # 알림 설정 그룹 추가
        notification_group = QtWidgets.QGroupBox("알림 설정")
        notification_form_layout = QtWidgets.QVBoxLayout()
        
        # 알림 사용 여부
        self.notification_enabled = QtWidgets.QCheckBox("교시 시작 알림 사용")
        self.notification_enabled.setChecked(self.parent.notification_manager.notification_enabled)
        notification_form_layout.addWidget(self.notification_enabled)
        
        # 다음 교시 예고 알림 사용 여부
        self.next_period_warning = QtWidgets.QCheckBox("다음 교시 예고 알림 사용")
        self.next_period_warning.setChecked(self.parent.notification_manager.next_period_warning)
        notification_form_layout.addWidget(self.next_period_warning)
        
        # 예고 시간 설정
        warning_layout = QtWidgets.QHBoxLayout()
        warning_layout.addWidget(QtWidgets.QLabel("예고 알림 시간:"))
        self.warning_minutes = QtWidgets.QSpinBox()
        self.warning_minutes.setRange(1, 10)
        self.warning_minutes.setValue(self.parent.notification_manager.warning_minutes)
        self.warning_minutes.setSuffix(" 분 전")
        warning_layout.addWidget(self.warning_minutes)
        warning_layout.addStretch()
        notification_form_layout.addLayout(warning_layout)
        
        notification_group.setLayout(notification_form_layout)
        notification_layout.addWidget(notification_group)
        notification_layout.addStretch()
        
        notification_tab.setLayout(notification_layout)
        self.tab_widget.addTab(notification_tab, "알림")
    
    def setup_widget_size_tab(self):
        """위젯 크기 및 위치 설정 탭 구성"""
        size_tab = QtWidgets.QWidget()
        size_layout = QtWidgets.QVBoxLayout()
        
        # 위젯 크기 설정 그룹
        size_group = QtWidgets.QGroupBox("위젯 크기 설정")
        size_form_layout = QtWidgets.QFormLayout()
        
        # 현재 위젯 크기 정보
        current_size = self.settings_manager.widget_size
        width = current_size.get("width", 400) if current_size else 400
        height = current_size.get("height", 300) if current_size else 300
        
        # 너비 및 높이 스핀박스 생성
        self.widget_width = QtWidgets.QSpinBox()
        self.widget_width.setRange(200, 800)  # 최소/최대 크기 제한
        self.widget_width.setValue(width)
        self.widget_width.setSuffix(" px")
        size_form_layout.addRow("너비:", self.widget_width)
        
        self.widget_height = QtWidgets.QSpinBox()
        self.widget_height.setRange(150, 600)  # 최소/최대 크기 제한
        self.widget_height.setValue(height)
        self.widget_height.setSuffix(" px")
        size_form_layout.addRow("높이:", self.widget_height)
        
        # 미리보기
        preview_group = QtWidgets.QGroupBox("미리보기")
        preview_layout = QtWidgets.QVBoxLayout()
        
        self.size_preview = QtWidgets.QFrame()
        self.size_preview.setFrameShape(QtWidgets.QFrame.Box)
        self.size_preview.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.size_preview.setMinimumHeight(100)
        self.size_preview.setStyleSheet("background-color: #F0F0F0;")
        
        # 미리보기 내부 라벨
        preview_inner_layout = QtWidgets.QVBoxLayout(self.size_preview)
        preview_label = QtWidgets.QLabel("시간표 위젯 크기 미리보기")
        preview_label.setAlignment(QtCore.Qt.AlignCenter)
        preview_inner_layout.addWidget(preview_label)
        
        preview_layout.addWidget(self.size_preview)
        preview_group.setLayout(preview_layout)
        
        # 크기 설정 그룹화 완료
        size_form_layout.addRow("", preview_group)
        size_group.setLayout(size_form_layout)
        
        # 위젯 위치 설정 그룹
        position_group = QtWidgets.QGroupBox("위젯 위치 설정")
        position_layout = QtWidgets.QVBoxLayout()
        
        # 위젯 위치 고정 옵션
        self.lock_position = QtWidgets.QCheckBox("위젯 위치 고정")
        self.lock_position.setChecked(self.settings_manager.is_position_locked)
        self.lock_position.setToolTip("체크하면 위젯의 위치가 고정되어 마우스로 이동할 수 없습니다.")
        position_layout.addWidget(self.lock_position)
        
        # 위치 초기화 버튼
        reset_position_btn = QtWidgets.QPushButton("위치 초기화")
        reset_position_btn.setToolTip("위젯 위치를 기본 위치(화면 왼쪽 상단)로 초기화합니다.")
        reset_position_btn.clicked.connect(self.reset_widget_position)
        position_layout.addWidget(reset_position_btn)
        
        position_group.setLayout(position_layout)
        
        # 위젯 크기 변경 시 미리보기 업데이트
        self.widget_width.valueChanged.connect(self.update_size_preview)
        self.widget_height.valueChanged.connect(self.update_size_preview)
        
        # 초기 미리보기 설정
        self.update_size_preview()
        
        # 레이아웃에 그룹 추가
        size_layout.addWidget(size_group)
        size_layout.addWidget(position_group)
        size_layout.addStretch()
        
        size_tab.setLayout(size_layout)
        self.tab_widget.addTab(size_tab, "크기/위치")
    
    def update_size_preview(self):
        """위젯 크기 미리보기 업데이트"""
        # 스케일 비율 (원래 크기의 1/3 정도로 표시)
        scale = 0.3
        scaled_width = int(self.widget_width.value() * scale)
        scaled_height = int(self.widget_height.value() * scale)
        
        # 미리보기 라벨 스타일 업데이트
        style = f"""
            QFrame {{
                min-width: {scaled_width}px;
                max-width: {scaled_width}px;
                min-height: {scaled_height}px;
                max-height: {scaled_height}px;
                background-color: #F0F0F0;
                border: 1px solid gray;
            }}
        """
        self.size_preview.setStyleSheet(style)
    
    def reset_widget_position(self):
        """위젯 위치를 기본값으로 초기화"""
        from utils.config import Config
        msg_box = QtWidgets.QMessageBox(self)
        msg_box.setWindowTitle("위치 초기화")
        msg_box.setText("위젯 위치를 화면 왼쪽 상단으로 초기화하시겠습니까?")
        msg_box.setIcon(QtWidgets.QMessageBox.Question)
        msg_box.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        
        if msg_box.exec_() == QtWidgets.QMessageBox.Yes:
            # 기본 위치 적용 (실제 초기화는 apply_settings에서 처리)
            default_pos = Config.DEFAULT_WINDOW_POSITION
            self.settings_manager.widget_position = {"x": default_pos[0], "y": default_pos[1]}
            QtWidgets.QMessageBox.information(self, "완료", "위치가 초기화되었습니다.\n적용 또는 확인 버튼을 누르면 반영됩니다.")
    
    def on_theme_changed(self, theme_name):
        """테마가 변경되었을 때 호출
        
        Args:
            theme_name: 선택된 테마 이름
        """
        # 테마가 변경되면 설정 대화상자의 컨트롤도 업데이트
        self.update_controls_from_settings()
        
        # 부모 위젯 스타일 갱신
        self.parent.update_styles()
    def update_controls_from_settings(self):
        """설정 매니저의 값으로 컨트롤 업데이트"""
        # 색상 버튼 업데이트
        self.header_bg_btn.color = self.settings_manager.header_bg_color
        self.header_bg_btn.updateStyleSheet()
        self.header_text_btn.color = self.settings_manager.header_text_color
        self.header_text_btn.updateStyleSheet()
        self.cell_bg_btn.color = self.settings_manager.cell_bg_color
        self.cell_bg_btn.updateStyleSheet()
        self.cell_text_btn.color = self.settings_manager.cell_text_color
        self.cell_text_btn.updateStyleSheet()
        self.current_period_btn.color = self.settings_manager.current_period_color
        self.current_period_btn.updateStyleSheet()
        self.border_btn.color = self.settings_manager.border_color
        self.border_btn.updateStyleSheet()
        
        # 투명도 슬라이더 업데이트
        self.header_opacity.setValue(int(self.settings_manager.header_opacity * 100 / 255))
        self.cell_opacity.setValue(int(self.settings_manager.cell_opacity * 100 / 255))
        self.current_period_opacity.setValue(int(self.settings_manager.current_period_opacity * 100 / 255))
        self.border_opacity.setValue(int(self.settings_manager.border_opacity * 100 / 255))
        
        # 폰트 설정 업데이트
        if hasattr(self, 'header_font_combo') and hasattr(self, 'cell_font_combo'):
            # 새로운 개별 폰트 설정 적용
            self.header_font_combo.setCurrentFont(QtGui.QFont(self.settings_manager.header_font_family))
            self.header_font_size.setValue(self.settings_manager.header_font_size)
            self.cell_font_combo.setCurrentFont(QtGui.QFont(self.settings_manager.cell_font_family))
            self.cell_font_size.setValue(self.settings_manager.cell_font_size)
        else:
            # 기존 단일 폰트 설정 호환성 유지
            self.font_combo.setCurrentFont(QtGui.QFont(self.settings_manager.font_family))
            self.font_size.setValue(self.settings_manager.font_size)
        self.update_font_preview()
        
    def update_font_preview(self):
        """폰트 미리보기 업데이트"""
        # 헤더 폰트 미리보기 업데이트
        if hasattr(self, 'header_font_combo') and hasattr(self, 'header_font_preview'):
            header_font = self.header_font_combo.currentFont()
            header_font.setPointSize(self.header_font_size.value())
            self.header_font_preview.setFont(header_font)
        
        # 셀 폰트 미리보기 업데이트
        if hasattr(self, 'cell_font_combo') and hasattr(self, 'cell_font_preview'):
            cell_font = self.cell_font_combo.currentFont()
            cell_font.setPointSize(self.cell_font_size.value())
            self.cell_font_preview.setFont(cell_font)
        
    def apply_settings(self):
        """현재 설정을 SettingsManager에 적용"""
        # 색상 설정 적용
        self.settings_manager.header_bg_color = self.header_bg_btn.color
        self.settings_manager.header_text_color = self.header_text_btn.color
        self.settings_manager.cell_bg_color = self.cell_bg_btn.color
        self.settings_manager.cell_text_color = self.cell_text_btn.color
        self.settings_manager.current_period_color = self.current_period_btn.color
        self.settings_manager.border_color = self.border_btn.color
        
        # 투명도 설정 적용 (0-100% -> 0-255)
        self.settings_manager.header_opacity = int(self.header_opacity.value() * 255 / 100)
        self.settings_manager.cell_opacity = int(self.cell_opacity.value() * 255 / 100)
        self.settings_manager.current_period_opacity = int(self.current_period_opacity.value() * 255 / 100)
        self.settings_manager.border_opacity = int(self.border_opacity.value() * 255 / 100)
        # 폰트 설정 적용
        if hasattr(self, 'header_font_combo') and hasattr(self, 'cell_font_combo'):
            # 개별 폰트 설정 저장
            self.settings_manager.header_font_family = self.header_font_combo.currentFont().family()
            self.settings_manager.header_font_size = self.header_font_size.value()
            self.settings_manager.cell_font_family = self.cell_font_combo.currentFont().family()
            self.settings_manager.cell_font_size = self.cell_font_size.value()
            
            # 기존 폰트 설정도 호환성을 위해 헤더 폰트로 유지
            self.settings_manager.font_family = self.header_font_combo.currentFont().family()
            self.settings_manager.font_size = self.header_font_size.value()
        else:
            # 기존 단일 폰트 설정 적용
            self.settings_manager.font_family = self.font_combo.currentFont().family()
            self.settings_manager.font_size = self.font_size.value()
        
        # 알림 설정 적용
        notification_manager = self.parent.notification_manager
        notification_manager.set_notification_enabled(self.notification_enabled.isChecked())
        notification_manager.set_next_period_warning(self.next_period_warning.isChecked())
        notification_manager.set_warning_minutes(self.warning_minutes.value())
        notification_manager.save_notification_settings()
        
        # 위젯 크기 및 위치 설정 적용
        try:
            # 이전 크기/위치 정보 백업
            old_size = self.settings_manager.widget_size.copy() if self.settings_manager.widget_size else {}
            old_position = self.settings_manager.widget_position.copy() if self.settings_manager.widget_position else {}
            
            # 새로운 크기 설정
            if hasattr(self, 'widget_width') and hasattr(self, 'widget_height'):
                new_size = {
                    "width": self.widget_width.value(),
                    "height": self.widget_height.value()
                }
                
                # 위치 고정 상태 업데이트
                if hasattr(self, 'lock_position'):
                    is_locked = self.lock_position.isChecked()
                    self.settings_manager.set_position_lock(is_locked)
                
                # 위젯 위치와 크기 정보 저장
                x = old_position.get('x', 100)
                y = old_position.get('y', 100)
                self.settings_manager.save_widget_position(x, y, new_size['width'], new_size['height'])
                
                # 부모 위젯 크기 업데이트 (값이 변경된 경우만)
                if (old_size.get('width') != new_size['width'] or 
                    old_size.get('height') != new_size['height']):
                    logger.info(f"위젯 크기 변경: {old_size} -> {new_size}")
                    self.parent.resize(new_size['width'], new_size['height'])
        except Exception as e:
            logger.error(f"위젯 크기 설정 적용 중 오류: {e}")
          # 설정 파일에 저장
        self.settings_manager.save_style_settings()
        
        # 부모 위젯 스타일 갱신
        self.parent.update_styles()
    
    def accept(self):
        """확인 버튼 클릭 시 설정을 적용하고 대화상자 닫기"""
        self.apply_settings()
        super().accept()


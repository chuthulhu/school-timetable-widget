"""
테마 선택 컴포넌트
- 미리 정의된 테마(라이트/다크) 선택 기능
- 테마 미리보기
- 사용자 정의 테마 지원
"""
from PyQt5 import QtWidgets, QtGui, QtCore
from utils.config import Config
from utils.settings_manager import SettingsManager
from utils.styling import hex_to_rgba

class ThemePreview(QtWidgets.QFrame):
    """테마 미리보기 위젯"""
    def __init__(self, theme_data, theme_name, parent=None):
        super().__init__(parent)
        self.theme_data = theme_data
        self.theme_name = theme_name
        self.setFixedSize(120, 80)
        self.setFrameShape(QtWidgets.QFrame.Box)
        self.setFrameShadow(QtWidgets.QFrame.Raised)
        self.setStyleSheet(f"border: 1px solid {theme_data['border_color']};")
        self.setup_ui()
    
    def setup_ui(self):
        """미리보기 UI 구성"""
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(1)
        
        # 테마 이름 레이블
        name_label = QtWidgets.QLabel(self.get_display_name())
        name_label.setAlignment(QtCore.Qt.AlignCenter)
        header_opacity = self.theme_data.get('header_opacity', 255)
        header_color_rgba = hex_to_rgba(self.theme_data['header_bg_color'], header_opacity)
        
        name_label.setStyleSheet(f"background-color: {header_color_rgba}; color: {self.theme_data['header_text_color']};")
        layout.addWidget(name_label)
        
        # 미리보기 그리드 (요일 + 교시)
        grid_frame = QtWidgets.QFrame()
        grid_layout = QtWidgets.QGridLayout(grid_frame)
        grid_layout.setContentsMargins(1, 1, 1, 1)
        grid_layout.setSpacing(2)
        
        # 요일 헤더
        for col, day in enumerate(['월', '화', '수']):
            day_label = QtWidgets.QLabel(day)
            day_label.setAlignment(QtCore.Qt.AlignCenter)
            day_label.setStyleSheet(f"background-color: {header_color_rgba}; color: {self.theme_data['header_text_color']}; font-size: 8px;")
            grid_layout.addWidget(day_label, 0, col)
        
        # 교시 (셀)
        cell_opacity = self.theme_data.get('cell_opacity', 255)
        cell_color_rgba = hex_to_rgba(self.theme_data['cell_bg_color'], cell_opacity)
        
        current_opacity = self.theme_data.get('current_period_opacity', 255)
        current_color_rgba = hex_to_rgba(self.theme_data['current_period_color'], current_opacity)
        
        for row in range(1, 3):  # 2개의 행만 미리보기
            for col in range(3):  # 3개의 열(요일)만 미리보기
                cell = QtWidgets.QLabel(f"{row}")
                cell.setAlignment(QtCore.Qt.AlignCenter)
                
                # 현재 교시 강조 (1행 2열)
                if row == 1 and col == 1:
                    cell.setStyleSheet(f"background-color: {current_color_rgba}; color: {self.theme_data['cell_text_color']}; font-size: 8px;")
                else:
                    cell.setStyleSheet(f"background-color: {cell_color_rgba}; color: {self.theme_data['cell_text_color']}; font-size: 8px;")
                
                grid_layout.addWidget(cell, row, col)
        
        layout.addWidget(grid_frame)
        self.setLayout(layout)
    
    def get_display_name(self):
        """테마명 표시용 문자열 반환"""
        if self.theme_name == Config.THEME_LIGHT:
            return "라이트 모드"
        elif self.theme_name == Config.THEME_DARK:
            return "다크 모드"
        elif self.theme_name == Config.THEME_CUSTOM:
            return "사용자 정의"
        return self.theme_name

class ThemeSelector(QtWidgets.QWidget):
    """테마 선택 위젯"""
    themeChanged = QtCore.pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings_manager = SettingsManager.get_instance()
        self.current_theme = self.settings_manager.theme
        self.setup_ui()
    
    def setup_ui(self):
        """테마 선택 UI 구성"""
        layout = QtWidgets.QVBoxLayout(self)
        
        # 설명 레이블
        title_label = QtWidgets.QLabel("테마 선택")
        title_label.setStyleSheet("font-size: 12px; font-weight: bold;")
        layout.addWidget(title_label)
        
        theme_layout = QtWidgets.QHBoxLayout()
        
        # 라이트 테마 미리보기
        light_theme = Config.THEMES[Config.THEME_LIGHT]
        self.light_preview = ThemePreview(light_theme, Config.THEME_LIGHT)
        self.light_preview.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.light_preview.mousePressEvent = lambda e: self.select_theme(Config.THEME_LIGHT)
        theme_layout.addWidget(self.light_preview)
        
        # 다크 테마 미리보기
        dark_theme = Config.THEMES[Config.THEME_DARK]
        self.dark_preview = ThemePreview(dark_theme, Config.THEME_DARK)
        self.dark_preview.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.dark_preview.mousePressEvent = lambda e: self.select_theme(Config.THEME_DARK)
        theme_layout.addWidget(self.dark_preview)
        
        # 사용자 정의 테마 미리보기 (현재 스타일을 사용)
        custom_theme = {
            "header_bg_color": self.settings_manager.header_bg_color,
            "header_text_color": self.settings_manager.header_text_color,
            "cell_bg_color": self.settings_manager.cell_bg_color,
            "cell_text_color": self.settings_manager.cell_text_color,
            "current_period_color": self.settings_manager.current_period_color,
            "border_color": self.settings_manager.border_color,
            "header_opacity": self.settings_manager.header_opacity,
            "cell_opacity": self.settings_manager.cell_opacity,
            "current_period_opacity": self.settings_manager.current_period_opacity,
            "border_opacity": self.settings_manager.border_opacity
        }
        
        self.custom_preview = ThemePreview(custom_theme, Config.THEME_CUSTOM)
        theme_layout.addWidget(self.custom_preview)
        
        layout.addLayout(theme_layout)
        
        # 테마 선택 상태 표시
        self.theme_label = QtWidgets.QLabel(f"현재 테마: {self.get_theme_display_name()}")
        layout.addWidget(self.theme_label)
        
        # 선택한 테마 하이라이트
        self.highlight_selected_theme()
        
        self.setLayout(layout)
    
    def select_theme(self, theme_name):
        """테마 선택 처리"""
        # 테마가 이미 선택된 경우 무시
        if self.current_theme == theme_name:
            return
            
        # 설정 관리자를 통해 테마 변경
        success = self.settings_manager.change_theme(theme_name)
        
        if success:
            self.current_theme = theme_name
            self.highlight_selected_theme()
            self.theme_label.setText(f"현재 테마: {self.get_theme_display_name()}")
            self.themeChanged.emit(theme_name)
    
    def highlight_selected_theme(self):
        """선택된 테마 강조 표시"""
        # 모든 테마 미리보기의 테두리 초기화
        self.light_preview.setStyleSheet("border: 1px solid #CCCCCC;")
        self.dark_preview.setStyleSheet("border: 1px solid #CCCCCC;")
        self.custom_preview.setStyleSheet("border: 1px solid #CCCCCC;")
        
        # 선택된 테마 강조
        selected_style = "border: 2px solid #3498db; border-radius: 3px;"
        if self.current_theme == Config.THEME_LIGHT:
            self.light_preview.setStyleSheet(selected_style)
        elif self.current_theme == Config.THEME_DARK:
            self.dark_preview.setStyleSheet(selected_style)
        elif self.current_theme == Config.THEME_CUSTOM:
            self.custom_preview.setStyleSheet(selected_style)
    
    def get_theme_display_name(self):
        """현재 테마의 표시용 이름 반환"""
        if self.current_theme == Config.THEME_LIGHT:
            return "라이트 모드"
        elif self.current_theme == Config.THEME_DARK:
            return "다크 모드"
        elif self.current_theme == Config.THEME_CUSTOM:
            return "사용자 정의"
        return self.current_theme

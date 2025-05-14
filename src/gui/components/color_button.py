from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import pyqtSignal # pyqtSignal 임포트

class ColorButton(QtWidgets.QPushButton):
    """색상 선택 버튼 클래스"""
    colorChanged = pyqtSignal(str) # 색상 변경 시그널

    def __init__(self, color, parent=None):
        super().__init__(parent)
        self.color = color
        self.setFixedSize(20, 20)
        # 색상 형식을 올바르게 적용
        self.updateStyleSheet()
        self.clicked.connect(self.choose_color)
    
    def updateStyleSheet(self):
        """색상에 맞게 버튼 스타일시트 업데이트"""
        # RGBA 형식으로 들어올 경우 처리
        if self.color.startswith("#") and len(self.color) > 7:
            # ARGB 형식인 경우 RGB로 변환
            rgb_color = self.color[3:] if len(self.color) == 9 else self.color
            self.setStyleSheet(f"background-color: {rgb_color}; border: 1px solid black;")
        else:
            # 일반적인 색상 포맷
            self.setStyleSheet(f"background-color: {self.color}; border: 1px solid black;")
    
    def choose_color(self):
        """색상 선택 대화상자 표시"""
        # 현재 색상을 QColor로 변환
        current_color = QtGui.QColor(self.color)
        
        # 색상 선택 대화상자 생성 및 설정
        color_dialog = QtWidgets.QColorDialog(current_color, self)
        color_dialog.setWindowTitle("색상 선택")
        color_dialog.setOption(QtWidgets.QColorDialog.ShowAlphaChannel)
        color_dialog.setOption(QtWidgets.QColorDialog.DontUseNativeDialog)  # 네이티브 대화상자 사용 안 함
        color_dialog.setStyleSheet("background-color: white;")  # 배경색을 흰색으로 설정
        
        # 대화상자 표시
        if color_dialog.exec_() == QtWidgets.QDialog.Accepted:
            color = color_dialog.currentColor()
            if color.isValid():
                self.color = color.name(QtGui.QColor.HexRgb) # #RRGGBB 형식으로 저장
                self.updateStyleSheet()
                self.colorChanged.emit(self.color) # 색상 변경 시그널 발생
                # # 부모 위젯에 변경 알림 (시그널 방식으로 대체)
                # if hasattr(self.parent(), 'apply_settings'):
                #     self.parent().apply_settings()


class FontComboBox(QtWidgets.QFontComboBox):
    """폰트 선택 콤보박스 클래스"""
    def __init__(self, current_font, parent=None):
        super().__init__(parent)
        self.setCurrentFont(QtGui.QFont(current_font))

from PyQt5.QtWidgets import QAction, QMenu, QSystemTrayIcon
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
import os
import sys

# 사용자 모듈
from utils.paths import resource_path
from utils.version import get_version_string

class TrayIcon(QSystemTrayIcon):
    def __init__(self, widget):
        super().__init__()
        self.widget = widget
        self.setup_tray()
        
    def setup_tray(self):
        # 아이콘 설정
        icon_path = resource_path("assets/app_icon.ico")
        if not os.path.exists(icon_path):
            # 기본 아이콘 사용 (패키지 내부)
            icon_path = resource_path("assets/icon.ico")
            if not os.path.exists(icon_path):
                # 그래도 없으면 Qt 기본 아이콘
                self.setIcon(QIcon.fromTheme("applications-education"))
            else:
                self.setIcon(QIcon(icon_path))
        else:
            self.setIcon(QIcon(icon_path))
            
        # 트레이 메뉴 설정
        menu = QMenu()
        
        # 보기 액션
        self.show_action = QAction("시간표 보기", menu)
        menu.addAction(self.show_action)
        
        # 구분선
        menu.addSeparator()
        
        # 버전 정보 표시 (클릭 불가능한 설명 텍스트)
        version_action = QAction(f"버전: {get_version_string()}", menu)
        version_action.setEnabled(False)  # 클릭 불가능하게 설정
        menu.addAction(version_action)
        
        # 구분선
        menu.addSeparator()
        
        # 종료 액션
        self.exit_action = QAction("종료", menu)
        menu.addAction(self.exit_action)
        
        # 메뉴 설정
        self.setContextMenu(menu)
        
        # 트레이 아이콘 클릭 시 메뉴 표시
        self.activated.connect(self.on_tray_icon_activated)
    
    def on_tray_icon_activated(self, reason):
        """트레이 아이콘 활성화 이벤트 처리"""
        if reason == QSystemTrayIcon.Trigger:
            # 클릭 시 위젯 표시/숨김 토글
            if self.widget.isVisible():
                self.widget.hide()
            else:
                self.widget.show()

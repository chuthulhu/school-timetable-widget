import platform
from PyQt5 import QtWidgets, QtCore, QtGui
import os
from utils.settings_manager import SettingsManager
from utils.paths import get_notification_settings_file_path
import json
import logging

class NotificationManager:
    """수업 시간 알림을 관리하는 클래스"""
    
    # 싱글톤 인스턴스
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """싱글톤 인스턴스 반환"""
        if cls._instance is None:
            cls._instance = NotificationManager()
        return cls._instance
    
    def __init__(self, parent=None):
        """알림 관리자 초기화"""
        # 이미 인스턴스가 있는지 확인
        if NotificationManager._instance is not None:
            raise Exception("NotificationManager는 싱글톤 클래스입니다. get_instance() 메서드를 사용하세요.")
            
        self.parent = parent
        self.system = platform.system()
        self.notification_enabled = True
        self.next_period_warning = True  # 다음 교시 예고
        self.warning_minutes = 5  # 수업 시작 5분 전 알림
        self.last_notified_period = None
        self.last_notified_warning = None
        
        # 설정 매니저 참조
        self.settings_manager = SettingsManager.get_instance()
        
        # 알림 설정 로드
        self.load_notification_settings()
        
    def set_notification_enabled(self, enabled):
        """알림 활성화 여부 설정"""
        self.notification_enabled = enabled
        self.save_notification_settings()
    
    def set_next_period_warning(self, enabled):
        """다음 교시 예고 알림 활성화 여부 설정"""
        self.next_period_warning = enabled
        self.save_notification_settings()
    
    def set_warning_minutes(self, minutes):
        """예고 시간(분) 설정"""
        self.warning_minutes = minutes
        self.save_notification_settings()
        
    def load_notification_settings(self):
        """알림 설정 로드"""
        try:
            file_path = get_notification_settings_file_path()
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    self.notification_enabled = settings.get("notification_enabled", True)
                    self.next_period_warning = settings.get("next_period_warning", True)
                    self.warning_minutes = settings.get("warning_minutes", 5)
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"알림 설정 로드 오류: {e}")
    
    def save_notification_settings(self):
        """알림 설정 저장"""
        try:
            file_path = get_notification_settings_file_path()
            settings = {
                "notification_enabled": self.notification_enabled,
                "next_period_warning": self.next_period_warning,
                "warning_minutes": self.warning_minutes
            }
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"알림 설정 저장 오류: {e}")
    
    def check_notifications(self, current_period, current_day_idx, timetable_data):
        """현재 교시에 대한 알림 확인
        
        Args:
            current_period: 현재 교시
            current_day_idx: 현재 요일 인덱스 (1=월요일, ..., 5=금요일)
            timetable_data: 시간표 데이터
        """
        if not self.notification_enabled:
            return
            
        # 새 교시로 변경되었고, 평일인 경우만 알림
        if current_period is not None and current_day_idx is not None:
            if current_period != self.last_notified_period:
                day_name = ['월', '화', '수', '목', '금'][current_day_idx-1]
                subject = timetable_data.get(day_name, {}).get(str(current_period), "")
                
                # 현재 교시에 과목이 있는 경우 알림
                if subject:
                    self.show_notification(
                        "교시 변경",
                        f"{current_period}교시 {subject} 수업이 시작되었습니다."
                    )
                    self.last_notified_period = current_period

        # 다음 교시 예고 알림 기능
        if self.next_period_warning and current_period is not None and current_day_idx is not None:
            next_period = current_period + 1
            if next_period <= 7:  # 최대 7교시까지만 체크
                now = QtCore.QTime.currentTime()
                next_period_start = self.settings_manager.time_ranges.get(next_period, {}).get("start")
                
                if next_period_start:
                    time_diff_secs = now.secsTo(next_period_start)
                    # 다음 교시 시작 n분 전 예고
                    if 0 < time_diff_secs <= self.warning_minutes * 60:
                        if self.last_notified_warning != next_period:
                            day_name = ['월', '화', '수', '목', '금'][current_day_idx-1]
                            subject = timetable_data.get(day_name, {}).get(str(next_period), "")
                            
                            if subject:
                                minutes = time_diff_secs // 60
                                self.show_notification(
                                    "다음 교시 예고",
                                    f"{minutes}분 후 {next_period}교시 {subject} 수업이 시작됩니다."
                                )
                                self.last_notified_warning = next_period

    def show_notification(self, title, message):
        """시스템 알림 표시"""
        if self.system == "Windows":
            self._show_windows_notification(title, message)
        elif self.system == "Darwin":  # macOS
            self._show_macos_notification(title, message)
        else:  # Linux 등
            self._show_fallback_notification(title, message)
    
    def _show_windows_notification(self, title, message):
        """Windows 10+ 알림 표시"""
        try:
            # win10toast 패키지 사용 시도
            try:
                from win10toast import ToastNotifier
                toaster = ToastNotifier()
                toaster.show_toast(title, message, duration=5, threaded=True)
                return
            except ImportError:
                pass
                
            # Qt의 자체 알림 기능 사용
            tray_icon = QtWidgets.QSystemTrayIcon()
            tray_icon.setIcon(QtGui.QIcon.fromTheme("dialog-information"))
            tray_icon.show()
            tray_icon.showMessage(title, message, QtWidgets.QSystemTrayIcon.Information, 3000)
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"윈도우 알림 오류: {e}")
            # 오류 발생 시 폴백 알림 사용
            self._show_fallback_notification(title, message)
    
    def _show_macos_notification(self, title, message):
        """macOS 알림 표시"""
        try:
            # osascript를 통해 macOS 알림 표시
            import subprocess
            script = f'display notification "{message}" with title "{title}"'
            subprocess.run(['osascript', '-e', script])
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"macOS 알림 오류: {e}")
            # 오류 발생 시 폴백 알림 사용
            self._show_fallback_notification(title, message)
    
    def _show_fallback_notification(self, title, message):
        """플랫폼에 관계없이 작동하는 기본 알림 대화상자"""
        try:
            # 간단한 팝업 메시지로 표시
            msg = QtWidgets.QMessageBox()
            msg.setWindowTitle(title)
            msg.setText(message)
            msg.setIcon(QtWidgets.QMessageBox.Information)
            msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
            # 타이머로 3초 후에 자동으로 닫히도록 설정
            QtCore.QTimer.singleShot(3000, msg.close)
            msg.show()
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"기본 알림 오류: {e}")

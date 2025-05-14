import logging
import sys
import os
import shutil
import atexit
import traceback
import multiprocessing
import signal
import psutil
import threading
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer, pyqtSignal, QObject

# 버전 정보 가져오기
from utils.version import get_version, get_version_string
# 예외 처리 시스템
from utils.exceptions import TimetableError, handle_exception

# 사용자 모듈 가져오기
from gui.widget import Widget
from utils.paths import resource_path, ensure_data_directory_exists
from utils.settings_manager import SettingsManager
from notifications.notification_manager import NotificationManager
from tray_icon import TrayIcon

# 정리 작업이 완료되었는지 추적하는 플래그
_cleanup_done = False

# Windows 환경에서 사용할 추가 모듈
try:
    import win32api
    import win32con
    import win32process
    WINDOWS_MODULES_AVAILABLE = True
except ImportError:
    WINDOWS_MODULES_AVAILABLE = False

# 로거 설정
def setup_logging():
    log_dir = os.path.join(ensure_data_directory_exists(), "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, "application.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger("SchoolTimetable")

logger = setup_logging()

def force_terminate_process(pid):
    """프로세스를 강제로 종료 (Windows 환경에 최적화)"""
    try:
        if WINDOWS_MODULES_AVAILABLE:
            PROCESS_TERMINATE = 1
            handle = win32api.OpenProcess(PROCESS_TERMINATE, False, pid)
            if handle:
                win32api.TerminateProcess(handle, 0)
                win32api.CloseHandle(handle)
                logger.info(f"Windows API로 프로세스 종료: {pid}")
                return True
        # 일반적인 방식으로 프로세스 종료 시도
        process = psutil.Process(pid)
        process.kill()
        return True
    except Exception as e:
        logger.error(f"프로세스 {pid} 종료 실패: {str(e)}")
        return False

def kill_all_threads():
    """모든 non-daemon 스레드 종료 시도"""
    main_thread = threading.main_thread()
    for thread in threading.enumerate():
        if thread is not main_thread and thread.is_alive():
            logger.info(f"스레드 종료 시도: {thread.name}")
            # 강제 종료는 불가, 데몬 스레드는 메인 종료 시 같이 종료됨
            pass

class ApplicationManager:
    def __init__(self):
        self._cleanup_done = False
        self.app = None
        self.widget = None
        self.tray_icon = None
        self.setup_environment()
        
    def setup_environment(self):
        """실행 환경 설정"""
        config = {
            "app_name": "학교 시간표 위젯",
            "app_version": get_version(),
            "app_version_string": get_version_string(),
            "data_dir": ensure_data_directory_exists()
        }
        
        # 환경 변수 설정
        os.environ['SCHOOL_TIMETABLE_DATA_DIR'] = config["data_dir"]
        os.environ['SCHOOL_TIMETABLE_VERSION'] = config["app_version"]
        
        # 버전 정보 로깅
        logger.info(f"애플리케이션 시작: {config['app_name']} {config['app_version_string']}")
        
        # 기본 리소스 복사 (첫 실행 시)
        self.copy_default_resources(config["data_dir"])
        
        return config
    
    def copy_default_resources(self, data_dir):
        """기본 리소스 파일 복사"""
        try:
            csv_path = os.path.join(data_dir, 'default_timetable.csv')
            if not os.path.exists(csv_path) and getattr(sys, 'frozen', False):
                default_csv = resource_path(os.path.join('assets', 'default_timetable.csv'))
                if (os.path.exists(default_csv)):
                    shutil.copy(default_csv, csv_path)
                else:
                    logger.error(f"기본 시간표 파일을 찾을 수 없습니다: {default_csv}")
        except Exception as e:
            logger.error(f"리소스 복사 중 오류 발생: {e}")
        
    def setup_signal_handlers(self):
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        if hasattr(signal, 'SIGBREAK'):
            signal.signal(signal.SIGBREAK, self.signal_handler)
            
    def signal_handler(self, signum, frame):
        logger.info(f"시그널 {signum} 수신: 애플리케이션을 종료합니다.")
        self.cleanup_resources()
        sys.exit(0)
        
    def cleanup_resources(self):
        """애플리케이션 종료 시 모든 리소스 정리"""
        if self._cleanup_done:
            logger.info("정리 작업이 이미 완료되었습니다.")
            return
        
        logger.info("리소스 정리 시작...")
        
        # 모든 QTimer 중지 시도
        try:
            self.stop_timers()
        except:
            logger.error("QTimer 중지 중 오류 발생")
        
        # 모든 스레드 종료 시도
        try:
            kill_all_threads()
        except Exception as e:
            logger.error(f"스레드 종료 중 오류: {str(e)}")
        
        # 현재 프로세스의 모든 자식 프로세스 종료
        try:
            current_pid = os.getpid()
            current_process = psutil.Process(current_pid)
            children = current_process.children(recursive=True)
            logger.info(f"종료할 자식 프로세스 수: {len(children)}")
            for idx, child in enumerate(children):
                try:
                    logger.info(f"프로세스 종료 시도 {idx+1}/{len(children)}: PID {child.pid}, 이름: {child.name()}")
                    child.terminate()
                except Exception as e:
                    logger.error(f"프로세스 종료 중 오류 (PID {child.pid}): {str(e)}")
            gone, alive = psutil.wait_procs(children, timeout=1)
            logger.info(f"정상 종료된 프로세스: {len(gone)}, 강제 종료 필요한 프로세스: {len(alive)}")
            for child in alive:
                try:
                    logger.info(f"프로세스 강제 종료 (PID {child.pid}): {child.name()}")
                    force_terminate_process(child.pid)
                except Exception as e:
                    logger.error(f"프로세스 강제 종료 중 오류 (PID {child.pid}): {str(e)}")
        except Exception as e:
            logger.error(f"프로세스 정리 중 예외 발생: {str(e)}")
        
        # multiprocessing 모듈의 자식 프로세스 정리
        try:
            active_children = multiprocessing.active_children()
            logger.info(f"활성 multiprocessing 자식 프로세스: {len(active_children)}")
            for child in active_children:
                logger.info(f"multiprocessing 자식 종료: {child.name} (PID: {child.pid})")
                child.terminate()
                child.join(0.5)
        except Exception as e:
            logger.error(f"multiprocessing 정리 중 오류: {str(e)}")
        
        # Windows에서 추가로 필요한 프로세스 정리
        if hasattr(multiprocessing, 'process'):
            try:
                mp_children = list(multiprocessing.process._children)
                logger.info(f"남은 multiprocessing 프로세스: {len(mp_children)}")
                for p in mp_children:
                    if p.is_alive():
                        logger.info(f"추가 프로세스 종료: {p.name}")
                        p.terminate()
                        p.join(0.5)
            except Exception as e:
                logger.error(f"추가 프로세스 정리 중 오류: {str(e)}")
        
        # 관련 파이썬 프로세스 강제 종료 (최후의 수단)
        try:
            self.force_kill_python_processes()
        except Exception as e:
            logger.error(f"파이썬 프로세스 강제 종료 중 오류: {str(e)}")
        
        # 메모리 정리 시도
        try:
            import gc
            gc.collect()
        except:
            pass
        
        logger.info("모든 리소스 정리 완료")
        self._cleanup_done = True
    
    def force_kill_python_processes(self):
        current_pid = os.getpid()
        logger.info(f"현재 프로세스 ID: {current_pid}")
        killed = 0
        try:
            for proc in psutil.process_iter(['pid', 'name', 'username', 'cmdline']):
                try:
                    pid = proc.pid
                    if pid == current_pid:
                        continue
                    try:
                        proc_name = proc.name().lower()
                    except:
                        proc_name = ""
                    try:
                        cmdline = proc.cmdline()
                    except:
                        cmdline = []
                    is_python = False
                    if cmdline:
                        is_python = any('python' in cmd.lower() for cmd in cmdline if cmd)
                    if proc_name in ('python.exe', 'pythonw.exe'):
                        is_python = True
                    if is_python:
                        logger.info(f"Python 프로세스 발견: PID {pid}, 명령어: {' '.join(cmdline[:2] if cmdline else [])}")
                        if force_terminate_process(pid):
                            killed += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
                    logger.debug(f"프로세스 정보 접근 오류: {e}")
                    continue
                except Exception as e:
                    logger.error(f"예상치 못한 오류: {e}")
                    continue
        except Exception as e:
            logger.error(f"프로세스 종료 중 오류 발생: {e}")
        logger.info(f"총 {killed}개의 Python 프로세스를 강제 종료했습니다.")
        return killed
    
    def stop_timers(self):
        if not self.app:
            return
        for obj in self.app.findChildren(QTimer):
            try:
                if obj.isActive():
                    obj.stop()
                    logger.debug(f"QTimer 중지: {obj}")
            except Exception as e:
                logger.error(f"타이머 중지 중 오류: {e}")
    
    def run(self):
        try:
            self.setup_signal_handlers()
            atexit.register(self.final_cleanup)
            self.app = QApplication(sys.argv)
            self.app.setQuitOnLastWindowClosed(False)
            self.app.setApplicationName("학교 시간표 위젯")
            self.app.aboutToQuit.connect(self.cleanup_resources)
            settings_manager = SettingsManager.get_instance()
            notification_manager = NotificationManager.get_instance()
            self.widget = Widget()
            self.widget.cleanup_on_close = self.cleanup_resources
            self.widget.show()
            self.tray_icon = TrayIcon(self.widget)
            self.tray_icon.show_action.triggered.connect(self.widget.show)
            self.tray_icon.exit_action.triggered.connect(self.safe_exit)
            if not self.tray_icon.isSystemTrayAvailable() or not self.tray_icon.isVisible():
                logger.warning("시스템 트레이를 사용할 수 없거나 아이콘이 표시되지 않습니다.")
                from PyQt5.QtGui import QIcon
                self.tray_icon.setIcon(QIcon(resource_path(os.path.join('assets', 'app_icon.ico'))))
            self.tray_icon.show()
            exit_code = self.app.exec_()
            logger.info(f"앱 종료됨 (코드: {exit_code}), 리소스 정리 시작")
            self.cleanup_resources()
            return exit_code
        except Exception as e:
            logger.exception(f"애플리케이션 실행 중 오류 발생: {e}")
            self.cleanup_resources()
            return 1
    
    def safe_exit(self):
        logger.info("트레이 아이콘에서 종료 요청됨")
        if self.widget:
            self.widget.hide()
        if self.tray_icon:
            self.tray_icon.hide()
        self.cleanup_resources()
        logger.info("애플리케이션 정상 종료")
        QTimer.singleShot(200, lambda: os._exit(0))
    
    def final_cleanup(self):
        if not self._cleanup_done:
            logger.info("프로그램 종료: 최종 정리 작업 수행")
            self.cleanup_resources()
        logger.info("프로그램 정상 종료 완료")

def main():
    try:
        sys.excepthook = handle_exception
        version_str = get_version_string()
        logger.info(f"학교시간표위젯 {version_str} 시작")
        app_manager = ApplicationManager()
        exit_code = app_manager.run()
        return exit_code
    except Exception as e:
        logger.critical(f"심각한 오류 발생: {e}", exc_info=True)
        try:
            app = QApplication.instance()
            if not app:
                app = QApplication(sys.argv)
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setWindowTitle("심각한 오류")
            msg_box.setText("프로그램을 시작할 수 없습니다")
            msg_box.setInformativeText(str(e))
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.exec_()
        except:
            print(f"심각한 오류: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    multiprocessing.freeze_support()
    sys.exit(main())
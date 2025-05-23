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
import requests
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer, pyqtSignal, QObject, Qt

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
from utils.auto_start import enable_auto_start, disable_auto_start

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
    from utils.paths import get_log_directory, APP_NAME # APP_NAME은 파일명에 사용될 수 있음
    
    log_dir_path = get_log_directory() # utils.paths에서 로그 디렉토리 경로 가져오기
    # os.makedirs는 get_log_directory 내부에서 처리됨
    
    # 로그 파일명 (예: SchoolTimetableWidget.log)
    log_file_name = f"{APP_NAME}.log"
    log_file_path = os.path.join(log_dir_path, log_file_name)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file_path, encoding='utf-8'),
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

GITHUB_REPO = "chuthulhu/school-timetable-widget"
GITHUB_API_RELEASES = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

class Updater:
    def __init__(self, current_version):
        self.current_version = current_version
        self.latest_version = None
        self.download_url = None
        self.release_notes = None

    def check_for_update(self):
        try:
            resp = requests.get(GITHUB_API_RELEASES, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                self.latest_version = data.get("tag_name")
                self.release_notes = data.get("body", "")
                for asset in data.get("assets", []):
                    if asset["name"].endswith(".exe"):
                        self.download_url = asset["browser_download_url"]
                        break
                if self.latest_version and self.download_url:
                    return self.is_newer_version(self.latest_version, self.current_version)
            else:
                logger.warning(f"GitHub 릴리즈 정보 조회 실패: {resp.status_code}")
        except Exception as e:
            logger.warning(f"업데이트 확인 중 오류: {e}")
        return False

    @staticmethod
    def is_newer_version(latest, current):
        import re
        def parse(v):
            return [int(x) for x in re.findall(r'\d+', v)]
        return parse(latest) > parse(current)

    def download_update(self, dest_path, progress_callback=None):
        try:
            with requests.get(self.download_url, stream=True, timeout=30) as r:
                r.raise_for_status()
                total = int(r.headers.get('content-length', 0))
                with open(dest_path, 'wb') as f:
                    downloaded = 0
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if progress_callback and total:
                                progress_callback(downloaded, total)
            return True
        except Exception as e:
            logger.error(f"업데이트 다운로드 실패: {e}")
            return False

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
        
        # 관련 파이썬 프로세스 강제 종료 (최후의 수단) - 현재 비활성화 (위험성 때문)
        # try:
        #     self.force_kill_python_processes()
        # except Exception as e:
        #     logger.error(f"파이썬 프로세스 강제 종료 중 오류: {str(e)}")
        
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
            self.settings_manager = SettingsManager.get_instance() # self.settings_manager로 할당
            self.notification_manager = NotificationManager.get_instance() # self.notification_manager로 할당
            
            # 애플리케이션 시작 시 자동 시작 설정 동기화
            self._sync_auto_start_setting()

            # Widget 생성 시 필요한 인스턴스 전달
            self.widget = Widget(settings_manager=self.settings_manager,
                                 notification_manager=self.notification_manager,
                                 app_manager=self)
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
        # QTimer.singleShot(200, lambda: os._exit(0)) # os._exit() 대신 QApplication.quit() 사용
        if QApplication.instance():
            QApplication.instance().quit()

    def _sync_auto_start_setting(self):
        """애플리케이션 시작 시 자동 시작 설정을 시스템 상태와 동기화합니다."""
        try:
            # platform 모듈은 파일 상단에 이미 임포트되어 있다고 가정
            # import platform
            import platform # 명시적으로 다시 임포트 (안전하게)
            from utils.auto_start import is_auto_start_enabled, enable_auto_start, disable_auto_start, get_executable_path
            from utils.paths import resource_path, APP_NAME
            # os 모듈은 파일 상단에 이미 임포트되어 있음

            if platform.system() != "Windows": # Windows 외에는 자동 시작 미지원
                logger.debug("Windows가 아닌 OS에서는 자동 시작 동기화를 건너<0xEB><0><0x8A><0x8D>니다.")
                return

            app_name_for_shortcut = APP_NAME
            # SettingsManager 인스턴스가 self.settings_manager에 할당되어 있어야 함
            if not hasattr(self, 'settings_manager') or self.settings_manager is None:
                logger.error("SettingsManager가 초기화되지 않아 자동 시작 설정을 동기화할 수 없습니다.")
                return

            current_setting_enabled = getattr(self.settings_manager, 'auto_start_enabled', False)
            system_is_enabled = is_auto_start_enabled(app_name_for_shortcut=app_name_for_shortcut)

            executable_path = get_executable_path()
            icon_path = resource_path("assets/app_icon.ico")
            if not os.path.exists(icon_path):
                icon_path = resource_path("assets/icon.ico")
            if not os.path.exists(icon_path): # 아이콘 파일이 아예 없는 경우
                icon_path = executable_path # 실행 파일 자체 아이콘 사용


            if current_setting_enabled != system_is_enabled:
                logger.info(f"자동 시작 설정 동기화 필요: 설정({current_setting_enabled}), 시스템({system_is_enabled})")
                if current_setting_enabled:
                    if enable_auto_start(app_name_for_shortcut=app_name_for_shortcut,
                                         target_path=executable_path,
                                         icon_location=icon_path):
                        logger.info("시스템 자동 시작 활성화됨 (설정 동기화).")
                    else:
                        logger.error("시스템 자동 시작 활성화 실패 (설정 동기화).")
                        # 설정값을 시스템 상태에 맞게 변경 (False로) 및 저장
                        self.settings_manager.set_auto_start(False)
                else: # current_setting_enabled is False, system_is_enabled is True
                    if disable_auto_start(app_name_for_shortcut=app_name_for_shortcut):
                        logger.info("시스템 자동 시작 비활성화됨 (설정 동기화).")
                        # 설정은 이미 False이므로 set_auto_start(False)를 다시 호출할 필요는 없음
                        # (set_auto_start 내부에서 값이 같으면 저장 안 함)
                    else:
                        logger.error("시스템 자동 시작 비활성화 실패 (설정 동기화).")
            else:
                logger.debug(f"자동 시작 설정과 시스템 상태 일치: {current_setting_enabled}")
        except ImportError as e:
            logger.warning(f"자동 시작 관련 모듈(pywin32 등)을 찾을 수 없어 자동 시작 설정을 동기화할 수 없습니다: {e}")
        except Exception as e:
            logger.error(f"자동 시작 설정 동기화 중 오류 발생: {e}", exc_info=True)
    
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

        # 자동 업데이트 확인
        updater = Updater(get_version())
        if updater.check_for_update():
            from PyQt5.QtWidgets import QMessageBox, QProgressDialog
            app = QApplication.instance() or QApplication(sys.argv)
            msg = f"새 버전({updater.latest_version})이 출시되었습니다!\n\n릴리즈 노트:\n{updater.release_notes}\n\n지금 다운로드하시겠습니까?"
            reply = QMessageBox.question(None, "업데이트 알림", msg, QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                import tempfile
                import os
                dest = os.path.join(tempfile.gettempdir(), f"school_timetable_update_{updater.latest_version}.exe")
                progress = QProgressDialog("업데이트 다운로드 중...", None, 0, 100)
                progress.setWindowTitle("업데이트")
                progress.setWindowModality(Qt.ApplicationModal)
                def cb(done, total):
                    progress.setValue(int(done/total*100))
                ok = updater.download_update(dest, progress_callback=cb)
                progress.close()
                if ok:
                    QMessageBox.information(None, "업데이트 완료", f"다운로드가 완료되었습니다.\n프로그램을 종료하면 새 버전이 실행됩니다.")
                    # 종료 후 새 exe 실행
                    import subprocess
                    subprocess.Popen([dest]) # 새 업데이터 실행
                    logger.info("새 업데이터 실행 후 현재 애플리케이션 종료 요청")
                    if QApplication.instance():
                        QApplication.instance().quit() # 현재 앱 종료
                    return 0 # main 함수 종료
                else:
                    QMessageBox.warning(None, "업데이트 실패", "업데이트 파일 다운로드에 실패했습니다.")
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
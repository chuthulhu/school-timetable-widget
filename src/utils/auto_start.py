import os
import sys
import logging
import platform

# 로거 설정
logger = logging.getLogger(__name__)

try:
    # APP_NAME은 내부 식별용 (영문), APP_DISPLAY_NAME은 UI 표시용 (한글 등)
    from utils.paths import APP_NAME, APP_DISPLAY_NAME
except ImportError:
    APP_NAME = "SchoolTimetableWidget" # 폴백 (영문)
    APP_DISPLAY_NAME = "학교 시간표 위젯" # 폴백 (표시용)

def get_executable_path():
    """현재 실행 중인 실행 파일의 경로를 반환합니다."""
    if getattr(sys, 'frozen', False):
        # PyInstaller 등으로 빌드된 경우
        return sys.executable
    else:
        # 일반 Python 스크립트로 실행된 경우 (개발 중)
        return os.path.abspath(sys.argv[0])

def get_startup_folder():
    """현재 사용자의 시작프로그램 폴더 경로를 반환합니다."""
    if platform.system() == "Windows":
        try:
            appdata_dir = os.getenv('APPDATA')
            if appdata_dir:
                startup_path = os.path.join(appdata_dir, 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
                if os.path.isdir(startup_path):
                    return startup_path
            logger.warning("APPDATA 환경 변수를 찾을 수 없거나 시작 폴더 경로가 유효하지 않습니다.")
        except Exception as e:
            logger.error(f"시작프로그램 폴더 경로 조회 중 오류: {e}")
    # Windows가 아니거나 오류 발생 시 None 반환
    logger.debug("Windows 시작프로그램 폴더를 찾을 수 없거나 지원되지 않는 OS입니다.")
    return None

def get_shortcut_path(app_name_for_shortcut=None):
    """시작프로그램 폴더 내의 바로 가기 파일 경로를 반환합니다."""
    startup_dir = get_startup_folder()
    if not startup_dir:
        return None
    
    # 바로 가기 파일명은 내부 식별용 APP_NAME (영문)을 사용
    name_for_file = app_name_for_shortcut or APP_NAME 
    safe_name = "".join(c for c in name_for_file if c.isalnum() or c in " _-").rstrip()
    if not safe_name: 
        safe_name = "AppShortcut" # 이름이 모두 특수문자였던 경우 대비
    return os.path.join(startup_dir, f"{safe_name}.lnk")

def enable_auto_start(app_name_for_shortcut=None, target_path=None, working_directory=None, icon_location=None):
    """
    시작프로그램 폴더에 바로 가기를 생성하여 자동 시작을 활성화합니다.
    app_name_for_shortcut: 바로 가기 파일명 및 내부 식별에 사용될 이름 (주로 APP_NAME).
    target_path: 바로 가기가 가리킬 실행 파일 경로.
    working_directory: 바로 가기의 작업 디렉토리.
    icon_location: 바로 가기의 아이콘 경로.
    """
    if platform.system() != "Windows":
        logger.warning("Windows가 아닌 OS에서는 자동 시작 설정을 지원하지 않습니다.")
        return False

    # app_name_for_shortcut은 내부 식별자(주로 APP_NAME)를 사용하도록 유도
    shortcut_name_internal = app_name_for_shortcut or APP_NAME
    shortcut_file_path = get_shortcut_path(shortcut_name_internal)

    if not shortcut_file_path:
        logger.error("바로 가기 경로를 생성할 수 없습니다 (시작 폴더 문제일 수 있음).")
        return False

    _target_path = target_path or get_executable_path()
    _working_directory = working_directory or os.path.dirname(_target_path)
    _icon_location = icon_location or _target_path

    try:
        import win32com.client # pywin32 라이브러리 필요
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortcut(shortcut_file_path)
        
        if _target_path.lower().endswith((".py", ".pyw")):
            pythonw_exe = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
            if os.path.exists(pythonw_exe):
                shortcut.TargetPath = pythonw_exe
                shortcut.Arguments = f'"{_target_path}"' 
            else: 
                shortcut.TargetPath = sys.executable 
                shortcut.Arguments = f'"{_target_path}"'
        else: 
            shortcut.TargetPath = _target_path
        
        shortcut.WorkingDirectory = _working_directory
        shortcut.IconLocation = _icon_location
        shortcut.Description = f"{APP_DISPLAY_NAME} 자동 시작"
        shortcut.save()
        logger.info(f"자동 시작 활성화: '{shortcut_file_path}' 바로 가기 생성됨 (대상: {_target_path})")
        return True
    except ImportError:
        logger.error("pywin32 라이브러리가 설치되어 있지 않아 자동 시작을 활성화할 수 없습니다. 'pip install pywin32'로 설치해주세요.")
        return False
    except Exception as e:
        logger.error(f"자동 시작 활성화 중 오류 발생: {e}")
        return False

def disable_auto_start(app_name_for_shortcut=None):
    """시작프로그램 폴더에서 바로 가기를 삭제하여 자동 시작을 비활성화합니다."""
    if platform.system() != "Windows":
        logger.warning("Windows가 아닌 OS에서는 자동 시작 설정을 지원하지 않습니다.")
        return False

    shortcut_name_internal = app_name_for_shortcut or APP_NAME
    shortcut_file_path = get_shortcut_path(shortcut_name_internal)

    if not shortcut_file_path: 
        logger.error("바로 가기 경로를 확인할 수 없어 자동 시작을 비활성화할 수 없습니다.")
        return False 

    try:
        if os.path.exists(shortcut_file_path):
            os.remove(shortcut_file_path)
            logger.info(f"자동 시작 비활성화: '{shortcut_file_path}' 바로 가기 삭제됨")
            return True
        else:
            logger.info("자동 시작이 이미 비활성화되어 있거나 바로 가기 파일이 없습니다.")
            return True 
    except Exception as e:
        logger.error(f"자동 시작 비활성화 중 오류 발생: {e}")
        return False

def is_auto_start_enabled(app_name_for_shortcut=None):
    """자동 시작이 활성화되어 있는지 (바로 가기 파일이 존재하는지) 확인합니다."""
    if platform.system() != "Windows":
        return False 

    shortcut_name_internal = app_name_for_shortcut or APP_NAME
    shortcut_file_path = get_shortcut_path(shortcut_name_internal)
    
    if not shortcut_file_path: 
        return False
        
    return os.path.exists(shortcut_file_path)

"""
경로 관리 유틸리티 모듈
- 애플리케이션에서 사용하는 모든 경로 관리
- OS별 적절한 경로 제공
- 사용자 데이터 디렉토리 관리
"""
import os
import sys
import logging
from pathlib import Path
import platform
import appdirs
import shutil

# 로거 설정
logger = logging.getLogger(__name__)

# 애플리케이션 정보
APP_DISPLAY_NAME = "학교시간표위젯" # UI 표시용 이름
APP_NAME = "SchoolTimetableWidget" # 내부 식별자, 폴더명, 레지스트리 키 등에 사용될 영문 이름
APP_AUTHOR = "TimeTableDev" # 개발자/회사 이름

def resource_path(relative_path):
    """
    패키지 리소스 경로를 얻기 위한 헬퍼 함수
    PyInstaller로 패키징된 애플리케이션에서도 리소스에 접근할 수 있게 함
    """
    try:
        # PyInstaller에서 생성된 임시 폴더
        base_path = sys._MEIPASS
        logger.debug(f"PyInstaller 환경에서 리소스 경로 사용: {base_path}")
    except Exception:
        # 일반 실행 시 현재 스크립트 경로
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        logger.debug(f"일반 환경에서 리소스 경로 사용: {base_path}")
    
    full_path = os.path.join(base_path, relative_path)
    logger.debug(f"리소스 경로 반환: {full_path}")
    return full_path

def get_data_directory():
    """
    애플리케이션 데이터 저장 디렉토리 반환
    appdirs 라이브러리를 사용해 OS에 맞는 표준 경로 제공
    """
    # 환경변수가 설정되어 있으면 그것을 우선 사용
    env_dir = os.environ.get('SCHOOL_TIMETABLE_DATA_DIR')
    if env_dir and os.path.exists(env_dir):
        logger.debug(f"환경변수에서 데이터 디렉토리 사용: {env_dir}")
        return env_dir
    
    # 그렇지 않으면 OS에 적합한 디렉토리 사용
    data_dir = appdirs.user_data_dir(APP_NAME, APP_AUTHOR) # 내부 식별용 APP_NAME 사용
    logger.debug(f"OS 표준 데이터 디렉토리 사용: {data_dir}")
    
    # 디렉토리가 없으면 생성
    if not os.path.exists(data_dir):
        try:
            os.makedirs(data_dir)
            logger.info(f"데이터 디렉토리 생성: {data_dir}")
        except Exception as e:
            logger.error(f"데이터 디렉토리 생성 실패: {e}")
            # 실패하면 임시 디렉토리 사용
            import tempfile
            data_dir = os.path.join(tempfile.gettempdir(), APP_NAME) # 내부 식별용 APP_NAME 사용
            os.makedirs(data_dir, exist_ok=True)
            logger.warning(f"임시 디렉토리로 대체: {data_dir}")
    
    return data_dir

def get_config_directory():
    """애플리케이션 설정 저장 디렉토리 반환"""
    config_dir = appdirs.user_config_dir(APP_NAME, APP_AUTHOR) # 내부 식별용 APP_NAME 사용
    os.makedirs(config_dir, exist_ok=True)
    return config_dir

def get_cache_directory():
    """애플리케이션 캐시 디렉토리 반환"""
    cache_dir = appdirs.user_cache_dir(APP_NAME, APP_AUTHOR) # 내부 식별용 APP_NAME 사용
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir

def get_log_directory():
    """로그 파일 저장 디렉토리 반환"""
    log_dir = os.path.join(get_data_directory(), "logs")
    os.makedirs(log_dir, exist_ok=True)
    return log_dir

def ensure_data_directory_exists():
    """데이터 디렉토리가 존재하는지 확인하고 없으면 생성"""
    data_dir = get_data_directory()
    # 이미 get_data_directory에서 생성 로직을 처리하므로 중복 생성 불필요
    return data_dir

def get_settings_file_path():
    """교시별 시간 설정 파일 경로 반환"""
    return os.path.join(get_data_directory(), "time_settings.json")

def get_timetable_file_path():
    """시간표 데이터 파일 경로 반환"""
    return os.path.join(get_data_directory(), "timetable_data.json")

def get_style_settings_file_path():
    """스타일 설정 파일 경로 반환"""
    return os.path.join(get_data_directory(), "style_settings.json")

def get_widget_settings_file_path():
    """위젯 위치 설정 파일 경로 반환"""
    return os.path.join(get_data_directory(), "widget_settings.json")

def get_notification_settings_file_path():
    """알림 설정 파일 경로 반환"""
    return os.path.join(get_data_directory(), "notification_settings.json")

def get_backup_directory():
    """백업 파일 저장 디렉토리 반환"""
    backup_dir = os.path.join(get_data_directory(), "backups")
    os.makedirs(backup_dir, exist_ok=True)
    return backup_dir

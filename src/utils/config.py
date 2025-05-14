"""
통합된 시간표 위젯 설정 파일
- 애플리케이션 전역 설정 관리
- 하드코딩된 경로 대신 유연한 경로 설정 사용
- 운영체제에 따른 적절한 설정 적용

테마/스타일 관리 가이드라인
- 테마 정의 및 기본값: utils/config.py (THEMES, DEFAULT_STYLES)
- 스타일 생성 함수: utils/styling.py (generate_header_style 등)
- 테마/스타일 관련 코드는 반드시 위 두 파일만 수정
- 테마 프리셋 추가 시 config.py의 THEMES, styling.py의 get_theme_presets()만 수정
- settings_manager.py 등에서는 import config, import styling만 사용
"""

import os
import sys
import platform
import appdirs

class Config:
    # 애플리케이션 기본 정보
    APP_NAME = "학교시간표위젯"
    APP_AUTHOR = "TimeTableDev"
    
    # 사용자 데이터 경로 (OS에 맞게 자동 설정)
    USER_DATA_DIR = appdirs.user_data_dir(APP_NAME, APP_AUTHOR)
    USER_CONFIG_DIR = appdirs.user_config_dir(APP_NAME, APP_AUTHOR)
    USER_CACHE_DIR = appdirs.user_cache_dir(APP_NAME, APP_AUTHOR)
    
    # 리소스 파일 경로
    @staticmethod
    def get_resource_path(relative_path):
        """번들링된 애플리케이션 내의 리소스 경로 반환"""
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.abspath('.'), relative_path)
    
    # 파일 경로 설정 (상대 경로는 절대 경로로 변환)
    TIMETABLE_CSV_PATH = get_resource_path.__func__('assets/default_timetable.csv')
    
    # 사용자 설정 파일 (사용자 데이터 디렉토리에 저장)
    TIME_SETTINGS_FILE = 'time_settings.json'
    TIMETABLE_DATA_FILE = 'timetable_data.json'
    STYLE_SETTINGS_FILE = 'style_settings.json'
    WIDGET_SETTINGS_FILE = 'widget_settings.json'
    
    # 창 설정
    WINDOW_TRANSPARENCY = 0.8
    DEFAULT_WINDOW_POSITION = (100, 100)
    DEFAULT_WINDOW_SIZE = (400, 300)
    
    # 시간표 구성 설정
    SUBJECTS = ['Math', 'Science', 'English', 'History', 'Art', 'Physical Education', 'Music']
    DAYS_OF_WEEK = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    DAYS_OF_WEEK_KR = ['월', '화', '수', '목', '금']
    NUMBER_OF_CLASSES = 7
    
    # 기본 교시별 시간 설정
    DEFAULT_TIME_RANGES = {
        1: {"start": "09:00", "end": "09:50"},
        2: {"start": "10:00", "end": "10:50"},
        3: {"start": "11:00", "end": "11:50"},
        4: {"start": "12:00", "end": "12:50"},
        5: {"start": "14:00", "end": "14:50"},
        6: {"start": "15:00", "end": "15:50"},
        7: {"start": "16:00", "end": "16:50"}
    }
    
    # 알림 설정
    DEFAULT_NOTIFICATION_SETTINGS = {
        "enabled": True,
        "next_period_warning": True,
        "warning_minutes": 5
    }
    
    # 테마 설정
    THEME_LIGHT = "light"
    THEME_DARK = "dark"
    THEME_CUSTOM = "custom"
    
    # 테마 스타일 정의
    THEMES = {
        THEME_LIGHT: {
            "header_bg_color": "#6464C8",  # 연한 파란색
            "header_text_color": "#FFFFFF",  # 흰색
            "cell_bg_color": "#FFFFFF",  # 흰색
            "cell_text_color": "#000000",  # 검정색 
            "current_period_color": "#FFD700",  # 금색
            "border_color": "#000000",  # 검정색
            "header_opacity": 120,  # 약간 투명한 헤더 (0-255)
            "cell_opacity": 30,  # 매우 투명한 셀 (0-255)
            "current_period_opacity": 150,  # 현재 교시 투명도 (0-255)
            "border_opacity": 200,  # 테두리 투명도
        },
        THEME_DARK: {
            "header_bg_color": "#2C2C54",  # 진한 남색
            "header_text_color": "#E4E4E4",  # 밝은 회색
            "cell_bg_color": "#393954",  # 어두운 파란색
            "cell_text_color": "#FFFFFF",  # 흰색 
            "current_period_color": "#FFB400",  # 진한 금색
            "border_color": "#CCCCCC",  # 연한 회색
            "header_opacity": 180,  # 약간 투명한 헤더 (0-255)
            "cell_opacity": 120,  # 불투명한 셀 (0-255)
            "current_period_opacity": 200,  # 현재 교시 투명도 (0-255)
            "border_opacity": 150,  # 테두리 투명도
        }
    }
    
    # 기본 테마 설정
    DEFAULT_THEME = THEME_LIGHT
    
    # 기본 스타일 설정
    DEFAULT_STYLES = {
        # 라이트 테마 기본값으로 초기화
        **THEMES[THEME_LIGHT],
        # 폰트 설정 추가
        "font_family": "맑은 고딕",  # 기본 폰트
        "font_size": 10,
        # 헤더 및 셀 개별 폰트 설정
        "header_font_family": "맑은 고딕",  # 기본 헤더 폰트
        "header_font_size": 11,  # 헤더는 약간 더 크게
        "cell_font_family": "맑은 고딕",  # 기본 셀 폰트
        "cell_font_size": 10,  # 셀 폰트 크기
        # 테마 설정
        "theme": DEFAULT_THEME
    }
    
    # 애플리케이션 설정
    APP_NAME = "학교 시간표 위젯"
    APP_VERSION = "1.0.0"
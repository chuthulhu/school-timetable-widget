import json
import os
import datetime
import shutil
import logging
from PyQt5 import QtCore
from utils.paths import (
    get_timetable_file_path, get_settings_file_path, 
    get_style_settings_file_path, get_widget_settings_file_path,
    get_backup_directory
)
from utils.config import Config
from utils.exceptions import DataError, ConfigError

# 로거 설정
logger = logging.getLogger(__name__)

# get_notification_settings_file_path 함수 추가 또는 경로 지정
def get_notification_settings_file_path():
    """알림 설정 파일 경로 반환"""
    from utils.paths import get_data_directory
    return os.path.join(get_data_directory(), "notification_settings.json")

class SettingsManager:
    """설정 관리 클래스"""
    
    # 싱글톤 인스턴스
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """싱글톤 인스턴스 반환"""
        if cls._instance is None:
            cls._instance = SettingsManager()
        return cls._instance
    
    def __init__(self):
        """설정 관리자 초기화"""
        # 이미 인스턴스가 있는지 확인
        if SettingsManager._instance is not None:
            raise Exception("SettingsManager는 싱글톤 클래스입니다. get_instance() 메서드를 사용하세요.")
        
        # 테마 및 스타일 설정
        self.theme = Config.DEFAULT_THEME
        
        # 기본 스타일 설정 (config에서 가져옴)
        self.header_bg_color = Config.DEFAULT_STYLES["header_bg_color"]
        self.header_text_color = Config.DEFAULT_STYLES["header_text_color"]
        self.cell_bg_color = Config.DEFAULT_STYLES["cell_bg_color"]
        self.cell_text_color = Config.DEFAULT_STYLES["cell_text_color"]
        self.current_period_color = Config.DEFAULT_STYLES["current_period_color"]
        self.border_color = Config.DEFAULT_STYLES["border_color"]
        self.header_opacity = Config.DEFAULT_STYLES["header_opacity"]
        self.cell_opacity = Config.DEFAULT_STYLES["cell_opacity"]
        self.current_period_opacity = Config.DEFAULT_STYLES["current_period_opacity"]
        self.border_opacity = Config.DEFAULT_STYLES["border_opacity"]
        
        # 기존 폰트 설정은 호환성을 위해 유지
        self.font_family = Config.DEFAULT_STYLES["font_family"]
        self.font_size = Config.DEFAULT_STYLES["font_size"]
        
        # 헤더 및 셀 개별 폰트 설정 추가
        self.header_font_family = Config.DEFAULT_STYLES.get("header_font_family", Config.DEFAULT_STYLES["font_family"])
        self.header_font_size = Config.DEFAULT_STYLES.get("header_font_size", Config.DEFAULT_STYLES["font_size"])
        self.cell_font_family = Config.DEFAULT_STYLES.get("cell_font_family", Config.DEFAULT_STYLES["font_family"])
        self.cell_font_size = Config.DEFAULT_STYLES.get("cell_font_size", Config.DEFAULT_STYLES["font_size"])
        
        # 위젯 위치 및 크기 기본값
        self.widget_position = {"x": Config.DEFAULT_WINDOW_POSITION[0], "y": Config.DEFAULT_WINDOW_POSITION[1]}
        self.widget_size = {"width": Config.DEFAULT_WINDOW_SIZE[0], "height": Config.DEFAULT_WINDOW_SIZE[1]}
        self.is_position_locked = False  # 위치 고정 여부 (기본값: 고정되지 않음)
        self.widget_screen_info = None  # 멀티모니터 스크린 정보 (기본값)
        
        # 기본 시간 설정 (config에서 가져옴)
        self.time_ranges = {}
        for period, time_info in Config.DEFAULT_TIME_RANGES.items():
            start_hour, start_min = map(int, time_info["start"].split(':'))
            end_hour, end_min = map(int, time_info["end"].split(':'))
            
            self.time_ranges[period] = {
                "start": QtCore.QTime(start_hour, start_min),
                "end": QtCore.QTime(end_hour, end_min)
            }
        
        # 시간표 데이터 초기화
        self.timetable_data = {}
        
        # 알림 설정
        self.notification_enabled = True
        self.next_period_warning = True
        self.warning_minutes = 5
        
        # 설정 불러오기
        self.load_all_settings()
        
    def load_all_settings(self):
        """모든 설정 불러오기"""
        self.load_style_settings()
        self.load_time_settings()
        self.load_timetable_data()
        self.load_widget_position()
    
    # Style Settings
    def load_style_settings(self):
        """저장된 스타일 설정 불러오기"""
        file_path = get_style_settings_file_path()
        
        if not os.path.exists(file_path):
            logger.warning(f"스타일 설정 파일이 존재하지 않습니다: {file_path}")
            return
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                style_settings = json.load(f)
            
            # 저장된 설정 적용
            self.header_bg_color = style_settings.get("header_bg_color", self.header_bg_color)
            self.header_text_color = style_settings.get("header_text_color", self.header_text_color)
            self.cell_bg_color = style_settings.get("cell_bg_color", self.cell_bg_color)
            self.cell_text_color = style_settings.get("cell_text_color", self.cell_text_color)
            self.current_period_color = style_settings.get("current_period_color", self.current_period_color)
            self.border_color = style_settings.get("border_color", self.border_color)
            self.header_opacity = style_settings.get("header_opacity", self.header_opacity)
            self.cell_opacity = style_settings.get("cell_opacity", self.cell_opacity)
            self.current_period_opacity = style_settings.get("current_period_opacity", self.current_period_opacity)
            self.border_opacity = style_settings.get("border_opacity", self.border_opacity)
            
            # 기존 폰트 설정 (호환성 유지)
            self.font_family = style_settings.get("font_family", self.font_family)
            self.font_size = style_settings.get("font_size", self.font_size)
            
            # 헤더 및 셀 개별 폰트 설정 로드
            self.header_font_family = style_settings.get("header_font_family", self.font_family)
            self.header_font_size = style_settings.get("header_font_size", self.font_size)
            self.cell_font_family = style_settings.get("cell_font_family", self.font_family)
            self.cell_font_size = style_settings.get("cell_font_size", self.font_size)
            
            # 테마 설정 로드
            self.theme = style_settings.get("theme", self.theme)
            
            logger.info("스타일 설정을 성공적으로 로드했습니다.")
        except json.JSONDecodeError as e:
            logger.error(f"스타일 설정 파일 형식 오류: {e}")
            # 파일 백업 및 기본값 복원
            self._backup_corrupted_file(file_path, "style_settings_backup")
            raise DataError("스타일 설정 파일이 손상되었습니다. 기본값으로 복원합니다.", str(e))
        except Exception as e:
            logger.error(f"스타일 설정 로드 실패: {e}")
            # 오류가 발생해도 기본 스타일은 유지
    def save_style_settings(self):
        """스타일 설정 저장"""
        try:
            style_settings = {
                "header_bg_color": self.header_bg_color,
                "header_text_color": self.header_text_color,
                "cell_bg_color": self.cell_bg_color,
                "cell_text_color": self.cell_text_color,
                "current_period_color": self.current_period_color,
                "border_color": self.border_color,
                "header_opacity": self.header_opacity,
                "cell_opacity": self.cell_opacity,
                "current_period_opacity": self.current_period_opacity,
                "border_opacity": self.border_opacity,
                "font_family": self.font_family,
                "font_size": self.font_size,
                # 헤더 및 셀 폰트 설정 추가
                "header_font_family": self.header_font_family,
                "header_font_size": self.header_font_size,
                "cell_font_family": self.cell_font_family,
                "cell_font_size": self.cell_font_size,
                "theme": self.theme
            }
            
            file_path = get_style_settings_file_path()
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(style_settings, f, ensure_ascii=False, indent=2)
            logger.info("스타일 설정을 성공적으로 저장했습니다.")
        except Exception as e:
            logger.error(f"스타일 설정 저장 오류: {e}")
            raise DataError("스타일 설정 저장 실패", str(e))
            
    def change_theme(self, theme_name):
        """테마 변경"""
        if theme_name not in [Config.THEME_LIGHT, Config.THEME_DARK, Config.THEME_CUSTOM]:
            logger.error(f"알 수 없는 테마 이름: {theme_name}")
            return False
            
        try:
            # 커스텀 테마가 아니면 미리 정의된 테마 설정 적용
            if theme_name != Config.THEME_CUSTOM:
                theme_styles = Config.THEMES[theme_name]
                
                # 테마 설정 적용
                self.header_bg_color = theme_styles["header_bg_color"]
                self.header_text_color = theme_styles["header_text_color"]
                self.cell_bg_color = theme_styles["cell_bg_color"]
                self.cell_text_color = theme_styles["cell_text_color"]
                self.current_period_color = theme_styles["current_period_color"]
                self.border_color = theme_styles["border_color"]
                self.header_opacity = theme_styles["header_opacity"]
                self.cell_opacity = theme_styles["cell_opacity"]
                self.current_period_opacity = theme_styles["current_period_opacity"]
                self.border_opacity = theme_styles["border_opacity"]
                
                # 테마 값 저장
                self.theme = theme_name
                
                # 설정 저장
                self.save_style_settings()
                
            logger.info(f"테마 변경 완료: {theme_name}")
            return True
        except Exception as e:
            logger.error(f"테마 변경 오류: {e}")
            return False
    
    # Time Settings
    def load_time_settings(self):
        """저장된 시간 설정 불러오기"""
        try:
            file_path = get_settings_file_path()
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    time_settings = json.load(f)
                
                # 저장된 설정 적용
                for period, time_range in time_settings.items():
                    period = int(period)  # JSON에서는 키가 문자열로 저장됨
                    start_hour, start_min = map(int, time_range["start"].split(':'))
                    end_hour, end_min = map(int, time_range["end"].split(':'))
                    
                    self.time_ranges[period] = {
                        "start": QtCore.QTime(start_hour, start_min),
                        "end": QtCore.QTime(end_hour, end_min)
                    }
        except Exception as e:
            logger.error(f"시간 설정 로드 오류: {e}")
    
    def save_time_settings(self):
        """시간 설정 저장"""
        try:
            time_settings = {}
            for period, time_range in self.time_ranges.items():
                start_time = time_range["start"].toString("HH:mm")
                end_time = time_range["end"].toString("HH:mm")
                
                time_settings[str(period)] = {
                    "start": start_time,
                    "end": end_time
                }
            
            file_path = get_settings_file_path()
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(time_settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"시간 설정 저장 오류: {e}")
    
    # Timetable Data
    def load_timetable_data(self):
        """저장된 시간표 데이터 불러오기"""
        try:
            file_path = get_timetable_file_path()
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.timetable_data = json.load(f)
        except Exception as e:
            logger.error(f"시간표 데이터 로드 오류: {e}")
            self.timetable_data = {}
    
    def save_timetable_data(self):
        """시간표 데이터 저장"""
        try:
            file_path = get_timetable_file_path()
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.timetable_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"시간표 데이터 저장 오류: {e}")
    
    # 위젯 위치 설정
    def load_widget_position(self):
        """저장된 위젯 위치 불러오기 (멀티모니터 스크린 정보 포함)"""
        try:
            file_path = get_widget_settings_file_path()
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    widget_settings = json.load(f)
                self.widget_position = widget_settings.get("position", self.widget_position)
                self.widget_size = widget_settings.get("size", self.widget_size)
                self.is_position_locked = widget_settings.get("is_position_locked", False)
                self.widget_screen_info = widget_settings.get("screen_info", None)
            else:
                self.widget_screen_info = None
        except Exception as e:
            logger.error(f"위젯 위치 설정 로드 오류: {e}")
            self.widget_screen_info = None

    def save_widget_position(self, x, y, width, height, screen_info=None):
        """위젯 위치 및 스크린 정보 저장 (멀티모니터 지원)"""
        try:
            self.widget_position = {"x": x, "y": y}
            self.widget_size = {"width": width, "height": height}
            self.widget_screen_info = screen_info
            widget_settings = {
                "position": self.widget_position,
                "size": self.widget_size,
                "is_position_locked": self.is_position_locked,
                "screen_info": self.widget_screen_info
            }
            file_path = get_widget_settings_file_path()
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(widget_settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"위젯 위치 설정 저장 오류: {e}")
    
    def toggle_position_lock(self):
        """위치 고정 상태 토글"""
        self.is_position_locked = not self.is_position_locked
        return self.is_position_locked
    
    def set_position_lock(self, locked):
        """위치 고정 상태 설정"""
        self.is_position_locked = locked
        
    def update_timetable_data(self, updated_data):
        """시간표 데이터 업데이트"""
        self.timetable_data = updated_data
        self.save_timetable_data()
        return self.timetable_data
    
    def get_current_period(self, current_time):
        """현재 시간에 해당하는 교시 반환"""
        for period, time_range in self.time_ranges.items():
            start_time = time_range["start"]
            end_time = time_range["end"]
            if start_time <= current_time <= end_time:
                return period
        return None

    def create_backup(self, backup_name=None):
        """현재 설정과 시간표 데이터의 백업 생성"""
        try:
            # 데이터 디렉토리 확인
            from utils.paths import ensure_data_directory_exists, get_data_directory
            data_dir = ensure_data_directory_exists()
            
            # 백업 디렉토리 생성
            backup_dir = os.path.join(data_dir, "backups")
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            
            # 백업 이름 설정 (지정되지 않은 경우 날짜 사용)
            if not backup_name:
                now = datetime.datetime.now()
                backup_name = f"backup_{now.strftime('%Y%m%d_%H%M%S')}"
            
            # 백업 폴더 생성
            backup_path = os.path.join(backup_dir, backup_name)
            if not os.path.exists(backup_path):
                os.makedirs(backup_path)
            
            # 필요한 파일 목록
            files_to_backup = [
                ("timetable_data.json", get_timetable_file_path()),
                ("time_settings.json", get_settings_file_path()),
                ("style_settings.json", get_style_settings_file_path()),
                ("widget_settings.json", get_widget_settings_file_path()),
                ("notification_settings.json", get_notification_settings_file_path()),  # 수정된 함수 사용
            ]
            
            # 파일 복사
            for backup_filename, source_path in files_to_backup:
                if os.path.exists(source_path):
                    shutil.copy2(source_path, os.path.join(backup_path, backup_filename))
            
            # 백업 설명 파일 생성
            description = f"시간표 백업 - {now.strftime('%Y년 %m월 %d일 %H:%M:%S')}"
            with open(os.path.join(backup_path, "description.txt"), 'w', encoding='utf-8') as f:
                f.write(description)
            
            return True, backup_path
            
        except Exception as e:
            logger.error(f"백업 생성 오류: {e}")
            return False, str(e)

    def restore_backup(self, backup_name):
        """지정된 백업에서 설정 복원"""
        try:
            # 데이터 디렉토리
            from utils.paths import get_data_directory
            backup_path = os.path.join(get_data_directory(), "backups", backup_name)
            
            if not os.path.exists(backup_path):
                return False, f"백업을 찾을 수 없습니다: {backup_name}"
            
            # 필요한 파일 목록
            files_to_restore = [
                ("timetable_data.json", get_timetable_file_path()),
                ("time_settings.json", get_settings_file_path()),
                ("style_settings.json", get_style_settings_file_path()),
                ("widget_settings.json", get_widget_settings_file_path()),
                ("notification_settings.json", get_notification_settings_file_path()),
            ]
            
            # 파일 복사
            for backup_filename, target_path in files_to_restore:
                source_path = os.path.join(backup_path, backup_filename)
                if os.path.exists(source_path):
                    # 대상 파일 경로의 디렉토리 확인
                    target_dir = os.path.dirname(target_path)
                    if not os.path.exists(target_dir):
                        os.makedirs(target_dir)
                    # 파일 복원
                    shutil.copy2(source_path, target_path)
            
            # 설정 다시 로드
            self.load_all_settings()
            
            return True, "백업이 성공적으로 복원되었습니다."
            
        except Exception as e:
            logger.error(f"백업 복원 오류: {e}")
            return False, str(e)

    def get_available_backups(self):
        """사용 가능한 백업 목록 반환"""
        try:
            from utils.paths import get_data_directory
            backup_dir = os.path.join(get_data_directory(), "backups")
            
            if not os.path.exists(backup_dir):
                return []
            
            # 디렉토리만 찾기
            backups = []
            for item in os.listdir(backup_dir):
                item_path = os.path.join(backup_dir, item)
                if os.path.isdir(item_path):
                    # 백업 정보 읽기
                    desc_file = os.path.join(item_path, "description.txt")
                    description = ""
                    if os.path.exists(desc_file):
                        with open(desc_file, 'r', encoding='utf-8') as f:
                            description = f.read().strip()
                    
                    # 생성 시간 구하기
                    created_time = None
                    try:
                        parts = item.split('_')
                        if len(parts) >= 2 and parts[0] == "backup":
                            date_str = parts[1]
                            time_str = parts[2] if len(parts) > 2 else "000000"
                            timestamp = f"{date_str}_{time_str}"
                            created_time = datetime.datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
                    except:
                        # 파일 생성 시간 대신 폴더 수정 시간 사용
                        created_time = datetime.datetime.fromtimestamp(os.path.getmtime(item_path))
                    
                    backups.append({
                        "name": item,
                        "description": description,
                        "created": created_time,
                        "path": item_path
                    })
            
            # 생성 시간 기준으로 최신순 정렬
            backups.sort(key=lambda x: x["created"] if x["created"] else datetime.datetime.now(), reverse=True)
            
            return backups
            
        except Exception as e:
            logger.error(f"백업 목록 로드 오류: {e}")
            return []

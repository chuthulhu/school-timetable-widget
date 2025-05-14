"""
SettingsManager 단위 테스트
"""
import os
import pytest
import json
from utils.settings_manager import SettingsManager
from utils.paths import get_style_settings_file_path

def test_save_and_load_style_settings(tmp_path, monkeypatch):
    # 임시 디렉토리로 데이터 경로 변경
    monkeypatch.setenv('SCHOOL_TIMETABLE_DATA_DIR', str(tmp_path))
    sm = SettingsManager.get_instance()
    sm.header_bg_color = "#123456"
    sm.header_text_color = "#654321"
    sm.save_style_settings()

    # 인스턴스 새로 생성(싱글톤 해제)
    SettingsManager._instance = None
    sm2 = SettingsManager.get_instance()
    sm2.load_style_settings()
    assert sm2.header_bg_color == "#123456"
    assert sm2.header_text_color == "#654321"

    # 파일 직접 확인
    with open(get_style_settings_file_path(), encoding="utf-8") as f:
        data = json.load(f)
        assert data["header_bg_color"] == "#123456"
        assert data["header_text_color"] == "#654321"

def test_save_and_load_widget_position_with_screen_info(tmp_path, monkeypatch):
    """
    위젯 위치/크기/screen_info 저장 및 복원 테스트 (멀티모니터 지원)
    실제 스크린 객체 대신 dict로 모의
    """
    from utils.paths import get_widget_settings_file_path
    monkeypatch.setenv('SCHOOL_TIMETABLE_DATA_DIR', str(tmp_path))
    SettingsManager._instance = None
    sm = SettingsManager.get_instance()
    # 저장
    screen_info = {'geometry': [1920, 0, 1920, 1080], 'name': 'MockScreen1'}
    sm.save_widget_position(200, 300, 400, 500, screen_info)
    # 인스턴스 새로 생성(싱글톤 해제)
    SettingsManager._instance = None
    sm2 = SettingsManager.get_instance()
    sm2.load_widget_position()
    assert sm2.widget_position == {'x': 200, 'y': 300}
    assert sm2.widget_size == {'width': 400, 'height': 500}
    assert sm2.widget_screen_info == screen_info
    # 파일 직접 확인
    with open(get_widget_settings_file_path(), encoding="utf-8") as f:
        data = json.load(f)
        assert data["screen_info"] == screen_info

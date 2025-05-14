"""
테마/스타일 관리 가이드라인
- 테마 정의 및 기본값: utils/config.py (THEMES, DEFAULT_STYLES)
- 스타일 생성 함수: utils/styling.py (generate_header_style 등)
- 테마/스타일 관련 코드는 반드시 위 두 파일만 수정
- 테마 프리셋 추가 시 config.py의 THEMES, styling.py의 get_theme_presets()만 수정
- settings_manager.py 등에서는 import config, import styling만 사용
"""

from PyQt5.QtGui import QColor

def hex_to_rgba(hex_color, opacity):
    """HEX 색상 코드와 불투명도를 RGBA 형식으로 변환
    
    Args:
        hex_color: '#RRGGBB' 형식의 색상 코드
        opacity: 0-255 범위의 불투명도 값
    
    Returns:
        rgba(r, g, b, a) 형식의 문자열
    """
    color = QColor(hex_color)
    return f"rgba({color.red()}, {color.green()}, {color.blue()}, {opacity / 255})"

def generate_header_style(bg_color, text_color, font_family, font_size):
    """헤더 스타일 생성
    
    Args:
        bg_color: 배경색 (rgba 형식)
        text_color: 텍스트 색상 (HEX 형식)
        font_family: 폰트 패밀리
        font_size: 폰트 크기
    
    Returns:
        스타일시트 문자열
    """
    return f"""
        background-color: {bg_color}; 
        color: {text_color}; 
        border-radius: 4px;
        font-family: '{font_family}';
        font-size: {font_size}pt;
        padding: 2px;
    """

def generate_cell_style(bg_color, text_color, border_color, font_family, font_size):
    """셀 스타일 생성
    
    Args:
        bg_color: 배경색 (rgba 형식)
        text_color: 텍스트 색상 (HEX 형식)
        border_color: 테두리 색상 (rgba 형식)
        font_family: 폰트 패밀리
        font_size: 폰트 크기
    
    Returns:
        스타일시트 문자열
    """
    return f"""
        background-color: {bg_color}; 
        color: {text_color}; 
        border: 1px solid {border_color};
        border-radius: 4px;
        font-family: '{font_family}';
        font-size: {font_size}pt;
        padding: 2px;
    """

def generate_current_style(bg_color, text_color, border_color, font_family, font_size):
    """현재 교시 강조 스타일 생성
    
    Args:
        bg_color: 배경색 (rgba 형식)
        text_color: 텍스트 색상 (HEX 형식)
        border_color: 테두리 색상 (rgba 형식)
        font_family: 폰트 패밀리
        font_size: 폰트 크기
    
    Returns:
        스타일시트 문자열
    """
    return f"""
        background-color: {bg_color}; 
        color: {text_color}; 
        border: 2px solid {border_color};
        border-radius: 4px;
        font-family: '{font_family}';
        font-size: {font_size}pt;
        padding: 2px;
        font-weight: bold;
    """

def generate_drag_style(bg_color, text_color, border_color, font_family, font_size):
    """드래그 모드 스타일 생성
    
    Args:
        bg_color: 배경색 (rgba 형식)
        text_color: 텍스트 색상 (HEX 형식)
        border_color: 테두리 색상 (rgba 형식)
        font_family: 폰트 패밀리
        font_size: 폰트 크기
    
    Returns:
        스타일시트 문자열
    """
    return f"""
        background-color: {bg_color}; 
        color: {text_color}; 
        border: 1px dashed {border_color};
        border-radius: 4px;
        font-family: '{font_family}';
        font-size: {font_size}pt;
        padding: 2px;
    """

def get_widget_style(bg_color, fg_color, transparency=0.8):
    """위젯 전체 스타일 생성 (tkinter 호환)
    
    Args:
        bg_color: 배경색 (HEX 형식)
        fg_color: 전경색 (HEX 형식)
        transparency: 투명도 (0.0-1.0)
    
    Returns:
        스타일 딕셔너리
    """
    return {
        "bg": bg_color,
        "fg": fg_color,
        "highlightthickness": 0,
        "borderwidth": 0,
        "relief": "flat",
        "alpha": transparency
    }

def get_theme_presets():
    """사전 정의된 테마 프리셋 목록 반환"""
    return {
        "기본 테마": {
            "header_bg_color": "#6464C8",
            "header_text_color": "#FFFFFF",
            "cell_bg_color": "#FFFFFF",
            "cell_text_color": "#000000",
            "current_period_color": "#FFD700",
            "border_color": "#000000",
            "header_opacity": 120,
            "cell_opacity": 30,
            "current_period_opacity": 150,
            "border_opacity": 200
        },
        "다크 테마": {
            "header_bg_color": "#2D2D2D",
            "header_text_color": "#FFFFFF",
            "cell_bg_color": "#121212",
            "cell_text_color": "#FFFFFF", 
            "current_period_color": "#BB86FC",
            "border_color": "#FFFFFF",
            "header_opacity": 200,
            "cell_opacity": 100,
            "current_period_opacity": 200,
            "border_opacity": 70
        },
        "파스텔 테마": {
            "header_bg_color": "#FFB6C1",
            "header_text_color": "#4B0082",
            "cell_bg_color": "#E6E6FA",
            "cell_text_color": "#4B0082",
            "current_period_color": "#98FB98",
            "border_color": "#FFB6C1",
            "header_opacity": 100,
            "cell_opacity": 80,
            "current_period_opacity": 150,
            "border_opacity": 100
        },
        "고대비 테마": {
            "header_bg_color": "#000000",
            "header_text_color": "#FFFFFF",
            "cell_bg_color": "#FFFFFF",
            "cell_text_color": "#000000",
            "current_period_color": "#FF0000",
            "border_color": "#000000",
            "header_opacity": 255,
            "cell_opacity": 255,
            "current_period_opacity": 255,
            "border_opacity": 255
        }
    }

def generate_hover_style(base_style, additional_opacity=50):
    """마우스 호버 시 적용할 스타일 생성 (불투명도 증가)"""
    # base_style에서 opacity 값을 추출
    import re
    
    # rgba 패턴에서 투명도 추출
    pattern = r'rgba\((\d+),\s*(\d+),\s*(\d+),\s*([\d.]+)\)'
    
    def opacity_replace(match):
        r, g, b, a = match.groups()
        new_a = min(float(a) + (additional_opacity / 255), 1.0)
        return f'rgba({r}, {g}, {b}, {new_a})'
    
    # 모든 rgba 패턴에서 투명도 증가
    hover_style = re.sub(pattern, opacity_replace, base_style)
    return hover_style

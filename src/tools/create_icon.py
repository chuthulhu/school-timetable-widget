"""기본 앱 아이콘 생성 스크립트"""
import os
import sys
from PIL import Image, ImageDraw

def create_default_icon(output_path='src/assets/app_icon.ico', size=(256, 256)):
    """기본 앱 아이콘 생성"""
    # 디렉토리 확인
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # 이미지 생성
    img = Image.new('RGBA', size, color=(100, 100, 200, 255))  # 청색 배경
    draw = ImageDraw.Draw(img)
    
    # 간단한 시간표 모양 그리기
    border = 40
    width, height = size[0] - (2 * border), size[1] - (2 * border)
    
    # 외곽선
    draw.rectangle((border, border, size[0] - border, size[1] - border), 
                  fill=(255, 255, 255, 220), outline=(50, 50, 150, 255), width=4)
    
    # 격자 선
    cell_width = width // 5
    cell_height = height // 7
    
    # 가로선
    for i in range(1, 7):
        y = border + i * cell_height
        draw.line((border, y, size[0] - border, y), fill=(50, 50, 150, 180), width=2)
    
    # 세로선
    for i in range(1, 5):
        x = border + i * cell_width
        draw.line((x, border, x, size[1] - border), fill=(50, 50, 150, 180), width=2)
    
    # 현재 교시 하이라이트
    highlight_x = border + 2 * cell_width
    highlight_y = border + 3 * cell_height
    draw.rectangle(
        (highlight_x, highlight_y, highlight_x + cell_width, highlight_y + cell_height),
        fill=(255, 215, 0, 180)  # 금색
    )
    
    # 저장
    try:
        img.save(output_path)
        print(f"아이콘이 생성되었습니다: {output_path}")
        return True
    except Exception as e:
        print(f"아이콘 생성 실패: {e}")
        return False

if __name__ == "__main__":
    # 커맨드 라인에서 출력 경로를 지정할 수 있음
    output_path = sys.argv[1] if len(sys.argv) > 1 else 'src/assets/app_icon.ico'
    create_default_icon(output_path)

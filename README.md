# School Timetable Widget v2 (Windows)

간단한 바탕화면 시간표 위젯 (Windows 전용). 요일/교시 유연 구성, 자동 업데이트(체크), 알림 없음.

## 요구 사항
- Windows 10/11
- Python 3.10+

## 빠른 실행(개발용)
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install -r requirements.txt
python app\main.py
```

## 설정 파일 위치 및 스키마
- 경로: `%APPDATA%\Timetable\SchoolTimetableWidgetV2\config.json`
- 스키마(v2): 요일/교시/시간, 요일별 시간 override, UI 위치/크기/고정, 테마 토큰 포함

## 테마
- 라이트/다크 프리셋 + 토큰 기반 QSS
- 현재 교시 셀은 강조 스타일 자동 적용

## 빌드(로컬)
```powershell
./build.ps1 -Clean
# 또는 수동 빌드
pyinstaller --noconfirm --name TimetableWidgetV2 --icon assets/app_icon.ico --onefile app\main.py
```

## CI (GitHub Actions)
- 워크플로우: `.github/workflows/build.yml`
- 수동 실행(workflow_dispatch) → Windows 환경에서 빌드 후 `dist/` 아티팩트 업로드

## 프로젝트 구조
```
app/        # UI (메인/위젯/트레이/다이얼로그)
core/       # 도메인(스키마/스케줄 계산)
infra/      # 저장/경로/로깅/테마/업데이트/버전
assets/     # 아이콘 등 정적 자원
settings/   # 초기 config 샘플(필요시)
```

## 라이선스
- TBD



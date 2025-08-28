# 학교 시간표 위젯 (School Timetable Widget)

Windows 트레이 위젯으로 시간표를 항상 데스크톱에 띄워둘 수 있는 PyQt5 기반 앱입니다.

## 다운로드 및 설치(사용자)

1. 최신 버전 다운로드: https://github.com/chuthulhu/school-timetable-widget/releases/latest  
   - `TimetableWidget.exe` 또는 `main.exe`를 다운로드하여 실행합니다.
2. 최초 실행 시 Windows SmartScreen 경고가 나타날 수 있습니다.  
   - "추가 정보" → "실행"을 선택하세요.
3. 별도의 설치 과정 없이 바로 실행됩니다.

## 수동 업데이트 방법
- 새 버전이 출시되면 위의 링크에서 최신 exe 파일을 다시 다운로드하여 덮어쓰면 됩니다.

## 자동 업데이트
- 앱 시작 시 GitHub 릴리스를 확인하여 새 버전이 있으면 안내합니다. (Windows 실행 환경 권장)

---

## 개발 가이드(로컬 실행/테스트/빌드)

### 1) 사전 준비
- Python 3.12 권장(3.9+ 동작 가능)
- OS: Windows 권장(트레이/자동시작은 Windows 전용), Linux/macOS에선 일부 기능 제한

### 2) 개발 환경 준비
```bash
python -m venv .venv
# Windows
. .venv\Scripts\activate
# macOS/Linux
. .venv/bin/activate

pip install --upgrade pip
# 필수 패키지
pip install pyqt5 psutil appdirs requests
# 개발/테스트
pip install pytest
```

### 3) 애플리케이션 실행
```bash
python src/main.py
```
- Linux CI/헤드리스 환경에서는 `QT_QPA_PLATFORM=offscreen`로 실행/테스트합니다.

### 4) 테스트 실행
```bash
pytest -q
```
- SettingsManager 단위 테스트가 포함되어 있습니다.

### 5) Windows 빌드(PyInstaller)
```bash
pip install pyinstaller
pyinstaller TimetableWidget.spec
# 산출물: dist/TimetableWidget/TimetableWidget.exe
```

### 6) 데이터/로그 경로
- appdirs를 사용하여 사용자 데이터 디렉터리에 설정을 저장합니다.
- 주요 파일(자동 생성/저장):
  - timetable_data.json, time_settings.json, style_settings.json, widget_settings.json, notification_settings.json
- 로그: %APPDATA%/SchoolTimetableWidget/logs/*.log

### 7) 자동 시작(Windows)
- 시작프로그램 폴더에 바로가기를 생성/삭제합니다(pywin32 필요). CI/비Windows 환경에서는 자동으로 건너뜁니다.

---

## CI(테스트 자동화)
- GitHub Actions 워크플로우가 설정되어 있습니다: `.github/workflows/ci.yml`
- Python 3.12, Ubuntu 최신, 오프스크린 모드로 pytest 실행

---

## 기여 가이드
- PR 전 테스트 통과 필수
- 큰 산출물(.venv, build, dist 등)은 커밋 금지(.gitignore 적용)
- 이슈/기능 요청은 GitHub Issues 사용

## 라이선스
- 추후 명시(또는 저장소 라이선스 파일 참고)

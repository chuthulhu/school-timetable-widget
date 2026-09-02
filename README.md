
## 다운로드 및 설치

1. [최신 버전 다운로드](https://github.com/chuthulhu/school-timetable-widget/releases/latest)  
   - `main.exe` 파일을 다운로드하여 실행하세요.

2. 최초 실행 시 Windows SmartScreen 경고가 나타날 수 있습니다.  
   - "추가 정보" → "실행"을 선택하세요.

3. 별도의 설치 과정 없이 바로 실행됩니다.

## 수동 업데이트 방법

- 새 버전이 출시되면 위의 링크에서 최신 exe 파일을 다시 다운로드하여 덮어쓰면 됩니다.

## 업데이트 알림

- 앱 시작 시 새 버전이 있는지 확인합니다.
- 새 버전이 있으면 공식 GitHub 릴리스 페이지를 열지 사용자에게 확인합니다.
- 보안을 위해 앱이 실행 파일을 자동으로 다운로드하거나 실행하지 않습니다.

## 개발 환경에서 실행

```bash
pip install pyqt5 pyqt5-tools psutil appdirs win10toast pytest pywin32
python src/main.py
```

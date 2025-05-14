
## 다운로드 및 설치

1. [최신 버전 다운로드](https://github.com/chuthulhu/school-timetable-widget/releases/latest)  
   - `main.exe` 파일을 다운로드하여 실행하세요.

2. 최초 실행 시 Windows SmartScreen 경고가 나타날 수 있습니다.  
   - "추가 정보" → "실행"을 선택하세요.

3. 별도의 설치 과정 없이 바로 실행됩니다.

## 수동 업데이트 방법

- 새 버전이 출시되면 위의 링크에서 최신 exe 파일을 다시 다운로드하여 덮어쓰면 됩니다.

## 자동 업데이트 (예정)

- 향후 앱 내에서 최신 버전 확인 및 자동 다운로드 기능이 추가될 예정입니다.

## 개발 환경에서 실행

```bash
pip install pyqt5 pyqt5-tools psutil appdirs win10toast pytest pywin32
python src/main.py
```

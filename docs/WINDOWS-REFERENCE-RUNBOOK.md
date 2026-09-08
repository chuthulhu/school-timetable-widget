# Windows Reference Runbook

## Purpose

다른 Windows PC/Codex 환경에서 legacy Python 앱을 안전하게 실행하고 behavior comparison을 수행한다.
**M4 COMPLETE / CHARACTERIZED — reconstructed and characterized Golden Reference.**
이는 exact deployed v1.0.1 source recovered 선언이 아니다. 기준 소스와 관찰 범위, 안전한 실행 경계를 함께 보존한다.

## Reference Baseline

| 항목 | 기준 / 실제 확인 |
| --- | --- |
| Repository / branch | `chuthulhu/school-timetable-widget` / `recovery-v1-release` |
| M4 시작 HEAD | `07eaa43de6f55a0d4ba21fb74482dbf539b3636d`, clean tree 확인 |
| M4 기록일 | 2026-09-08 |
| OS | Windows 11, build 26100, AMD64 |
| Python | 3.12.14, 64-bit |
| Interpreter | `C:\CodexVenvs\school-timetable-widget-py312\Scripts\python.exe` |
| PyQt5 / Qt runtime | 5.15.11 / 5.15.2 (`qVersion()`도 5.15.2) |
| 기타 설치 버전 | PyQt5-sip 12.19.0, pytest 9.1.1, psutil 7.2.2, appdirs 1.4.4, requests 2.34.2 |
| 자동 suite baseline | M3 full pytest **226 passed × 2**, 41.44s / 41.21s; [원래 실행 기록](LEGACY-RECOVERY-STATUS.md#m3-completion-and-validation) |
| M4 repository 변경 | docs 4개만; production/tests/dependency/build 무변경, commit/push/PR 없음 |

위 버전은 **실제 설치·실행 환경**이다. repository가 선언한 버전 pin이나 완전한 dependency lock은 아니다.
이번에 다른 물리 PC에서 clone/install을 수행했다는 뜻도 아니다. 아래는 현재 소스와 검증 환경에서 도출한 재현 절차다.
이 HEAD와 미커밋 M4 문서를 구분한다. 최종 문서 commit hash는 아직 없으며 기존 HEAD를 종료 문서 commit이라고 부르지 않는다.

### Evidence vocabulary

- **S — source-confirmed:** 연결된 production source의 구조·분기 확인.
- **Q — Qt/process observation:** TEMP profile과 실제 Qt 객체/이벤트/프로세스 관찰. native 입력 증거가 아님.
- **N — native Windows:** 사용자 Default desktop의 원래 Widget flags에서 사용자 조작과 관찰.
- **H — historical:** 기존 M1/M2/M3 또는 DPI 검증 기록 재사용.
- **UNKNOWN / document-only:** 미실행 범위와 .NET 처리 방침을 명시한 비차단 한계.

## Golden Reference Scope

M1 시간표·교시, M2 설정·appearance, M3 데이터 수명주기에 이어 M4 실행 환경·startup/tray/shutdown을 고정한다.
[시간표](TIMETABLE-BEHAVIOR-SPEC.md), [설정](SETTINGS-BEHAVIOR-SPEC.md),
[데이터 수명주기](DATA-LIFECYCLE-SPEC.md)의 상세 regression을 매번 반복하지 않는다.
실제 autostart 등록/재로그인, toast delivery, 새 EXE build, updater 실행은 이 reference의 exit gate가 아니다.

## Environment Prerequisites

Windows 사용자 interactive desktop, Git, Python 3.12.x, 쓸 수 있는 ASCII-only venv 경로가 필요하다.
현재 known-good patch는 3.12.14다. 다른 patch/OS/Qt에서는 아래 smoke 결과와 실제 버전을 기록한다.
Release executable에서 발견된 Python 3.14는 release 분석 증거이며 reference runtime 요구사항이 아니다.
저장소에 추적된 Linux `.venv`, `build/`, `dist/`는 Windows 실행 환경이나 검증된 배포물로 재사용하지 않는다.

## ASCII-only Virtual Environment

repo 자체는 한글/OneDrive 경로여도 현재 reference 실행이 성공했다. venv는 ASCII-only 경로에 둔다.
검증된 Qt plugin 경로:

```text
C:/CodexVenvs/school-timetable-widget-py312/Lib/site-packages/PyQt5/Qt5/plugins
```

`QT_PLUGIN_PATH`, `QT_QPA_PLATFORM_PLUGIN_PATH` override 없이 QApplication 초기화 exit 0을 확인했고,
같은 venv로 사용자 desktop의 실제 main/tray startup도 성공했다. production에 plugin-path workaround를 추가하지 않는다.

## Clone / Checkout

새 PC의 PowerShell에서, 아직 존재하지 않는 작업 경로를 사용한다. 아래 경로는 예시다.
이미 쓰는 clone에 강제 checkout/reset하지 않는다.

```powershell
git clone https://github.com/chuthulhu/school-timetable-widget.git C:\CodexRepos\school-timetable-widget
Set-Location C:\CodexRepos\school-timetable-widget
git switch recovery-v1-release
git branch --show-current
git rev-parse HEAD
git status --short
```

M4 재현 source baseline은 위의 정확한 HEAD다. branch가 진전했다면 무조건 reset하지 말고,
별도 clone에서 `git switch --detach 07eaa43de6f55a0d4ba21fb74482dbf539b3636d`로 역사적 source를 고정하고
detached 상태임을 기록한다. 아직 미커밋인 이 runbook은 그 historical tree에 들어 있지 않다.
다른 revision 결과를 M4 baseline 결과로 합치지 않는다.

## Install Dependencies

HEAD에는 root requirements.txt/pyproject/lock 및 tracked workflow가 없다.
[README](../README.md)의 선언은 `pyqt5 pyqt5-tools psutil appdirs win10toast pytest pywin32`이며 **모두 unpinned**다.
main이 import하는 requests가 빠져 있고 QR 기능 의존성도 빠져 있다. README의 updater 예정 표현도 현재 소스와 다르다.
dependency 파일은 이번에 고치지 않았다.

다음은 README 복사가 아닌, **현재 검증된 core reference subset**의 명시적 설치 절차다.
새 venv 경로인지 확인한 뒤 실행한다. 기존 venv를 덮어쓰지 않는다.

```powershell
py -3.12 -m venv C:\CodexVenvs\school-timetable-widget-py312
$m4Python = 'C:\CodexVenvs\school-timetable-widget-py312\Scripts\python.exe'
& $m4Python -m pip install PyQt5==5.15.11 PyQt5-Qt5==5.15.2 PyQt5-sip==12.19.0 psutil==7.2.2 appdirs==1.4.4 requests==2.34.2 pytest==9.1.1
& $m4Python -B -c "import sys,requests,psutil,appdirs,pytest; from PyQt5.QtCore import PYQT_VERSION_STR,qVersion; print(sys.version,sys.executable,PYQT_VERSION_STR,qVersion())"
```

Transitive dependencies 전체를 lock한 명령은 아니다. install 실패 시 다른 버전을 조용히 대체하지 말고 차이를 기록한다.
현재 venv에는 pywin32, win10toast, pyqt5-tools, numpy, qrcode, Pillow가 **설치되지 않았다**.
core main/settings/tray와 baseline tests는 이들 없이 실행됐다. pyqt5-tools는 reference startup에 필요하지 않다.

| Optional path | Source dependency / boundary |
| --- | --- |
| 실제 Startup shortcut 생성 | pywin32 / `win32com.client`; 이번 reference에서는 호출 차단 |
| Windows toast 우선 backend | win10toast, 없으면 Qt fallback; 전달은 차단 |
| QR 생성 | qrcode, Pillow |
| 가져오기 dialog import | numpy; camera는 OpenCV/pyzbar, image decode는 pyzbar/Pillow |

Optional image/camera 설치·실행은 최소 smoke 밖이다. image 생성/인식까지 M3 payload 검증에 포함됐다고 해석하지 않는다.

## TEMP Profile Setup

[paths.py](../src/utils/paths.py)는 **이미 존재하는** `SCHOOL_TIMETABLE_DATA_DIR`를 사용한다.
경로만 지정하고 디렉터리를 만들지 않으면 원본 appdirs 경로로 fallback할 수 있다.
main import 자체도 logging을 준비하므로 **import 전에** 설정한다.

PowerShell 변수·환경변수는 reference 전용 shell에서 사용하고 종료 후 그 shell을 닫는다.
시스템/사용자 영구 환경변수나 system clock은 변경하지 않는다.

```powershell
$m4Repo = (Get-Location).Path
$m4Python = 'C:\CodexVenvs\school-timetable-widget-py312\Scripts\python.exe'
$m4Profile = Join-Path ([IO.Path]::GetTempPath()) ('school-reference-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $m4Profile -ErrorAction Stop | Out-Null
$env:SCHOOL_TIMETABLE_DATA_DIR = $m4Profile
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTHONPATH = Join-Path $m4Repo 'src'
```

### Blank / fresh profile

그대로 두면 빈 시간표와 Config 기본값을 load한다. 5 JSON이 startup에서 모두 생성되는 것은 아니다.
main은 `logs/`를 준비하며 JSON은 해당 save trigger에서 생성된다. `src/settings`와 CSV는 자동 seed가 아니다.
M4 offscreen main은 fresh profile, native main은 새 profile에 월~금 1교시 `M4 reference`,
2교시 `TEMP profile`만 넣은 **synthetic fixture**였다. 원본 copied-profile native 검증이라고 부르지 않는다.

### Copied realistic profile

fresh 대신 쓸 때만 실행한다. source 앱의 저장이 끝난 안정된 snapshot을 고르고 원본을 읽기만 한다.
먼저 source 경로를 실제 확인해 입력한다. `appdirs.user_data_dir('SchoolTimetableWidget','TimeTableDev')`가 기본 경로지만
원래 앱도 override를 썼을 수 있다. 읽기 거부를 파일 없음으로 취급하지 않는다.

```powershell
$m4Source = Read-Host '복사할 원본 profile의 절대 경로'
$m4Names = @('timetable_data.json','time_settings.json','style_settings.json','widget_settings.json','notification_settings.json')
$m4Before = foreach ($name in $m4Names) {
    $sourceFile = Join-Path $m4Source $name
    if (Test-Path -LiteralPath $sourceFile -ErrorAction Stop) {
        $item = Get-Item -LiteralPath $sourceFile -ErrorAction Stop
        [pscustomobject]@{Name=$name; Hash=(Get-FileHash -LiteralPath $sourceFile).Hash; Mtime=$item.LastWriteTimeUtc.Ticks}
        Copy-Item -LiteralPath $sourceFile -Destination (Join-Path $m4Profile $name) -ErrorAction Stop
    }
}
$m4Before | Format-Table
```

종료 후 같은 source 파일의 hash/mtime와 비교한다. 없는 파일은 복사하지 않으며 defaults로 읽는다는 점을 기록한다.
`logs/`, `backups/`, Startup shortcut은 5파일 copy에 포함되지 않는다. 원본 profile로 역복사하지 않는다.
아래 safe launcher가 copied notification/autostart 값을 읽더라도 OS side effects는 차단한다.

## Safe Reference Launch

**DO NOT use updater during reference validation.** `python src/main.py`를 그대로 실행하지 않는다.
TEMP만으로 updater network, Startup shortcut sync, notification delivery가 격리되지는 않는다.
현재 production에는 이를 모두 끄는 reference CLI switch가 없다.

아래는 process-local boundary replacement를 사용하는 **isolated full-main launch**다.
source 파일을 수정하거나 별도 test/helper 파일을 추가하지 않는다. runbook의 명령이며 제품 기능이 아니다.
앞 절의 기존 TEMP·repo·interpreter 변수와 전용 shell에서 실행한다.

```powershell
$env:QT_QPA_PLATFORM = 'windows'
Remove-Item Env:QT_PLUGIN_PATH -ErrorAction SilentlyContinue
Remove-Item Env:QT_QPA_PLATFORM_PLUGIN_PATH -ErrorAction SilentlyContinue
@'
import os, sys, tempfile
from pathlib import Path
profile = Path(os.environ['SCHOOL_TIMETABLE_DATA_DIR']).resolve()
assert profile.is_dir(), 'Create the unique TEMP profile BEFORE imports'
assert profile.parent == Path(tempfile.gettempdir()).resolve()
assert profile.name.startswith('school-reference-'), 'Use the runbook unique TEMP profile'
os.environ['SCHOOL_TIMETABLE_DATA_DIR'] = str(profile)
sys.path.insert(0, str(Path('src').resolve()))
import utils.auto_start as auto
def simulated_success(*args, **kwargs):
    print('REFERENCE: OS autostart mutation suppressed', flush=True)
    return True
auto.enable_auto_start = simulated_success
auto.disable_auto_start = simulated_success
auto.is_auto_start_enabled = lambda *args, **kwargs: False
import main
main.Updater.check_for_update = lambda self: False
main.ApplicationManager._sync_auto_start_setting = lambda self: None
main.NotificationManager.show_notification = lambda *args, **kwargs: None
print('REFERENCE PROFILE:', profile, 'PID:', os.getpid(), flush=True)
sys.exit(main.main())
'@ | & $m4Python -B -
$m4ExitCode = $LASTEXITCODE
Write-Output "Reference exit code: $m4ExitCode"
```

Settings Apply에서 쓰는 autostart module 함수도 차단한다. 반환 True는 **simulation**이며 OS 등록 성공 증거가 아니다.
notification manager는 실제 JSON을 load하지만 delivery 함수는 no-op이다. updater check를 False로 대체해
download/prompt 분기로 진입하지 않는다. 이것을 unmodified full-main 또는 notification/autostart 검증이라고 부르지 않는다.
stdin launch의 `sys.argv[0]`도 production script path와 다르므로 shortcut target 검증에 사용하지 않는다.
이 실행에서는 tray·manager·Widget·cleanup production 흐름과 원래 window flags를 유지한다.
`.py` entry의 `multiprocessing.freeze_support()`는 Python 모드에서 실행 의미가 없는 frozen 준비 경계로,
위 `main.main()` 호출이 frozen `__main__` packaging 전체를 검증하는 것은 아니다.

다른 앱에서 작업 중이면 native 실행·입력을 조율한다. Codex에서 foreground 실행을 시작할 때는
**현재 사용자 desktop에 실행되는지 확인**한다. sandbox의 별도 desktop에서 실행된 QApplication/tray는 사용자 화면 증거가 아니다.
필요한 sandbox 밖 실행 승인은 구체적인 위 명령에 한정한다. 승인 없이 system 설정을 바꾸거나 VM을 설치하지 않는다.

### New-PC pytest smoke

새 환경에서는 visible launch 전에 core 설치 smoke를 실행할 수 있다. 현재 M4 작업에서 full pytest를 다시 돌린 기록은 아니다.
별도 fresh TEMP profile을 앞 절대로 만들고, 아래를 실행한 뒤 native용으로 또 새 profile을 만든다.

```powershell
$env:QT_QPA_PLATFORM = 'offscreen'
& $m4Python -B -m pytest src/utils/test_settings_manager.py -q -p no:cacheprovider --basetemp (Join-Path $m4Profile 'pytest-temp')
$m4TestExitCode = $LASTEXITCODE
Write-Output "Smoke exit code: $m4TestExitCode"
```

정상 기대는 exit 0이다. 필요 시 같은 환경에서 root `-m pytest -q`를 사용하되 TEMP/cache 옵션을 유지한다.
현재 회수된 full baseline은 226 passed × 2다. 소스/tests 무변경인 docs-only M4에서 전체 suite를 반복하지 않았다.

## Full Main vs Isolated Widget Launch

[main.py](../src/main.py) startup 순서 (S):

1. import 시 logging/data 경로 준비.
2. `main`: exception hook/version → updater check. **single-instance check는 없다.**
3. ApplicationManager: 환경/version 설정, frozen인 경우에만 누락 default CSV copy 시도.
4. run: signals·atexit 등록 → QApplication → `quitOnLastWindowClosed(False)` → aboutToQuit cleanup 연결.
5. SettingsManager → NotificationManager → autostart sync → Widget 생성·cleanup callback 연결·show.
6. TrayIcon 생성 → show/exit action 연결 → tray show → event loop.
7. 종료 후 common cleanup 재호출(중복 방지) → exit code 반환, atexit final cleanup.

SettingsManager + Widget만 만드는 과거 launcher는 dialog/geometry 비교에 유용하지만 2–7 전체 증거가 아니다.
**Unmodified full main is unsafe for a side-effect-free reference without updater/autostart/notification isolation.**
최소 isolated main을 확보했으므로 unmodified main을 억지로 실행할 필요가 없다.

## Tray / Hide / Show / Exit

[tray_icon.py](../src/tray_icon.py): 아이콘은 `assets/app_icon.ico` → `assets/icon.ico` → theme fallback이다.
왼쪽 단일 클릭의 Trigger는 visible 상태를 hide/show toggle한다. context menu는
**시간표 보기 / 버전: v1.0.0 (disabled) / 종료**이며 구분선을 포함한다. tray에 Settings action은 없다.
보기는 Widget.show, 종료는 ApplicationManager.safe_exit에 연결된다. startup은 visible이며 hidden 상태를 저장하지 않는다.

설정은 Widget 우클릭 → **설정**이다. 같은 메뉴에 시간표 편집, 시간 설정, 위치 고정,
공유 및 백업, 종료가 있다. Widget 메뉴 종료는 Widget.close → closeEvent → common cleanup이다.
main Widget은 Tool + Frameless + WindowStaysOnBottomHint, 주요 dialog는 top hint다.
OS 겹침/taskbar 동작 전체를 flags 값 확인만으로 VERIFIED라 하지 않는다.

## Single Instance

현재 Python entry에는 mutex/lock file/IPC/process-name 기반 guard가 **없다** (S).
두 번째 실행의 즉시 종료·첫 instance focus/show·duplicate 경고 구현도 없다.
두 프로세스/두 tray가 가능하다는 것은 소스에서의 추론이며 이번 native A/B 동시 실행은 생략했다.
서로 다른 TEMP profiles로 A/B 실행할 수 있으나 원본 profile에 concurrent writers를 만들지 않는다.

Process manager는 자기 PID의 children을 종료하는 cleanup이며 single-instance manager가 아니다.
frozen 분기에도 guard는 없지만 release EXE의 관찰 결과를 뜻하지 않는다.
[process_killer.py](../src/process_killer.py)는 별도 공격적 이름/cmdline 기반 종료 도구다.
main의 광범위 Python killer 호출은 비활성 상태이며 **reference에서는 이 도구를 실행하지 않는다**.

## Autostart Semantics

[auto_start.py](../src/utils/auto_start.py)는 Registry가 아닌 현재 사용자 Startup shortcut을 쓴다:

```text
%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\SchoolTimetableWidget.lnk
```

Startup 폴더가 없으면 경로 생성에 실패한다. detection은 `.lnk` 존재 여부뿐이며 target/arguments 유효성은 검사하지 않는다.
enable은 WScript.Shell/CreateShortcut/save로 기존 이름의 shortcut을 덮어쓸 수 있다.
disable은 존재하면 삭제, 이미 없으면 True다. 실패/pywin32 ImportError는 log 후 False다.
일반적으로 관리자 권한을 요구하는 전역 Registry 등록 구조가 아니다.

| Mode | Target semantics (S) |
| --- | --- |
| Python | `abspath(sys.argv[0])`; .py/.pyw면 인접 pythonw.exe가 있을 때 TargetPath=pythonw.exe, 없으면 sys.executable, Arguments=quoted script path |
| Frozen | TargetPath=sys.executable, 별도 Python script arguments 없음 |
| WorkingDirectory / icon | 기본 target dirname / 전달한 icon 또는 target |

main startup은 JSON의 auto_start_enabled와 shortcut 존재를 비교한다. false/true 불일치이면 **기존 shortcut도 삭제**한다.
enable 실패면 JSON 옵션을 false로 바꾸며, disable 실패는 log만 남긴다. 둘 다 true이면 target이 잘못돼도 sync는 수정하지 않는다.
Settings Apply는 별도로 enable/disable을 호출하며 실패 warning, enable 실패 시 checkbox/JSON false 보정을 한다.
TEMP 환경변수를 shortcut에 기록하는 기능은 없으므로 reference profile autostart 등록은 안전한 격리법이 아니다.

M4 read-only baseline/종료 후: 위 Startup 폴더는 존재, 해당 `.lnk`는 **없음**, 따라서 읽을 target도 없음.
실제 enable/disable/재로그인은 실행하지 않았다. 원본 5 JSON hash/mtime도 전후 동일했다.
다른 PC에 기존 shortcut이 있으면 target·arguments·working directory를 읽어 기록만 하고 덮어쓰지 않는다.
실제 등록 시험은 baseline 완전 복원이 보장되는 별도 승인 범위이며 Golden Reference MUST가 아니다.

## Notification Boundary

[NotificationManager](../src/notifications/notification_manager.py)는 settings manager 다음에 singleton으로 생성되며
notification JSON의 enabled/next warning/minutes를 load한다. 기본 true/true/5, Settings Apply/OK에서 저장한다.
Widget.update_current_period의 호출 조건과 누락되는 예고 callback은 [M1 quirk L7](TIMETABLE-BEHAVIOR-SPEC.md#known-legacy-quirks)을 따른다.

Windows delivery: win10toast ToastNotifier(threaded=True, 5초) 우선 → ImportError이면 별도 QSystemTrayIcon.showMessage(3초).
이는 main tray를 공유하는 경로가 아니다. outer error에서는 QMessageBox fallback을 시도한다.
Qt fallback icon 수명이나 OS delivery 성공은 미검증이다. **실제 toast delivery는 document-only, exit blocker 아님**.
safe launcher는 show_notification을 차단하므로 notification 설정을 바꿔도 toast를 보내지 않는다.

## DPI / Multi-Monitor Smoke

[기존 Windows 실측](LEGACY-RECOVERY-STATUS.md#manual-windows-verification)을 재사용한다 (H):
100% / 96 DPI ↔ 125% / 120 DPI, actual 488×473 → 610×591 → 488×473,
양축 scaling, margin/spacing, HFW, design preferred 보존, 왕복 A/C PNG hash 일치.
이는 그 fixture의 결과이며 모든 폰트·시간표에서 고정 픽셀을 요구하지 않는다.

이번 M4 Default desktop native run은 DISPLAY1 **96 DPI**, 새로운 100→125→100 왕복은 **미실행**이다.
초기 sandbox probe에서 보인 두 screen 96 DPI 값을 사용자 desktop의 두 monitor scaling으로 일반화하지 않는다.
새 PC에 이미 100/125% 두 화면이 있으면 한 번 옮겼다 돌아와 심한 clipping/누적 확대/위치 소실이 없는지 확인한다.
사용자 작업 중 OS scale이나 system clock을 임의 변경하지 않는다. 장비가 없으면 N/A와 기존 evidence 링크를 기록한다.

사라진 monitor는 `_get_target_screen` primary fallback 및 startup geometry clamp가 소스에 있으나
이번 native hot-unplug/startup은 미실행 document-only다. 저장된 geometry에는 source-DPI metadata가 없어
다른 DPI에서 저장한 size의 완전한 design-unit 복원을 보장하지 않는다.

## Shutdown and Persistence

safe_exit: Widget/tray hide → cleanup_resources → QApplication.quit.
Widget.closeEvent: Widget pending finalize → screen signal disconnect → cleanup callback → app.quit/event.accept.
cleanup_resources: **Widget pending finalize → SettingsManager pending flush → timers/processes 정리**.
Widget finalize 실패에도 manager flush는 시도한다. `_cleanup_done`으로 반복 cleanup을 막는다 (S/H).

실제 children terminate → 1초 wait → 남은 child kill, multiprocessing children 정리도 포함한다.
스레드 강제 종료는 구현되지 않았으며 모든 timer/child/강제 종료를 완전히 보장한다는 뜻이 아니다.
이번 진단에는 앱이 만든 작업 child가 없었다. OS kill/power loss는 정상 flush 계약 밖이다.

M4 Q: offscreen isolated main에서 fresh profile로 tray QAction.trigger와 Widget.close를 별도 프로세스에서 수행했다.
630×580 요청 후 Widget 지연 확정 중 즉시 종료했고 최종 JSON 630×580, cleanup true, process exit 0이었다.
그 시점 manager pending은 false였으므로 **이미 manager queue에 있던 snapshot을 새로 검증했다고 주장하지 않는다**.
Widget finalize가 만든 최종 저장의 main 통합 sanity이며 상세 40ms/250ms 계약은 기존 tests를 재사용한다.

M4 N/Q: 실제 tray exit 뒤 최종 position (861,220), size 440×375, cleanup true, exit 0,
해당 PID 종료를 확인했다. 같은 TEMP의 새 main process에서 geometry (861,220,440,375)를 관찰했다.
사용자는 위치 복원을 확인했고 크기 육안 비교는 불확실하다고 답했다. 크기는 **JSON/Qt geometry Q 증거**로 한정한다.
재실행 앱도 소유한 stop marker를 observer가 읽어 production safe_exit를 호출했고 exit 0이었다.

## M4 Native Evidence Record

| Input / condition | Observation | Evidence |
| --- | --- | --- |
| 첫 sandbox 실행 | CodexSandboxDesktop, Qt visible/tray true였지만 사용자에게 안 보임; 정상 종료 0 | Q, native visible 증거에서 제외 |
| 사용자 desktop 재실행 | Default desktop, 원래 flags 67110923 유지, 사용자 위젯 확인 | N/Q |
| Tray 우클릭 | 보기/version/종료 메뉴 사용자 확인, aboutToShow·Context activation 기록 | N/Q |
| Tray 왼쪽 클릭 | 사용자 숨김 확인, Trigger activation 후 visible=false | N/Q |
| Tray ‘시간표 보기’ | 사용자 복귀 확인, show action 후 visible=true | N/Q |
| Widget 우클릭 ‘설정’ → 취소 | 사용자 열림·닫힘 확인 | N; 별도 dialog 계측 없음 |
| Move / resize | 사용자 resize 확인, observer가 최종 (861,220,440,375) 기록 | N/Q |
| Tray ‘종료’ | 사용자 widget/icon 소실, exit action cleanup=true, main exit 0, PID 종료 | N/Q |
| 같은 TEMP 재실행 | 사용자 위치 일치; 크기 육안 UNKNOWN, Qt/JSON 크기는 동일 | N/Q |
| DPI 왕복 / lock drag / taskbar·overlap 전체 matrix | 이번 추가 native 미실행 | H 재사용 또는 S/document-only |

현재 computer-use 창 목록은 실제 Default desktop의 이 Tool 창도 반환하지 않았다.
이것은 **discovery limitation**이고 capture/input 실패를 직접 입증하지 않는다. 가짜 window 객체나 flags 변경을 사용하지 않았다.
사용자 직접 입력 + TEMP observer를 사용했으며 OS 입력 자동화 성공이라고 보고하지 않는다.
diagnostic observer는 읽기·종료 요청만 추가했고 production/tests 파일과 사용자 OS 설정은 바꾸지 않았다.
원본 5 JSON SHA-256/mtime 전후 동일, Startup shortcut 전후 부재, 소유 진단 3개 프로세스 모두 exit 0.
TEMP observer/log/JSON은 로컬 진단 자료이며 영구 artifact가 아니다. 이 표가 절차·관찰의 저장소 기록이다.

## Minimal Smoke Checklist

환경 설치를 제외하고 약 10분, 매 항목 PASS/FAIL/N/A와 environment/profile/revision을 기록한다.

- [ ] 정확한 Python/Qt/revision 및 기존 TEMP 경로 확인; safe launcher 사용.
- [ ] 사용자 desktop에서 앱 시작·Widget 표시·시간표 내용 load 확인 (blank면 빈 시간표 정상).
- [ ] Widget 메뉴에서 설정 열기 → 취소로 닫기.
- [ ] Tray icon 우클릭 메뉴, 왼쪽 클릭 숨김, 보기 action 복귀.
- [ ] 잠금 해제 상태에서 move/resize; 최종 위치·크기 기록.
- [ ] 사용 가능한 100/125% 화면에서 한 번 DPI 왕복; 없으면 N/A 사유 기록.
- [ ] Tray 종료로 widget/icon 소실, exit 0 및 소유 PID 종료 확인.
- [ ] TEMP widget JSON 최종 값 확인, **같은** TEMP로 재시작하여 위치·크기/데이터 복원 확인.
- [ ] 재시작 앱 정상 종료, 원본 profile/Startup baseline 불변 확인.
- [ ] 필요할 때만 백업/복원 목록 열기; destructive restore/QR scan은 최소 smoke 밖.

## Troubleshooting

### Qt plugin path / Korean OneDrive path

기존 Korean/OneDrive repo 내부 `.venv-win`에서 Qt plugin 경로의 한글이 `????????`로 해석돼
QApplication 초기화가 hang한 사례가 인계됐다. 모든 OneDrive repo가 실패한다는 일반화는 아니다.
repo는 유지하고 venv만 ASCII-only 위치에서 만든다. `sys.executable`, `QLibraryInfo.PluginsPath`,
`QApplication.platformName()`을 기록한다. plugin override 없는 현재 성공 경로를 우선 사용한다.
진단은 bounded timeout과 소유 PID 종료를 사용하고 Qt DLL을 임의 복사하거나 production 환경변수 patch를 넣지 않는다.

### Wrong Python/Qt

venv activate 상태에 의존하지 말고 절대 interpreter를 실행한다. bundled/tracked `.venv`나 release EXE runtime을 섞지 않는다.
pyqt5-tools 설치가 core 검증의 전제가 아니다. Python/Qt 차이가 있으면 baseline과 구분한다.
Widget import는 `QT_LOGGING_RULES=qt.qpa.*=false`를 설정한다. 로그가 조용하다는 사실은 warning 전체 부재 증거가 아니다.

### Data directory

폴더 생성 → 환경변수 설정 → import 순서를 지킨다. actual resolved profile을 출력하고 원본 경로이면 중단한다.
malformed style JSON은 manager startup을 중단할 수 있다. 원본을 고치지 말고 새 blank TEMP와 비교한다.
한 TEMP에 여러 instance를 쓰지 않는다. 복원 시험의 disk/runtime 차이는 M3 명세를 따른다.

### Existing process

guard가 없으므로 기존 앱을 자동 탐지해 focus시켜 준다고 기대하지 않는다. PID·시작 시각·desktop·profile을 구분한다.
진단 앱만 tray Exit/safe_exit로 종료한다. 이름 기준 전체 python 종료나 process_killer.py는 사용하지 않는다.

### Tray not visible

먼저 사용자 알림 영역 `^`를 확인한다. Qt `isVisible/isSystemTrayAvailable=True`만으로 사람이 보는 icon을 입증할 수 없다.
M4에서 실제로 sandbox 별도 desktop이 원인이었다. 프로세스의 desktop과 사용자 desktop이 같은지 확인한 뒤
승인된 interactive 환경에서 한 번 재실행한다. Tool 창 discovery 누락과 sandbox desktop 격리는 서로 다른 문제다.
Main Widget은 bottom hint이므로 다른 창에 가려질 수 있다. normal-window wrapper로 바꾸어 성공해도 원래 flags의 증거로 대체하지 않는다.

## Known Limitations

M1/M2/M3의 legacy quirks, source-DPI metadata 부재, QSS 고정 px, native warning 범위는 기존 명세대로 유지한다.
이번 새 native single-instance A/B, lock/overlap/taskbar 전체, monitor 제거, toast, Startup 재로그인,
frozen EXE 동등성, fresh physical PC install은 미실행이다. 각각 source/document-only 또는 별도 환경 smoke로 남는다.
현재 사용자 요청의 M4 범위에서 **비차단**이며 정상 reference startup/tray/save/restart를 막는 결함은 관찰되지 않았다.
다른 PC에서 문제가 나면 environment 차이를 기록하며 기존 VERIFIED 범위를 확대하지 않는다.

## Do Not Use During Reference Validation

- updater check/download/새 EXE 실행: historical release tag v1.0.1 / embedded 1.0.0 mismatch로 반복 prompt 가능.
- production autostart mutation 및 원본 profile destructive tests.
- aggressive process killer, system clock 변경, 무승인 OS 설정 변경.
- tracked dist/build를 검증된 공개 release로 배포하는 작업.

Updater는 **B: 문서화 후 .NET에서 대체**, build/release는 **B: source reference 실행 확보, pipeline은 .NET에서 구축**으로 disposition한다.
두 spec 모두 src/main.py/console=False이며 [main.spec](../main.spec)은 assets data 미지정,
[TimetableWidget.spec](../TimetableWidget.spec)은 src/assets를 bundle한다. version resource/현 HEAD workflow는 없다.
역사적 v1.0.1 workflow는 Python 3.10·app/main.py·TimetableWidgetV2 artifact upload로 다른 계통이다.
release EXE 재배포·byte-identical build·updater 수리는 Golden Reference exit blocker가 아니다.

## Golden Reference vs .NET Rewrite

**Golden Reference = behavior reference, NOT implementation template.**
이 Python branch는 legacy behavior comparison target과 migration evidence다.
future production architecture, 새 .NET implementation template, current public release candidate를 뜻하지 않는다.
새 구현은 각 명세의 **MATCH / COMPATIBLE / REDESIGN**을 따른다. 정상 사용자 동작은 비교하고,
legacy JSON 의미는 호환하며, 손실·lifecycle·scheduler·updater 등 알려진 구조는 별도로 설계한다.
Notion에서 정한 위 원칙과 같은 취지를 기록한 것이며 이번에 외부 Notion 문서를 새로 조회·수정하지 않았다.

## Documentation Validation

M4 최종 문서의 로컬 링크와 PowerShell/Python snippet 문법을 검사했다. Safe launcher의 Python 본문은
별도 fresh TEMP + offscreen + QApplication 자동 종료 timer를 주입해 실행, exit0을 확인했다.
이는 문서 명령의 core 실행 sanity이며 새 native 입력이나 전체 pytest 검증이 아니다.
새 파일을 포함한 공백 검사와 git diff --check를 수행하며 허용된 docs4개 외 변경은 없다.

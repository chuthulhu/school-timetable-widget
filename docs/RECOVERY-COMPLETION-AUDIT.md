# Recovery Completion Audit

## Executive verdict

**Geometry·DPI·widget persistence의 Golden Reference는 확보했다. 전체 앱의 Golden Reference 확정은 아래 M1–M4, 네 개의 행동 검증 묶음을 닫은 뒤 권고한다.** 네 개의 구현 결함을 고쳐야 한다는 뜻은 아니다. 필요한 것은 남은 사용자 동작의 명세와 재현 가능한 증거이며, 참조 사용을 막는 결함만 최소 수정 대상으로 삼는다. 근거 없는 완료 퍼센트는 사용하지 않는다.

기준은 `recovery-v1-release` / `7a27e4192a0b6d13a9d18a193b1770b6abb58c2c`다. 2026-09-07 시작 시 branch/HEAD/clean을 확인했다. 이번 작업은 production/test를 실행하거나 수정하지 않은 문서 감사다. 기존 95 passed와 Windows 결과는 [상태 문서](LEGACY-RECOVERY-STATUS.md)에 출처와 범위를 고정했다.

**RECOMMENDED:** updater는 **B — 동작을 문서화하고 .NET에서 대체**, build/release는 **B — local/reference execution을 확보하고 release pipeline은 .NET에서 구축**한다. 다른 PC에서도 사용할 수 있는 실행 환경·데이터 준비 절차는 필요하지만, legacy EXE 재배포나 byte-identical build는 종료 조건으로 두지 않는다.

## Evidence and audit coverage

VERIFIED / INFERRED / UNKNOWN / RECOMMENDED는 [상태 문서](LEGACY-RECOVERY-STATUS.md)의 정의를 따른다. 표의 **V**는 VERIFIED, **P**는 PRESENT / NOT FULLY VERIFIED, **K**는 KNOWN BROKEN, **R**은 MISSING / RELEASE-EVIDENCE ONLY, **O**는 OUT OF SCOPE FOR GOLDEN REFERENCE다. 소스에서 기능을 찾았다는 사실만으로 V가 되지는 않는다. K도 정적으로 확인한 구조와 실행 결과를 구분한다.

| Area | 검토 근거 및 범위 |
| --- | --- |
| Entry / lifecycle / updater | [main.py](../src/main.py)의 main, Updater, ApplicationManager, cleanup, autostart sync |
| Core widget | [widget.py](../src/gui/widget.py)의 렌더링, 시간 갱신, mouse, flags, DPI, menu, close |
| Dialogs | [settings](../src/gui/dialogs/settings_dialog.py), [time](../src/gui/dialogs/time_dialog.py), [timetable](../src/gui/dialogs/timetable_dialog.py), [backup](../src/gui/dialogs/backup_dialog.py), [import](../src/gui/dialogs/import_dialog.py), [QR share](../src/gui/dialogs/qr_share_dialog.py) |
| Utils / style | [settings_manager](../src/utils/settings_manager.py), [paths](../src/utils/paths.py), [config](../src/utils/config.py), [styling](../src/utils/styling.py), [version](../src/utils/version.py), [exceptions](../src/utils/exceptions.py), theme/color UI components |
| Windows | [tray_icon.py](../src/tray_icon.py), [auto_start.py](../src/utils/auto_start.py), [notification_manager.py](../src/notifications/notification_manager.py), [process_killer.py](../src/process_killer.py) |
| Tests | [test_settings_manager.py](../src/utils/test_settings_manager.py), [test_v101_recovery_contracts.py](../src/utils/test_v101_recovery_contracts.py); 기존 95 passed 기록은 인계 자료 |
| Build / release | [main.spec](../main.spec), [TimetableWidget.spec](../TimetableWidget.spec), [README](../README.md), tracked build/dist/venv 목록, HEAD와 tag의 tree 및 workflow 이력 |

Git 확인: safe point `d9756a6`부터의 5 recovery commits는 상태 문서의 표와 일치한다. `7fd6695`는 updater 추가, `de8e449` / `0aecbc4`는 설정·자동 실행 관련 이력이다. `v1.0.1` tree는 app/core/infra의 v2 계열이며, 인계된 legacy EXE의 내부 구조와 다르다.

다른 계통의 `5ed5f28b962179e6da8376f24f6b3c41aaa39494`는 updater를 release 페이지 안내로 바꾸고 backup을 강화했다. 기준 HEAD에는 포함되지 않은 변경이므로 현재 기능으로 서술하지 않는다. Tauri 이력은 확인된 역사적 배경으로 받아들이며 현재 baseline에 병합하지 않는다. 이번 감사에서 EXE를 다시 다운로드하거나 역분석하지 않았다.

## Feature inventory

### Core widget

| Feature | Status | 현재 증거 / 부족한 증거 | .NET 전 처리 |
| --- | --- | --- | --- |
| Timetable rendering | P | 5요일×7교시, 48 QLabel, 본문 word wrap. DPI 실측은 있지만 내용 편집·공백·저장 왕복의 전체 계약 없음 | MUST M1 |
| Current-period highlight | P | 시작/종료 모두 inclusive, 첫 일치 교시 반환. 평일의 해당 셀 강조. 경계·중복·주말 계약 없음 | MUST M1 |
| Position persistence / clamp | V, 범위 제한 | JSON 왕복, 음수 좌표 clamp, move 직후 cleanup의 기존 Windows 결과 | 유지, 사라진 화면에서 startup은 M4 |
| Resize / minimum / HFW | V | font minimum, actual/preferred, drag settle, Windows 결과 | 유지 |
| DPI / multi-monitor | V, 범위 제한 | 96↔120 DPI Windows 왕복, margin/hint/HFW 복귀. 모든 모니터 구성을 보장하지 않음 | 유지 |
| Hide/show geometry | V | signal 재연결 테스트와 settings size의 Windows hide/show | tray 입력 자체는 M4 |
| Transparency/background | P | WA_TranslucentBackground, RGBA/QSS, 네 가지 opacity. 설정 변경별 비교 이미지 부족 | MUST M2 |
| Always-on-top / window flags | P | **main widget은 WindowStaysOnBottomHint + Tool + FramelessWindowHint**. always-on-top toggle 없음. 주요 dialog는 top hint | MUST M4에서 실제 겹침 확인 |
| Drag move / resize / lock | P, 저장 부분 V | 오른쪽 아래 20px resize, lock 상태에서도 resize 허용. lock 조작의 전체 Windows 계약 부족 | MUST M4 |

### Settings and data

| Feature | Status | 현재 증거 / 부족한 증거 | .NET 전 처리 |
| --- | --- | --- | --- |
| Font / font size | P | header/body 개별 font, 이전 font fallback, preview. minimum은 V지만 Cancel/재시작 전체는 미검증 | MUST M2 |
| Colors / theme | P / K4 | 두 색상의 저장 테스트. light/dark 선택은 즉시 disk 저장, Cancel은 disk를 복원하지 않음 | MUST M2 |
| Opacity | P | UI 0–100에서 저장값 0–255로 정수 변환, 네 종류. 반올림·취소 의미 미검증 | MUST M2 |
| Widget size | V | settings→user request→acceptable actual 저장, hide/show, DPI 왕복 | 유지 |
| Timetable content | P | 여러 줄 편집, 같은 요일 merge/split, 연속 같은 과목 추정 merge. main은 독립 셀 표시 | MUST M1, 마지막 7교시 포함 |
| Time/period settings | P | 7교시 HH:mm 저장. 중복·역전 validation 없음 | MUST M1 |
| Reset/default | P / K5 | Config 기본값, 전체 factory reset UI 없음. 위치 reset은 manager 값 변경, Apply에 move 없음 | MUST M2 |
| Backup/restore UI | P | manager flush/명시적 이름은 V. 5파일 복사, UI는 재시작 안내. 전체 GUI 계약 부족 | MUST M3 |
| Widget settings | V | position/size/lock/screen_info/autostart, missing/corrupt JSON, snapshot/flush | 유지 |
| Timetable persistence | P | JSON 전체 read/write, 로드 실패 시 빈 dict. 내용 왕복 테스트 부족 | MUST M1/M3 |
| Period/time persistence | P | 문자열 key↔int, HH:mm↔QTime, 기본값 위에 저장값 로드 | MUST M1/M3 |
| Style persistence | P | 두 색상의 저장/로드만 V, 나머지 field 및 transaction 부족 | MUST M2/M3 |
| Notification persistence | P | 별도 NotificationManager의 3값 read/write. SettingsManager의 같은 이름 초기값과 별개 | MUST M3 |
| Debounce / atomic write | V, widget만 | 250ms coalescing, 같은 디렉터리 replace, 실패 시 기존 파일 보존 | 유지 |
| Atomic all-data / transactional backup | O | 나머지 JSON은 직접 write, backup은 개별 copy | SHOULD document, 전체 재설계 SKIP |
| QR export / image-camera import / JSON import | P | Base64 UTF-8 JSON, PNG 저장, 선택 데이터 덮어쓰기. optional dependency 포함 전체 계약 없음 | payload는 M3, camera/decoder 수리는 SKIP |

### Windows integration, update, build

| Feature | Status | 현재 증거 / 부족한 증거 | .NET 전 처리 |
| --- | --- | --- | --- |
| Tray | P | 왼쪽 클릭 hide/show, 표시·version·종료 메뉴, manager에서 action 연결 | MUST M4 |
| Autostart | P | 현재 사용자 Startup의 SchoolTimetableWidget.lnk, WScript.Shell, 시작 시 sync. 테스트는 JSON 옵션만 | MUST M4에서 on/off/재로그인 확인 |
| Single instance | O, 현재 없음 | entry에 mutex/IPC guard 없음. process cleanup은 단일 실행 기능이 아님 | SHOULD document, .NET 새 설계 |
| Process/application manager | P | 자기 child terminate→kill, signal/atexit, 중복 cleanup 방지. 테스트는 process stub | 정상 종료 M4, aggressive killer 이식 SKIP |
| Startup | P | logging/data dir, update check, QApplication, settings/notification/widget/tray, frozen CSV copy | MUST M4, fresh/existing profile |
| Shutdown persistence | V | Widget 확정→manager flush, 15ms 종료·move 직후 기존 Windows 결과 | native tray/context 종료 전체는 M4 |
| Notification | P / K3 | 교시 변경 시에만 check. 보통의 5분 전·쉬는 시간에 예고가 빠지는 경로. native toast 미검증 | M1 시각 계약, M4 표시 확인, backend 수리는 document-only |
| Version detection | V, 숫자 비교만 / K1 | 1.0.0, regex 숫자 list 비교 5case. semver 전체는 아님 | SHOULD document |
| GitHub release lookup | P | latest API, 5초 timeout, 첫 소문자 .exe suffix 선택, 실패는 False | SHOULD document |
| Download | P | 동기 stream GET, 30초 timeout, 8192byte chunk, content-length 있을 때 progress | SHOULD document |
| Replacement/restart | K2 | TEMP EXE Popen 후 main return. 원본 EXE 교체·rollback·서명/hash 검증 없음 | SKIP legacy repair |
| PyInstaller | P | 두 spec 모두 src/main.py, onefile 구성, console=False. clean build 미실시 | SHOULD document |
| Asset naming | P, 불일치 확인 | README main.exe / spec main.exe·TimetableWidget.exe / release SchoolTimetableWidget.exe | SHOULD document |
| Version stamping | P, 미확립 | Python 1.0.0 고정, spec에 version resource 없음, tag 연동 없음 | SKIP legacy pipeline |
| Workflow | O, HEAD에 없음 | tag의 v2 workflow는 다른 entry/output, artifact upload만 존재 | .NET에서 구축 |
| Reproducibility | P / UNKNOWN | tracked build/dist/venv는 있지만 clean build 명세·의존 lock·release hash 재현 증거 없음 | M4에서 source 실행 재현성 확보 |
| Exact release DPI implementation | R | symbol evidence 있음, UX는 재구성 완료. 원본 코드 일치는 UNKNOWN | SHOULD document, exact source 추적 SKIP |

## Verified areas

강한 증거는 geometry/persistence에 집중되어 있다. 대표 테스트는 `test_dpi_real_label_design_geometry_scales_and_recovers`, `test_settings_size_commits_real_hfw_actual`, `test_shutdown_save_common_cleanup_before_settle`, `test_failed_atomic_replace_preserves_existing_valid_file`, `test_restore_backup_cannot_be_overwritten_by_an_older_pending_snapshot`이다.

이 테스트들과 Windows 실측이 .NET의 size/position/DPI 비교 기준이다. 95라는 테스트 수만으로 시간표 편집과 notification에도 같은 coverage가 있다고 추론하지 않는다.

## Partially verified areas

시간표 내용·시각 경계, style Preview/Apply/Cancel, 전체 backup, native tray/flags/autostart, fresh startup과 import/share는 P다. 각 부족한 증거는 M1–M4 또는 document-only로 연결했다. 이미 완료된 Windows geometry 검증을 무조건 반복하지 않고 아직 관찰하지 않은 입력과 결과를 기록한다.

## Known broken areas

다음은 소스로 확인한 구조 또는 알려진 release 불일치다. 이번에 실행하지 않은 결과는 **INFERRED**로 표시하며, v1.0.1 EXE도 같은 결함이었다고 단정하지 않는다.

| ID | 근거와 구체적 사례 | 판정 / 처리 |
| --- | --- | --- |
| K1 | running 1.0.0 / release v1.0.1 비교가 True | 인계된 version mismatch, updater B |
| K2 | download 성공 분기가 TEMP Popen이며 원래 path를 교체하지 않음 | VERIFIED source absence, self-update 완료로 부르지 않음 |
| K3 | Widget.update_current_period가 prev_period 변경 시에만 notification check. 기본 시각 09:55는 current_period=None이므로 10:00의 2교시 예고를 평가하지 못함 | INFERRED 실패 경로. M1에서 시각 fixture로 기록 |
| K4 | ThemeSelector.select_theme→change_theme가 style JSON 저장, SettingsDialog.reject는 초기 style의 memory만 복원 | INFERRED: theme 변경→Cancel 후 disk는 원복되지 않아 재시작 시 선택 theme가 남을 수 있음. Apply 후 Cancel도 초기 snapshot 사용. M2에서 관찰 |
| K5 | reset_widget_position은 manager.position=(100,100), Apply는 저장하지만 widget.move를 호출하지 않음 | INFERRED: 위치 reset이 즉시 화면에 반영되지 않음. 재시작·size 변경 동시 적용 결과를 M2에서 기록 |
| K6 | exceptions.handle_exception의 QApplication 없는 경로가 logger.error에 지원하지 않는 file=sys.stderr 인자를 전달하고 except에서도 반복 | INFERRED: 해당 예외 보고 경로가 TypeError로 실패할 수 있음. document-only, 정상 reference 시작을 막을 때만 최소 수리 |

별도 UNKNOWN: timetable editor의 마지막 span 계산은 7교시에서 `span_count+1`을 사용하므로 과대 span 가능성이 있다. merge 저장도 Qt의 covered cell rowSpan 동작에 의존한다. M1에서 JSON과 재표시를 확인하기 전에는 실행 결함으로 확정하지 않는다.

backup restore는 notification JSON을 복사하지만 NotificationManager를 reload하지 않는다. UI가 재시작을 안내하므로 즉시 전체 설정 적용을 원래 계약이라고 가정하지 않는다. M3에서 재시작 후 결과까지 기록한다. 손상된 style JSON은 backup 후 DataError를 발생시키므로, 메시지의 “기본값 복원”만 보고 정상 startup이 계속된다고 판단하지 않는다.

## Release-only / uncertain areas

인계된 EXE의 DPI/minimum/debounce 증거는 reconstruction과 일치한다. `adjust_cell_sizes` 등의 이름 일치나 원본 알고리즘 복원은 요구하지 않는다. 새롭게 확인된 “Release에는 있으나 현재 없는 필수 사용자 기능”은 이번 evidence만으로 확정할 수 없다. always-on-top toggle이나 single-instance를 증거 없이 release 누락 기능으로 만들지 않는다.

## Must recover before .NET

여기서 recover에는 **비교 가능한 behavior specification 회수·검증**이 포함된다. 각 견적은 수리 구현을 제외한 RECOMMENDED 작업 규모이며 확약이 아니다.

| Item | Why required | Evidence needed | Estimated scope |
| --- | --- | --- | --- |
| M1 Core content / clock | 편집·표시·현재 교시는 핵심 기능. 내용 손실과 시각 경계의 모호함을 이식하지 않음 | 5×7 공백/한국어/여러 줄/연속 과목/마지막 7교시 fixture. merge/split→저장→재open→main 표시. 시작 직전/시작/종료/종료 직후/쉬는 시간/중복/역전/주말·날짜 변경. 예고 누락과 의도 구분 | 0.5–1.5일, 제한된 contract와 Windows 표시 기록 |
| M2 Settings / appearance | Preview/Apply/OK/Cancel의 의미와 실제 모양이 비교 기준 | header/body font, 크기, light/dark/custom, 네 opacity 대표값. Preview→Cancel, Apply→Cancel, restart, 위치 reset의 memory/disk/screenshot 비교. K4/K5의 채택 사양 결정 | 0.5–1일, 조작표와 제한된 contract |
| M3 Data lifecycle | 사용자 데이터의 이식 형식과 restore 결과 필요 | 5 JSON의 비식별 예시, fresh/missing/corrupt 입력, backup→변경→restore→restart, notification/geometry 적용 시점. QR/JSON payload 한 쌍 decode/import 결과 | 0.5–1일, isolated profile 왕복 |
| M4 Windows reference runbook | 다른 PC에서 비교 실행하고 native 동작을 오인하지 않음 | Python/Qt/OS/dependency 버전·source 실행법. fresh/existing profile, flags/겹침/taskbar, lock/drag, tray toggle/show/exit·context exit, autostart on/off/재로그인, notification 표시, 두 번째 실행, 사라진 monitor에서 startup. 기존 DPI 결과 재사용 | 0.5–1일 및 재로그인, native smoke/runbook |

M1–M4는 미지의 동작을 전부 승인하지 않기 위한 gate다. 이미 알려진 버그는 재현 예시와 이식 시 채택/수정 방침을 기록하면 닫을 수 있다. 정상 참조 실행이나 데이터 비교를 막는 것만 별도 최소 수리한다. Python updater나 notification을 전면 재작성할 필요는 없다.

## Document only

**SHOULD document, no need to repair**:

- inclusive 시각 경계, 중복 시 첫 일치, 고정 5요일×7교시, main의 독립 셀 표시.
- K3–K6의 관찰 또는 정적 분석 결과와 .NET에서 의도하는 동작. 버그를 필수 호환성으로 간주하지 않음.
- style/time/timetable/notification 직접 write, 입력 검증 부족, 비transaction backup, restore 재시작 요건.
- QR Base64 UTF-8 JSON 및 선택 덮어쓰기, optional dependency, camera/decoder 미보장 범위.
- Startup shortcut 방식, single-instance 없음, 정상 종료와 강제 종료의 차이.
- updater 비교/lookup/download/temp 실행, asset/version 불일치, Git tag와 EXE lineage 차이.
- source-DPI metadata 없음, 고정 px QSS, native warning 범위.

## Skip legacy repair

**SKIP legacy repair**:

- Windows self-replacement updater, 서명·rollback·배포 기반, tag 연동 version stamping.
- single-instance 신설, aggressive process killer 개선/이식, Python/Qt 대규모 refactor, v2 merge.
- 모든 JSON transaction, 새 schema/source-DPI metadata, 모든 QSS scaling, native warning 전면 제거.
- camera/QR decoder의 환경별 수리와 notification backend 교체. payload 및 관찰 결과는 보존.
- 완전한 original source 탐색, 원래 Release hash 재현, legacy 공개 재배포.

## Updater recommendation

**B — 동작을 문서화하고 .NET rewrite에서 새 updater로 대체한다.**

1. utils/version.py의 __version__은 1.0.0, major/minor/patch는 1/0/0이다. Config.APP_VERSION도 1.0.0이다. Git tag를 runtime에 반영하는 과정은 없다.
2. check_for_update는 chuthulhu/school-timetable-widget의 GitHub latest release API에 GET(5초)한다. tag/body를 읽고 첫 `.exe` asset을 채택한다. **SchoolTimetableWidget.exe라는 정확한 이름을 요구하지 않는다.**
3. is_newer_version은 정규표현식 숫자 열의 정수 list 비교다. 통상적인 버전 비교는 테스트되었지만 prerelease 등 semver 전체를 보장하지 않는다.
4. 시작 전에 Yes/No를 묻는다. Yes면 TEMP의 `school_timetable_update_{tag}.exe`에 동기 download한다. 30초 timeout, content-length가 있으면 progress 표시. 취소, hash/서명 검사, partial-file 정리 코드가 없다.
5. 성공하면 `subprocess.Popen([dest])` 후 quit/return한다. 원래 EXE의 종료를 기다리는 교체 helper, install path 교체, shortcut 갱신, rollback이 없다. Windows self-replacement의 성공 증거가 없다. TEMP EXE 실행 지속·반복 prompt는 INFERRED이며 이번에 download하지 않았다.

Reference 사용에서 update 승낙을 검증의 전제로 삼지 않는다. 네트워크가 통제된 환경이나 No 선택을 runbook에 기록한다. A는 reference 목적에 비해 과도하다. C(notification-only)는 다른 이력 5ed5f28에 선례가 있지만 이번 baseline을 바꿀 필요는 없다. 향후 legacy 배포가 요구되면 별도 C 검토가 가능하다.

## Build/release recommendation

**VERIFIED (source/tree):** HEAD에는 tracked .github/workflows, root requirements/lock, release script가 없다. 로컬에만 있는 다른 계통의 디렉터리를 HEAD 기능으로 취급하지 않는다. main.spec은 asset data 미지정, TimetableWidget.spec은 src/assets를 bundle한다. 모두 src/main.py, console=False이며 version resource 지정이 없다.

build/dist와 Linux Python 3.12 계열 .venv가 tracked여도 release EXE의 Python 3.14 환경이나 재현 가능한 의존 정의가 되지는 않는다. README의 install 목록도 소스가 사용하는 requests와 QR 관련 의존성을 모두 명시하지 않는다.

역사적 `v1.0.1:.github/workflows/build.yml`은 workflow_dispatch, Windows, Python 3.10, requirements.txt, `pyinstaller --name TimetableWidgetV2 ... app/main.py`, dist artifact upload를 사용한다. legacy EXE 재현 절차가 아니며 GitHub Release publish 단계도 없다.

| Option | 비용 | 위험 | Reference 가치 | Migration 가치 |
| --- | --- | --- | --- | --- |
| A Legacy reproducible build/release 복구 | 높음: 환경·bundle·version·배포·updater 검증 | 새 배포 책임과 EXE lineage 혼동 | 재배포 시 높지만 source 비교에는 과도함 | .NET pipeline으로 이전할 부분은 제한적 |
| B Local/reference execution, release는 .NET | 낮음~중간: 의존 버전·profile·실행 절차·다른 환경 smoke | frozen 전용 분기는 미검증으로 남음 | 일상적 동작 비교에 충분, runbook 필요 | 주기능 명세 회수에 집중 |
| C 최소 build reproducibility, release/updater 제외 | 중간: clean Windows build, resource/frozen smoke | Qt/PyInstaller 고유 문제로 확대 가능 | Python 없는 PC에 전달할 때 유용 | packaging 지식의 이식 가치는 작음 |

**B 권고.** frozen 전용 CSV copy와 EXE shortcut은 source 실행과 구분하여 UNKNOWN으로 남긴다. “Python 없는 PC에 reference EXE가 필수”라는 요구가 생길 때 C로 변경한다. 이번에 build하지 않았으며 byte-identical 재현과 같은 명세로 다시 build하는 것도 구분한다.

## Exit criteria for legacy recovery

- [x] Baseline hash·lineage·5 recovery commits·기존 95 passed의 출처를 문서에 고정.
- [x] Windows DPI/layout 실측 및 source-DPI/QSS/native warning 한계 기록.
- [ ] M1: content/clock fixture·contract·표시 결과 보존, 마지막 span 및 예고의 미확정점 해소.
- [ ] M2: Preview/Apply/OK/Cancel/restart/reset 조작표와 대표 이미지, K4/K5 처리 방침 결정.
- [ ] M3: 5 JSON·backup/import 왕복과 복원 시점 기록, 이식 입력 명세 확정.
- [ ] M4: native Windows smoke와 다른 환경에서도 쓸 수 있는 source 실행 runbook 기록.
- [ ] 각 미검증 항목을 verified 또는 명시적 document-only/skip으로 옮기고 참조 비교를 막는 결함 해소.
- [ ] 후속 구현 변경이 있으면 대상 contract와 full suite 통과, DPI/layout 변경이면 Windows 결과도 갱신.
- [ ] updater B / build B 범위를 리뷰로 채택하고 Golden Reference 종료 commit 명시.

원래 EXE의 완전 재현, updater 성공, 공개 release, 모든 native warning 제거는 종료 조건이 아니다.

## Recommended next task

**다음 한 작업은 M1 “시간표 내용·교시 경계의 behavior characterization”이다.** isolated fixture로 편집→저장→재open→main 표시와 시각 경계를 contract화한다. 마지막 merge/split과 예고 누락을 재현하고 기존 동작과 .NET 채택 사양을 구분한다. 이번 감사에서는 테스트 추가나 수리를 수행하지 않았다.

## Documentation-only validation

변경은 docs의 세 문서뿐이며 production/test/build/config를 바꾸지 않는다. full pytest는 재실행하지 않는다. 구현이 동일하고 이번 목적은 소스·기존 증거 감사이기 때문이다. 새로운 95 passed를 주장하지 않는다. 제출 시 git diff --check 및 untracked 문서 whitespace check, diff/stat/status/branch를 확인한다. commit/push/PR은 하지 않는다.

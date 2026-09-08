# Recovery Completion Audit

## Executive verdict

**Geometry·DPI·widget persistence, M1 시간표, M2 Settings / appearance, M3 Data lifecycle이 COMPLETE / CHARACTERIZED다. 남은 MUST는 M4 Windows reference runbook 하나다.** 알려진 M3 quirks의 Python 수리를 완료 조건으로 추가한 것은 아니다. 필요한 것은 남은 사용자 동작의 명세와 재현 가능한 증거이며, 참조 사용을 막는 결함만 최소 수정 대상으로 삼는다. 근거 없는 완료 퍼센트는 사용하지 않는다.

초기 문서 감사 기준은 `recovery-v1-release` / `7a27e4192a0b6d13a9d18a193b1770b6abb58c2c`였다. M1 후속 작업은 2026-09-07 `bb30e3c9983c9faf8acf7a76e03dc79662e6818b` 및 clean에서 시작했다. Production은 변경하지 않고 전용 contract와 [M1 명세](TIMETABLE-BEHAVIOR-SPEC.md)를 추가했다. 기존 95 passed의 역사적 기록과 이번 실행 결과는 [상태 문서](LEGACY-RECOVERY-STATUS.md)에서 구분한다.

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
| Timetable rendering | V, M1 범위 | 35셀 내용 왕복·공백·한글·multiline, native 대표 render 기록 | M1 COMPLETE |
| Current-period highlight | V / KNOWN QUIRK | 42개 초 경계 및 +1ms, 순서·주말·빈 셀, stale-date quirk 계약 | M1 COMPLETE, quirk는 REDESIGN |
| Position persistence / clamp | V, 범위 제한 | JSON 왕복, 음수 좌표 clamp, move 직후 cleanup의 기존 Windows 결과 | 유지, 사라진 화면에서 startup은 M4 |
| Resize / minimum / HFW | V | font minimum, actual/preferred, drag settle, Windows 결과 | 유지 |
| DPI / multi-monitor | V, 범위 제한 | 96↔120 DPI Windows 왕복, margin/hint/HFW 복귀. 모든 모니터 구성을 보장하지 않음 | 유지 |
| Hide/show geometry | V | signal 재연결 테스트와 settings size의 Windows hide/show | tray 입력 자체는 M4 |
| Transparency/background | V, M2 범위 | RGBA/QSS 네 opacity 대표값·signal rollback characterization | M2 COMPLETE; 모든 native compositor 조합 보장 아님 |
| Always-on-top / window flags | P | **main widget은 WindowStaysOnBottomHint + Tool + FramelessWindowHint**. always-on-top toggle 없음. 주요 dialog는 top hint | MUST M4에서 실제 겹침 확인 |
| Drag move / resize / lock | P, 저장 부분 V | 오른쪽 아래 20px resize, lock 상태에서도 resize 허용. lock 조작의 전체 Windows 계약 부족 | MUST M4 |

### Settings and data

| Feature | Status | 현재 증거 / 부족한 증거 | .NET 전 처리 |
| --- | --- | --- | --- |
| Font / font size | V, M2 | Preview/Cancel/Apply/restart, clipping native 기록 | M2 COMPLETE / CHARACTERIZED |
| Colors / theme | V / K4 | Preview와 theme whole-style 즉시 저장, Cancel/restart 확인 | M2 COMPLETE; quirk REDESIGN |
| Opacity | V, M2 | 50%→127 및 rollback 재진입 [119,124,124,124] 대표 contract | M2 COMPLETE; REDESIGN |
| Widget size | V | settings→user request→acceptable actual 저장, hide/show, DPI 왕복 | 유지 |
| Timetable content | V / KNOWN QUIRK | Save/Cancel/close·native X·재실행 확인. merge 손실·마지막 span/분할 예외 고정 | M1 COMPLETE |
| Time/period settings | V, M1 범위 | 7교시 HH:mm, Save/Cancel/close·즉시 재계산. native typing 한계는 명세에 기록 | M1 COMPLETE |
| Reset/default | V / K5 | memory target·파일·실제 위치 및 Cancel/Apply 경계 확인; factory reset 없음 | M2 COMPLETE; REDESIGN |
| Backup/restore lifecycle | V, M3 범위 | [명세](DATA-LIFECYCLE-SPEC.md)·전용 contracts: 5파일 왕복, UI refresh/deferred state, partial/failure. native dialog 외관 미검증 | M3 COMPLETE / CHARACTERIZED |
| Widget settings | V | position/size/lock/screen_info/autostart, missing/corrupt JSON, snapshot/flush | 유지 |
| Timetable persistence | V, M1 범위 | 내용 왕복·누락·malformed·wrong-schema 표시 결과 계약 | M1 COMPLETE; backup/import M3 COMPLETE |
| Period/time persistence | V, M1 범위 | 기본값·reload·부분 적용·invalid QTime 계약 | M1 COMPLETE; backup/import M3 COMPLETE |
| Style persistence | V, M2 정상 경로 | Preview/Apply/OK/Cancel/theme/restart 계약 | M2 COMPLETE; backup/malformed lifecycle M3 COMPLETE |
| Notification persistence | V, M3 범위 | 별도 manager 3값, restore 직후 B/restart A; SettingsManager의 동명 초기값과 별개 | M3 COMPLETE; 실제 전달 M4 |
| Debounce / atomic write | V, widget만 | 250ms coalescing, 같은 디렉터리 replace, 실패 시 기존 파일 보존 | 유지 |
| Atomic all-data / transactional backup | O | 나머지 JSON은 직접 write, backup은 개별 copy | SHOULD document, 전체 재설계 SKIP |
| QR/JSON sharing | V payload, image/camera P | production UTF-8/Base64 envelope 왕복, 선택 timetable replace/time merge 및 partial failure. image encoder/decoder는 미검증 | payload M3 COMPLETE; camera/decoder 수리 SKIP |

### Windows integration, update, build

| Feature | Status | 현재 증거 / 부족한 증거 | .NET 전 처리 |
| --- | --- | --- | --- |
| Tray | P | 왼쪽 클릭 hide/show, 표시·version·종료 메뉴, manager에서 action 연결 | MUST M4 |
| Autostart | P | 현재 사용자 Startup의 SchoolTimetableWidget.lnk, WScript.Shell, 시작 시 sync. 테스트는 JSON 옵션만 | MUST M4에서 on/off/재로그인 확인 |
| Single instance | O, 현재 없음 | entry에 mutex/IPC guard 없음. process cleanup은 단일 실행 기능이 아님 | SHOULD document, .NET 새 설계 |
| Process/application manager | P | 자기 child terminate→kill, signal/atexit, 중복 cleanup 방지. 테스트는 process stub | 정상 종료 M4, aggressive killer 이식 SKIP |
| Startup | P | logging/data dir, update check, QApplication, settings/notification/widget/tray, frozen CSV copy | MUST M4, fresh/existing profile |
| Shutdown persistence | V | Widget 확정→manager flush, 15ms 종료·move 직후 기존 Windows 결과 | native tray/context 종료 전체는 M4 |
| Notification | P / K3 | M1에서 예고 callback 누락 확인. native toast/backend 전체는 미검증 | M1 CHARACTERIZED; M4 표시 확인 |
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

초기 증거는 geometry/persistence에 집중되어 있었고, M1은 전용 95개 계약(강조/HFW interaction 포함)과 native 기록으로 확장했다. 대표 테스트는 `test_dpi_real_label_design_geometry_scales_and_recovers`, `test_settings_size_commits_real_hfw_actual`, `test_shutdown_save_common_cleanup_before_settle`, `test_failed_atomic_replace_preserves_existing_valid_file`, `test_restore_backup_cannot_be_overwritten_by_an_older_pending_snapshot`이다.

기존 테스트들과 Windows 실측이 .NET의 size/position/DPI 비교 기준이다. M1의 추가 근거는 시간표 명세를 따른다. 전체 pytest 통과를 전체 notification/native Windows coverage로 일반화하지 않는다.

## Partially verified areas

M1/M2는 전용 계약·명세·native 기록, M3는 source/TEMP Qt/subprocess 계약과 명세로 완료했다. native tray/flags/autostart, 전체 main startup은 M4다. 실제 QR image/camera decode 및 file picker/confirmation 외관은 M3 VERIFIED에 포함하지 않으며 document-only/skip 경계를 유지한다. 이미 완료된 Windows geometry 검증을 무조건 반복하지 않고 아직 관찰하지 않은 입력과 결과를 기록한다.

## Known broken areas

다음은 소스로 확인한 구조 또는 알려진 release 불일치다. 이번에 실행하지 않은 결과는 **INFERRED**로 표시하며, v1.0.1 EXE도 같은 결함이었다고 단정하지 않는다.

| ID | 근거와 구체적 사례 | 판정 / 처리 |
| --- | --- | --- |
| K1 | running 1.0.0 / release v1.0.1 비교가 True | 인계된 version mismatch, updater B |
| K2 | download 성공 분기가 TEMP Popen이며 원래 path를 교체하지 않음 | VERIFIED source absence, self-update 완료로 부르지 않음 |
| K3 | Widget.update_current_period가 prev_period 변경 시에만 notification check. 기본 시각 09:55는 current_period=None이므로 10:00의 2교시 예고를 평가하지 못함 | VERIFIED M1 callback fixture: 09:55 호출 없음. 실제 toast는 M4, .NET REDESIGN |
| K4 | ThemeSelector.select_theme→change_theme가 style JSON 저장, SettingsDialog.reject는 초기 style의 memory만 복원 | VERIFIED M2: theme→Cancel→restart에서 저장 theme 복원; Apply18→Preview24→Cancel visual10/file18. [설정 명세](SETTINGS-BEHAVIOR-SPEC.md), REDESIGN |
| K5 | reset_widget_position은 manager.position=(100,100), Apply는 저장하지만 widget.move를 호출하지 않음 | VERIFIED M2: target100,100, 즉시 move 없음, Cancel target 유지, 같은 크기 Apply persistence. 다중 모니터 M4; REDESIGN |
| K6 | exceptions.handle_exception의 QApplication 없는 경로가 logger.error에 지원하지 않는 file=sys.stderr 인자를 전달하고 except에서도 반복 | INFERRED: 해당 예외 보고 경로가 TypeError로 실패할 수 있음. document-only, 정상 reference 시작을 막을 때만 최소 수리 |

M1에서 확인한 KNOWN QUIRKS: `A,A,B` open/save→`A,A,A`, 수동 merge의 다음 셀 overwrite, 6~7 동일 span=3/1~7 동일 span=8 및 split AttributeError, 빈 셀 뒤 병합 누락. 전용 legacy tests와 명세 L1–L5에 고정했다. stale-date 강조, invalid time matching, QLabel AutoText도 명세에 기록하며 .NET 필수 재현 대상이 아니다.

M3는 [명세](DATA-LIFECYCLE-SPEC.md)와 [전용 contracts](../src/utils/test_data_lifecycle_contracts.py)로 disk replace/runtime merge, geometry·notification의 restart 적용, 부분 copy 실패와 rollback 부재를 고정했다. manager 250ms pending은 보호되지만 Widget 40ms pending은 restore 뒤 새로운 save로 geometry를 덮어쓸 수 있다. malformed style은 copy 이후 reload 또는 초기 manager 생성을 중단할 수 있다. 모두 LEGACY QUIRK / .NET REDESIGN이며 production은 수정하지 않았다.

## Release-only / uncertain areas

인계된 EXE의 DPI/minimum/debounce 증거는 reconstruction과 일치한다. `adjust_cell_sizes` 등의 이름 일치나 원본 알고리즘 복원은 요구하지 않는다. 새롭게 확인된 “Release에는 있으나 현재 없는 필수 사용자 기능”은 이번 evidence만으로 확정할 수 없다. always-on-top toggle이나 single-instance를 증거 없이 release 누락 기능으로 만들지 않는다.

## Must recover before .NET

여기서 recover에는 **비교 가능한 behavior specification 회수·검증**이 포함된다. 각 견적은 수리 구현을 제외한 RECOMMENDED 작업 규모이며 확약이 아니다.

| Item | Why required | Evidence needed | Estimated scope |
| --- | --- | --- | --- |
| M1 Core content / clock | COMPLETE / CHARACTERIZED | [명세](TIMETABLE-BEHAVIOR-SPEC.md), 전용 contracts, native IME/X/typing/render 기록 | 완료; legacy quirk는 REDESIGN |
| M2 Settings / appearance | COMPLETE / CHARACTERIZED | [설정 명세](SETTINGS-BEHAVIOR-SPEC.md), [전용 contracts](../src/utils/test_settings_behavior_contracts.py), native X/rollback/restart/render 기록 | 완료; quirks는 REDESIGN |
| M3 Data lifecycle | COMPLETE / CHARACTERIZED | [명세](DATA-LIFECYCLE-SPEC.md), [22 contracts](../src/utils/test_data_lifecycle_contracts.py), source/TEMP Qt 및 restart evidence. full profile·pending·partial/failure·sharing payload | 완료; quirks REDESIGN, native 과장 없음 |
| M4 Windows reference runbook | 다른 PC에서 비교 실행하고 native 동작을 오인하지 않음 | Python/Qt/OS/dependency 버전·source 실행법. fresh/existing profile, flags/겹침/taskbar, lock/drag, tray toggle/show/exit·context exit, autostart on/off/재로그인, notification 표시, 두 번째 실행, 사라진 monitor에서 startup. 기존 DPI 결과 재사용 | 0.5–1일 및 재로그인, native smoke/runbook |

M1/M2/M3는 완료했고 남은 MUST gate는 M4 하나다. 이미 알려진 버그는 재현 예시와 이식 시 채택/수정 방침을 기록하면 닫을 수 있다. 정상 참조 실행이나 데이터 비교를 막는 것만 별도 최소 수리한다. Python updater나 notification을 전면 재작성할 필요는 없다.

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
- [x] M1: content/clock 전용 contract·명세·native 표시 기록 완료. 마지막 span/예고는 quirk로 확정, 비차단 typing unknown 명시.
- [x] M2 COMPLETE / CHARACTERIZED: 5-state 명세·전용 contracts·native 관찰 기록, K4/K5 및 signal/geometry quirks REDESIGN. 원본 이미지는 TEMP 기록으로 한정.
- [x] M3 COMPLETE / CHARACTERIZED: 5 JSON·backup/import·pending·partial/failure·restart를 명세와 22 contracts로 고정. native file picker/QR scan/full main startup은 완료 주장하지 않음.
- [ ] M4: native Windows smoke와 다른 환경에서도 쓸 수 있는 source 실행 runbook 기록.
- [ ] 각 미검증 항목을 verified 또는 명시적 document-only/skip으로 옮기고 참조 비교를 막는 결함 해소.
- [ ] 후속 구현 변경이 있으면 대상 contract와 full suite 통과, DPI/layout 변경이면 Windows 결과도 갱신.
- [ ] updater B / build B 범위를 리뷰로 채택하고 Golden Reference 종료 commit 명시.

원래 EXE의 완전 재현, updater 성공, 공개 release, 모든 native warning 제거는 종료 조건이 아니다.

## Recommended next task

**다음 작업은 M4 Windows reference runbook이다.** source 실행 환경과 격리 profile 절차를 고정하고, 기존 DPI/native evidence를 재사용하며 아직 필요한 Windows smoke 범위만 검증한다.

## M1 documentation and contract validation

변경은 새 M1 명세, 기존 docs 3개, 전용 test module과 기존 DPI test 하나의 clock 고정이다. Production/build/config는 변경하지 않는다. 강조 border의 HFW +2px는 legacy visual/layout interaction이며 .NET REDESIGN이다. 실제 결과는 상태 문서의 M1 validation에 기록한다. commit/push/PR은 하지 않는다.

## M2 documentation and contract validation

기준 HEAD `da21ece624985dfa2b60be9cfc0c2043c440e242`와 clean에서 시작했다. 변경은 설정 명세, 기존 docs 3개, 전용 M2 test module뿐이다. Production 무변경. 실행 결과는 [상태 문서](LEGACY-RECOVERY-STATUS.md)의 M2 기록을 따른다.

## M3 documentation and contract validation

기준 HEAD `b966f464167b6cded02dc88cfb2ae0d878770a4a`와 clean에서 시작했다.
변경은 [새 M3 명세](DATA-LIFECYCLE-SPEC.md), 기존 docs 3개, 전용 22-case module이다.
Production/기존 7 backup contracts는 그대로 유지하며 핵심 profile/UI/failure 관계를 추가했다.
실행 결과와 재현 환경은 [상태 문서](LEGACY-RECOVERY-STATUS.md)의 M3 기록을 따른다.
M3 COMPLETE / CHARACTERIZED, 남은 MUST는 M4 하나다. native file picker/QR scan/full main startup 완료를 뜻하지 않는다.

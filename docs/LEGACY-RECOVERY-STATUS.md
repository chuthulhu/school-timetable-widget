# Legacy Recovery Status

## Purpose

`recovery-v1-release`는 available repository history, release executable evidence,
automated contracts, manual Windows verification을 이용해 deployed legacy behavior의
reliable reference implementation을 재구성하는 브랜치다. 실제 v1.0.1 source를
byte-for-byte 복원한 브랜치가 아니다. .NET 재작성 시 기능·디자인·설정·Windows
동작을 비교하는 Golden Reference가 목적이며, Python 제품의 전면 개선이 목적은 아니다.

현재 M1/M2/M3/M4 **COMPLETE / CHARACTERIZED**, 남은 MUST **0**.
Legacy recovery는 **COMPLETE AS GOLDEN REFERENCE**다.
이는 **reconstructed and characterized Golden Reference**이며 exact deployed v1.0.1 source recovered 선언이 아니다.
[Windows Reference Runbook](WINDOWS-REFERENCE-RUNBOOK.md)과 아래 M4 기록이 최신 종료 판정이다.

이 문서는 검증된 복구 상태를 고정한다. 전체 기능의 잔여 검증과 종료 판정은
[Recovery Completion Audit](RECOVERY-COMPLETION-AUDIT.md), 데이터와 소스의 이식 대응은
[Feature Map](FEATURE-MAP.md)을 참조한다.

## Reference baseline

| 항목 | 기준 |
| --- | --- |
| Repository | `chuthulhu/school-timetable-widget` |
| Branch | `recovery-v1-release` |
| Reference commit | `7a27e4192a0b6d13a9d18a193b1770b6abb58c2c` |
| Safe legacy point | `d9756a692c9330db74bed6e92f8366d424643f05` |
| 자동 테스트 기록 | 기준 커밋에서 full suite **95 passed** |
| 문서 감사 | 2026-09-07, 위 HEAD 및 clean working tree 확인 후 시작 |

95 passed 및 아래 Windows 결과는 작업 인계에서 제공된 기존 검증 결과다.
초기 문서 감사에서는 소스와 테스트만 읽었다. 후속 M1 실행은 아래 별도 기록이며 기존 수치를 소급 변경하지 않는다.
이 숫자는 미래 커밋의 테스트 수나 통과 상태를 보장하지 않는다.

### Evidence vocabulary

- **VERIFIED**: 명시된 범위에 실제 소스·테스트 또는 제공된 수동 검증 근거가 있다.
- **INFERRED**: 소스 흐름에서 도출한 결과이며 이번에 실행 관찰한 결과는 아니다.
- **UNKNOWN**: 원본 구현 일치성 또는 실행 증거가 부족하다.
- **RECOMMENDED**: 향후 작업·설계에 대한 권고다.

전체 기능을 VERIFIED로 분류하려면 소스와 자동 계약이 있어야 하고, 중요한 GUI 동작은
해당 Windows 검증도 있어야 한다. 소스에 존재한다는 사실만으로 기능 전체가 VERIFIED가 되지 않는다.

## Release mismatch background

이 저장소에는 legacy v1/main, refactor, v2 rewrite, Tauri 시도의 서로 다른 계보가 있다.
다음 release 분석 결과는 이미 확인된 인계 사실로 채택한다. 이번 감사에서 executable을
다시 내려받거나 역분석하지 않았으며, 로컬 Git 내용과 모순되는지 확인했다.

| 항목 | 확인된 역사적 release evidence |
| --- | --- |
| Release tag / target commitish | `v1.0.1` / `v2` |
| Asset | `SchoolTimetableWidget.exe` |
| Size | 68,704,039 bytes |
| SHA-256 | `aaec0f666b75501d4bb620fbf9e30e909dc1babe89de7ceaead4a1228d427031` |
| Packaging / runtime | PyInstaller / Python 3.14 계열 |
| Embedded application version | `1.0.0` |
| Internal application modules | legacy v1/refactored Python 구조 |

로컬 `v1.0.1` tag는 `bc100754c3ee2f6749989f3793008927b8276f6b`로 해석되며,
그 tree에는 `app/`, `core/`, `infra/` 구조가 있다. tag의 workflow도 `app/main.py`를 빌드한다.
이는 release target 이름만으로 EXE의 source lineage를 판단할 수 없다는 기존 분석과 일치한다.
exact original source tree는 Git history에 완전히 존재하지 않는다는 인계 결론을 유지한다.

Release EXE에는 runtime DPI handling, debounce, minimum cell sizing과 함께
`dpi_ratio`, `last_screen_dpi`, `adjust_cell_sizes`, `min_cell_height_px`,
`min_cell_width_px`, `_check_and_adjust_for_dpi_change`의 흔적이 있었다.
현재 구현은 이 이름들의 원본 알고리즘을 그대로 복원했다고 주장하지 않는다.

현재 [version.py](../src/utils/version.py)의 `__version__`도 `1.0.0`이다.
[main.py](../src/main.py)의 숫자 배열 비교에서 latest `v1.0.1`은 running `1.0.0`보다 크다.
따라서 같은 release EXE를 다시 받아도 update가 있다고 판단할 수 있다.
updater 및 배포 문제는 geometry recovery의 성공 여부와 별도로 관리한다.

## Recovery history

아래 hash와 제목 및 순서는 실제 `git log`와 대조했다.

| Commit | Subject |
| --- | --- |
| `f4eb094493e2e950d35fca528bbbb6e78e3aa58b` | test: establish v1.0.1 recovery contracts |
| `cf96b2421419057b28fef3f2fd4f1985b42c0557` | fix: restore safe debounced widget settings persistence |
| `54f701265ffd18ea856e5e9664022387e5c788f6` | fix: handle explicit backup names correctly |
| `8b7293c65ddbb93185a6c087044317eae72a0fce` | fix: restore minimum timetable cell sizing |
| `7a27e4192a0b6d13a9d18a193b1770b6abb58c2c` | fix: restore DPI-aware timetable sizing and persistence |

## Recovered behavior

### Settings persistence

[SettingsManager](../src/utils/settings_manager.py)는 widget settings에 한해 250ms debounce와
마지막 snapshot 저장을 제공한다. position, total size, position lock, screen info, autostart
옵션을 함께 보존한다. 같은 디렉터리의 임시 JSON을 완성하고 flush/fsync 후 `os.replace`한다.
교체 실패 시 기존 파일과 pending snapshot을 유지하며 명시적인 flush가 가능하다.

백업 생성·복원은 먼저 SettingsManager에 도달한 pending widget snapshot을 flush한다. flush 실패 시 작업을 중단하여
낡은 snapshot이 복원 데이터를 덮어쓰는 것을 막는다. 명시적 백업 이름과 자동 이름 모두
계약이 있다. **시간표·교시·스타일·알림 파일까지 atomic하다는 뜻은 아니다.** 백업 전체도
여러 파일의 단일 transaction은 아니다. Widget의 40ms 확정 이전 intent는 별도 경계이며,
복원 뒤 새 save를 만들어 geometry를 덮어쓸 수 있다. [M3 pending 계약](DATA-LIFECYCLE-SPEC.md)을 따른다.

### Minimum timetable sizing

[styling.py](../src/utils/styling.py)의 수식은 width = font size × 3.0 × DPI scale,
height = font size × 2.5 × DPI scale이다. [widget.py](../src/gui/widget.py)는 헤더/본문 폰트별
하한을 올림 처리하고 그리드·전체 창 최소치에 반영한다. 작은 저장 크기는 최소치로 보정한다.
실제 root layout의 height-for-width(HFW)를 고려하여 줄바꿈 내용이 요구하는 크기를 수용한다.
수식상의 최소 셀 크기와 실제 렌더링된 행 높이는 동일한 값일 필요가 없다.

### DPI / multi-monitor

**UX goal + release evidence + Windows verification에 기반한 reconstructed behavior**다.
runtime preferred size는 96-DPI design units의 `QSizeF`로 유지한다. 화면의 logical DPI / 96을
사용하며 devicePixelRatio를 다시 곱하지 않는다. 양축을 원래 design preference에서 반올림하므로
왕복 시 actual size를 재차 확대하는 누적 growth를 방지한다.

screen/DPI/layout 이벤트는 40ms owned timer로 모으고, 사용자 drag가 끝나고 스타일이 복원된 후
현재 screen과 실제 layout의 acceptable size를 사용한다. margin/spacing도 design 값에서 계산한다.
시간표의 48개 QLabel hint를 갱신하여 이전 DPI의 minimum hint가 복귀 크기를 오염시키지 않게 한다.
다른 dialog의 QLabel은 이 갱신 대상이 아니다.

runtime 위치는 available geometry에 clamp한다. 음수 좌표 모니터도 테스트한다.
최소 창 크기가 화면보다 큰 경우 최소치를 깨면서 전체 창을 화면 안에 축소한다는 보장은 없다.

### Explicit settings size

[SettingsDialog.apply_settings](../src/gui/dialogs/settings_dialog.py)의 크기 변경은
`Widget.apply_user_requested_size`로 사용자 의도를 전달한다. Qt/HFW가 허용하는 실제 크기를
design preferred 및 legacy persisted size에 반영한다. hide/show와 DPI 왕복 후에도 유지된다.
이 기존 검증과 별도로 아래 M2에서 Preview/Apply/Cancel과 재오픈 control 의미를 characterization했다.

### Shutdown persistence

공통 `ApplicationManager.cleanup_resources`는 pending Widget 사용자 요청을 먼저 확정한 후
`SettingsManager.flush_pending_widget_settings`를 호출하고 타이머·프로세스 정리를 진행한다.
Widget 확정이 실패해도 manager flush는 시도한다. 자동 DPI-only 전환은 사용자 저장으로 취급하지 않는다.
이 계약은 전체 child-process 종료, 모든 tray 입력, OS 강제 종료까지 검증한 것은 아니다.

## Automated verification

At reference commit `7a27e4192a0b6d13a9d18a193b1770b6abb58c2c`, the full suite passed 95 tests
(기존 검증 결과 인계). 영구 테스트 소스:

- [test_v101_recovery_contracts.py](../src/utils/test_v101_recovery_contracts.py): 최소치, logical DPI,
  design geometry, HFW, margins, QLabel hints, screen signal, clamp, drag settle, settings size,
  shutdown flush, widget JSON, atomic 실패, backup 상호작용, 숫자 버전 비교.
- [test_settings_manager.py](../src/utils/test_settings_manager.py): 기본 스타일 색상 저장/로드와
  screen info를 포함한 geometry 저장/로드.

screen stub 및 모의 native transient를 사용하는 테스트와 실제 Qt layout 테스트가 섞여 있다.
updater 테스트는 네트워크를 호출하지 않는다. autostart 테스트는 JSON 옵션만 검사하며
Startup 폴더나 registry를 변경하지 않는다. 기준 HEAD에는 추적된 CI workflow가 없다.

## Manual Windows verification

**Manual Windows verification result**: 인계된 실제 Windows 검증 결과다.
원본 로그·PNG는 로컬 TEMP에 있었으며 Git에 첨부되어 있지 않다. 따라서 아래 수치는 기록된 결과이고
이 저장소만으로 원본 PNG hash를 다시 검산할 수는 없다. TEMP 경로를 영구 링크로 사용하지 않는다.

| 측정 | DISPLAY1 96 DPI / 100% (A) | DISPLAY2 120 DPI / 125% (B) | 100% 복귀 (C) |
| --- | --- | --- | --- |
| Actual | 488×473 | 610×591 | 488×473 |
| Design preferred | 488×473 | 변경 없음 | 488×473 |
| Scaled preferred | 488×473 | 610×591 | 488×473 |
| Margin (L/T/R/B) | 10/10/10/10 | 12/12/13/13 | 10/10/10/10 |
| Spacing (H/V) | 4/4 | 5/5 | 4/4 |
| Header height | 33 | 41 | 33 |
| Body rows | 56×7 | 70×7 | 56×7 |

Snapshot A와 C의 PNG SHA-256은 동일했다. 양축 scaling, layout parity, stale QLabel hint 복귀,
HFW, margin/spacing, 누적 growth 방지를 확인한 결과다.

| Integration case | 검증 결과 |
| --- | --- |
| Settings dialog 550×520 요청 | actual/preferred/persisted 550×520, hide/show 유지, 125% 688×650, 100% 550×520 복귀 |
| HFW constrained 550×350 요청 | Qt acceptable 및 actual/design preferred/persisted 550×473; same-DPI restart도 550×473 |
| Resize release 후 약 15ms 종료 | 마지막 size 복구 |
| Move 직후 tray-style cleanup | 마지막 position/size 복구 |
| Automatic DPI-only transition | user save/preferred 오염 없음 |
| Deferred normalization geometry warning | 0 |

## M1 completion and validation

2026-09-07, production HEAD `bb30e3c9983c9faf8acf7a76e03dc79662e6818b`에서 M1을
**COMPLETE / CHARACTERIZED**로 판정했다. [Timetable Behavior Specification](TIMETABLE-BEHAVIOR-SPEC.md)에
데이터·편집·inclusive 경계·강조·저장·malformed·native-only evidence와 .NET 분류를 고정한다.
새 [전용 contract module](../src/utils/test_timetable_behavior_contracts.py)은 정상 계약과
legacy merge/span·stale-date·invalid time quirks를 분리한다. 후속 시각 의존성 수정은 기존 DPI test 하나의 clock 고정에 한정한다.

Native Windows 한글/IME·multiline·Save/Cancel/X·새 프로세스 복원, 650×540 대표 render,
빈 셀·주말 강조를 사용자 조작과 TEMP 로그/캡처로 확인했다. 원본 설정 hash/mtime 불변 및
진단 프로세스 종료 확인을 인계했다. 이번 문서화에서 native 검증을 반복하지 않았다.
QTimeEdit `9:00` 보정/유지 구분, `24:00`·`09:00:00` native typing은 비차단 UNKNOWN이다.

실행 환경: Windows / Python 3.12.14 / PyQt5 5.15.11 / Qt 5.15.2, offscreen 및 TEMP 격리.
아래는 이 HEAD 위의 미커밋 docs/tests 변경을 포함한 실제 실행 결과다. 원래 HEAD 자체가 189개 테스트를 포함한다는 뜻은 아니다.

| 실행 | 결과 |
| --- | --- |
| 새 M1 전용 module | **94 passed**, 0.84s |
| 기존 두 test modules | **95 passed**, 31.84s |
| Root 전체 pytest | **189 passed**, 32.45s (기존 95 + 신규 94) |

세 실행 모두 최종 결과에 warning/failure 없음. `git diff --check`와 새 파일 공백 검사 통과.

후속 최종 검증에서 기존 DPI test의 실제 시각 의존성(188 passed / 1 failed)을 확인했다.
M1 pollution이 아니라 강조 border 1→2px에 따른 HFW +2px였다. 해당 DPI test만 월요일
08:10으로 고정하고 기존 geometry 기대값을 유지했다. 전용 M1에 강조/HFW 왕복 contract를
1개 추가했다(.NET REDESIGN). 후속 검증: DPI 단독 1 passed, 새 contract 1 passed,
기존 95 passed (32.06s), M1 95 passed (1.00s), 전체 **190 passed** 두 번 (32.45s / 33.12s).
모두 warning/failure 없음. Production 무변경, system clock 변경 없이 offscreen/TEMP로 실행했다.

M1 완료는 알려진 결함을 수리했다는 뜻이 아니다. .NET의 destructive merge, validation,
scheduler, AutoText, 저장 실패 UX는 REDESIGN 대상이다. M1 당시 남은 MUST 묶음은 M2 Settings,
M3 Data lifecycle, M4 Windows reference runbook이었다. 당시 결과이며 현재 종료 판정은 아래 M4 기록을 따른다.

## Known limitations

- **Persisted geometry source-DPI metadata 없음.** 저장 size는 현재 화면의 Qt geometry이고
  runtime design preferred와 다르다. 다른 DPI에서 저장한 legacy JSON을 새 프로세스가 최초 실행 시
  완벽한 96-DPI design geometry로 역복원하는 것은 보장하지 않는다. 현재 복구 커밋의 blocker가 아니며,
  legacy 호환 개선 또는 .NET 새 schema 중 별도 결정할 사안이다.
- **QSS pixel scaling.** padding/border/border-radius 일부는 px 그대로다. 현재 Windows UX가 통과했으므로
  legacy에서 일괄 scaling을 추가할 근거가 없다.
- **Native geometry warnings.** 사용자 drag/native monitor transition 중 일부
  `QWindowsWindow::setGeometry` warning은 있을 수 있다. 검증된 deferred correction loop는 없고,
  deferred normalization warning 0과 전체 native warning 0을 혼동하지 않는다.
- **범위 한계.** M1 시간 계산/내용 편집, M2 appearance, M3 backup/import, M4 isolated main/tray/정상 종료를 명시 범위에서 완료했다. 실제 autostart/알림 전달, update/build 등은 runbook과 감사 문서의 document-only/skip 판정을 따른다.

## Golden Reference rules

1. 사용자에게 보이는 legacy 동작 변경에는 contract test가 필요하다.
2. DPI/layout 변경에는 실제 Windows validation이 필요하다. offscreen 통과만으로 대체하지 않는다.
3. Release executable과 일치한다는 증거가 없는 기능을 original exact behavior라고 주장하지 않는다.
4. .NET 재작성은 이 브랜치를 behavior reference로 사용하며, 알려진 버그를 자동으로 새 앱의 요구사항으로 승격하지 않는다.
5. 새 검증은 commit·환경·입력·기대/관찰 결과를 함께 남긴다. 중요한 신규 fixture와 결과는 Git에서 찾을 수 있게 한다.
6. v2/Tauri 구조를 병합하거나 Python 아키텍처를 대규모 정리하는 작업은 이 복구의 종료 조건이 아니다.

## M2 completion and validation

2026-09-07, `recovery-v1-release` / `da21ece624985dfa2b60be9cfc0c2043c440e242`와
clean working tree에서 시작했다. M2 **COMPLETE / CHARACTERIZED**.
[Settings Behavior Specification](SETTINGS-BEHAVIOR-SPEC.md)과
[전용 M2 module](../src/utils/test_settings_behavior_contracts.py)에 다섯 상태
(control / memory / visual / persisted / dialog-open rollback baseline)를 고정했다.

일반 Preview는 저장하지 않지만 theme는 현재 style 전체를 즉시 저장한다.
Apply 후 rollback baseline이 유지되어 Cancel/X가 visual10/file18을 만들 수 있다.
signal 재진입·opacity/alpha 손실·preview clipping·size control 불일치·position reset은
LEGACY QUIRK / .NET REDESIGN이다. 정상 preview/Apply/restart UX는 MATCH,
legacy JSON/size intent/content minimum 개념은 COMPATIBLE이다.

Native Windows 사용자 조작과 TEMP observer로 font Preview→Cancel/X,
Apply18→Preview24→Cancel10/file18, theme→Cancel→새 process dark 복원,
Apply18→X10→새 process18을 확인했다. 최종 native actual550×792/control550×520,
24pt preview required 약1065/actual520은 환경 의존 기록이며 자동 절대 수치가 아니다.
원본 profile 5개 SHA256/mtime와 repository source/docs 33개 hash 불변 및 진단 앱 정상 종료 확인.
원본 이미지/로그는 TEMP에만 있으며 명세는 절차와 관찰의 영구 기록이다.

자동 검증은 offscreen/TEMP, 실제 사용 가능한 font family, 월요일08:10 process clock,
OS autostart/notification stub을 사용한다. QApplication font/style은 변경하지 않고
singleton/environment monkeypatch와 dialog/widget/timer cleanup으로 격리한다.
subprocess는 SettingsManager reload만 검사하며 full main/native startup 증거와 구분한다.

M2 최초 작성 중 layout 미실현/지연 확정 전 조회로 실패한 fixture를 offscreen show 및
owned timer settle로 정정했다. Production 수정이나 host clock 변경은 없다.
최종 실행 결과는 아래 표에 기록한다.

| Run | Result |
| --- | --- |
| M2 focused | 14 passed (7.58s) |
| Existing recovery modules | 95 passed (31.89s) |
| M1 focused | 95 passed (0.94s) |
| Full pytest 1 | 204 passed (40.14s) |
| Full pytest 2 | 204 passed (40.09s) |

최종 다섯 실행은 pytest warning/failure 없이 통과했다. 최종 count는 기존190 + M2 14 = 204.
문서 상대 링크 80개와 git diff --check 통과. 테스트는 semantic JSON/실제 controls/QSS/geometry를
검사하며 native X와 platform pixel 수치를 자동화했다고 주장하지 않는다. M2 commit-ready다.

M2 완료 당시 남은 MUST는 M3/M4 두 묶음이었다. 현재 상태는 아래 M3 완료 기록을 따른다.
실제 autostart/notification delivery·backup/import가 M2와 함께 완료됐다는 뜻은 아니다.
이번 변경은 docs 4개와 신규 test module 하나이며 production 무변경, commit/push/PR 미실행.

## M3 completion and validation

2026-09-08, `recovery-v1-release` / `b966f464167b6cded02dc88cfb2ae0d878770a4a` 및
clean working tree에서 시작했다. M3 **COMPLETE / CHARACTERIZED**.
[Data Lifecycle Specification](DATA-LIFECYCLE-SPEC.md)과
[전용 M3 module](../src/utils/test_data_lifecycle_contracts.py)에 5 JSON, save strategy,
backup snapshot, disk replace/runtime merge, UI refresh/restart, pending, partial/failure,
JSON/QR sharing payload를 고정했다. 현재 남은 MUST는 **M4 Windows reference runbook** 하나다.

manager 250ms pending은 flush로 보호되지만 Widget 40ms 확정 이전 intent는 restore 뒤 새 저장으로
geometry를 덮어쓸 수 있다. 복원 UI는 timetable/time/style을 갱신하지만 geometry actual/preferred와
NotificationManager는 이전 값이 남는다. 정상 full restore 후 별도 process는 persisted A를 load한다.
partial JSON은 기존 memory/defaults와 섞이고 copy failure는 rollback하지 않는다.
이들은 LEGACY QUIRK / .NET REDESIGN이며 production을 수정하지 않았다.

Evidence는 source, 선행 TEMP Qt characterization/정상 종료 후 새 Widget process와 이번 automated contracts다.
새 tests의 subprocess는 manager 5 data classes reload이며 full main/tray/native Widget startup은 아니다.
Widget pending test는 실제 Qt event handlers와 owned timer callback을 순서대로 실행하여 causal relation을
검사한다. exact 40ms latency나 OS 마우스 입력을 검사하지 않는다. 절대 pixel 기대값 대신 A/B geometry 관계를 사용한다.

QR encoder 입구의 production payload를 캡처하고 실제 Base64 decode/import한다. optional image dependency만
test-local stub하여 원래 serializer/import를 실행하며, QR image encoding/scan은 검증하지 않는다.
실제 file picker/confirmation appearance, camera/image decoder, OS autostart/notification delivery는 미검증으로 유지한다.
기존 M1/M2 명세의 잔여 milestone 표현은 당시 기록이며 현재 gate는 이 절과 최신 감사 문서를 따른다.

실행 interpreter: `C:\CodexVenvs\school-timetable-widget-py312\Scripts\python.exe`.
Python 3.12.14 / PyQt 5.15.11 / Qt 5.15.2, `QT_QPA_PLATFORM=offscreen`, `PYTHONDONTWRITEBYTECODE=1`,
`PYTHONPATH=<repository>/src`, `-B -m pytest ... -q -p no:cacheprovider --basetemp <unique TEMP>`.
새 module은 test별 TEMP, singleton/environment monkeypatch, QApplication font/style 보존,
Widget/dialog/timer cleanup과 bounded subprocess를 사용한다. 기존 7 backup tests는 수정·복제하지 않았다.

| Run | Result |
| --- | --- |
| M3 focused | **22 passed**, 2.12s |
| Existing backup/recovery modules | **95 passed**, 32.16s (기존 backup 7개 포함) |
| M1 focused | **95 passed**, 1.31s |
| M2 focused | **14 passed**, 8.09s |
| Full pytest 1 | **226 passed**, 41.44s |
| Full pytest 2 | **226 passed**, 41.21s |

여섯 실행 모두 pytest warning/failure 없이 통과했다. 최종 count는 기존204 + M3 22 = **226**.
두 full run은 같은 count이며 skip도 없다. 초기 focused 성공 후 subprocess의 style file read를
context manager로 정리했고 최종 두 full run이 이를 포함한다. behavior/기대값 변경은 없었다.
문서 상대 링크 97개, 신규 파일 포함 공백 검사 및 `git diff --check` 통과.
Production Python 26개 SHA-256과 기존 tests 무변경, 원본 profile 5개 SHA-256/mtime는 선행
characterization 기준과 동일함을 확인했다. M3 **commit-ready**이며 남은 MUST는 M4 하나다.

이번 변경은 docs 4개와 신규 M3 test module 하나다. Production 및 기존 tests는 무변경이며
commit/push/PR은 실행하지 않았다. M3 완료는 전체 Golden Reference 종료나 legacy bug 수리를 의미하지 않는다.

## M4 completion and final recovery verdict

2026-09-08, `recovery-v1-release` / `07eaa43de6f55a0d4ba21fb74482dbf539b3636d`,
clean tree에서 시작했다. [Windows Reference Runbook](WINDOWS-REFERENCE-RUNBOOK.md)에
source 실행 환경·dependency 선언의 불완전성·fresh/copied TEMP 절차·safe launcher·10분 smoke를 고정했다.
**M4 COMPLETE / CHARACTERIZED; remaining MUST 0; COMPLETE AS GOLDEN REFERENCE.**

현재 source baseline은 위 HEAD이고, M4는 그 위의 미커밋 docs-only 변경이다. 종료 문서 commit hash는 아직 없다.
기존 reference baseline 표 및 M1/M2/M3 수치는 각 당시 기록이다. M1/M2/M3 명세의 남은 milestone 표현도
당시 범위 기록으로 보존하며 최신 종료 판정은 이 절과 감사 문서를 따른다.

환경 재확인: Windows 11 build26100 AMD64 / Python3.12.14 / PyQt5 5.15.11 / Qt5.15.2,
ASCII venv `C:\CodexVenvs\school-timetable-widget-py312`. PyQt5-sip12.19.0,
pytest9.1.1, psutil7.2.2, appdirs1.4.4, requests2.34.2. Qt plugin override 없이 startup 성공.
README는 unpinned이며 requests/QR dependencies가 빠져 있다. root dependency lock/workflow 없음.
다른 물리 PC의 fresh install을 수행한 것은 아니며 재현 명령과 현 환경의 실행 증거를 제공한다.

| M4 verification | Result / boundary |
| --- | --- |
| Offscreen isolated main, fresh TEMP | tray QAction 종료와 Widget.close 별도 프로세스; Widget 지연 size630×580 → 최종 JSON630×580, cleanup true, exit0 |
| 초기 native 시도 | sandbox 별도 desktop에서 Qt visible=true지만 사용자에게 안 보임. 사용자 visible 증거에서 제외, 정상 종료0 |
| Default desktop native main | 원래 Tool/Frameless/Bottom flags 유지, updater/autostart/notification delivery만 process-local 차단 |
| 사용자 tray 입력 | 우클릭 menu, 왼쪽 숨김, 보기 action 복귀, 종료로 widget/icon 소실; observer event와 일치 |
| 설정 / geometry | Widget 메뉴 설정 열기→취소, resize 사용자 확인, move/resize 최종 geometry 계측 |
| 종료 / 재실행 | tray exit0·cleanup true·PID 종료, JSON (861,220,440,375), 새 main의 같은 geometry. 위치 사용자 확인; 크기 육안은 불확실, Qt/JSON 계측으로만 확인 |
| DPI | 이번 Default run96 DPI; 새100↔125 왕복 미실행, 기존 Windows 왕복 증거 재사용 |
| 보호 확인 | 원본5 JSON SHA-256/mtime 전후 동일, Startup .lnk 전후 없음, 소유 native 진단3 process 모두 exit0 |

Native 원본 로그/observer/JSON은 TEMP 자료다. runbook의 절차·관찰 표가 영구 기록이며 원본 capture 보관을 주장하지 않는다.
computer-use는 Default desktop의 Tool 창도 반환하지 않았다. 이는 discovery 한계이며 capture/input 실패를 직접 입증하지 않는다.
사용자 직접 입력을 자동 OS 입력 검사로 부르지 않는다. 별도 desktop 문제를 Qt.Tool discovery 문제와 구분했다.

Autostart는 Startup shortcut 존재 detection/생성/삭제·Python/frozen target·실패 의미를 source-confirmed로 고정했다.
기존 shortcut을 바꾸거나 재로그인하지 않았다. Notification은 manager/load/toggle/backend 경계만 기록, 실제 toast 미실행.
single-instance guard 없음은 source-confirmed이며 native A/B 동시 실행은 생략했다. Lock/overlap/taskbar 전체,
monitor 제거 startup 등도 document-only; 알려진 동작은 .NET MATCH/COMPATIBLE/REDESIGN에 따라 사용한다.
이 disposition은 이번 M4의 명시적 범위를 따르며 미실행 기능을 VERIFIED로 승격하지 않는다.

Updater B / build B 채택: reference에서 updater 실행 금지, legacy release pipeline 수리·재배포는 gate 밖,
.NET에서 새로 구축한다. Golden Reference는 behavior reference이며 implementation template이나 public release candidate가 아니다.

Production/tests/dependency/build 변경 없음. test/helper 파일도 추가하지 않았다. TEMP inline characterization만 수행했다.
전체 pytest는 docs-only라 재실행하지 않았으며 **226 passed × 2는 M3의 기존 baseline**으로 기록한다.
허용된 문서4개만 변경, commit/push/PR은 실행하지 않는다. 최종 diff 검토 후 문서 commit은 별도 후속 단계다.

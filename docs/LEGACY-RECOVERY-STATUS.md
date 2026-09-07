# Legacy Recovery Status

## Purpose

`recovery-v1-release`는 available repository history, release executable evidence,
automated contracts, manual Windows verification을 이용해 deployed legacy behavior의
reliable reference implementation을 재구성하는 브랜치다. 실제 v1.0.1 source를
byte-for-byte 복원한 브랜치가 아니다. .NET 재작성 시 기능·디자인·설정·Windows
동작을 비교하는 Golden Reference가 목적이며, Python 제품의 전면 개선이 목적은 아니다.

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

백업 생성·복원은 먼저 pending widget settings를 flush한다. flush 실패 시 작업을 중단하여
낡은 snapshot이 복원 데이터를 덮어쓰는 것을 막는다. 명시적 백업 이름과 자동 이름 모두
계약이 있다. **시간표·교시·스타일·알림 파일까지 atomic하다는 뜻은 아니다.** 백업 전체도
여러 파일의 단일 transaction은 아니다.

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
이는 설정 대화상자의 모든 Preview/Apply/Cancel 의미를 검증했다는 뜻은 아니다.

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
scheduler, AutoText, 저장 실패 UX는 REDESIGN 대상이다. 남은 MUST 묶음은 M2 Settings,
M3 Data lifecycle, M4 Windows reference runbook이다. 전체 recovery 종료와 구분한다.

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
- **범위 한계.** M1 시간 계산/내용 편집은 위 범위에서 완료했다. 전체 설정 appearance, backup/import, tray/autostart/알림, update/build는 감사 문서에서 별도로 판정한다.

## Golden Reference rules

1. 사용자에게 보이는 legacy 동작 변경에는 contract test가 필요하다.
2. DPI/layout 변경에는 실제 Windows validation이 필요하다. offscreen 통과만으로 대체하지 않는다.
3. Release executable과 일치한다는 증거가 없는 기능을 original exact behavior라고 주장하지 않는다.
4. .NET 재작성은 이 브랜치를 behavior reference로 사용하며, 알려진 버그를 자동으로 새 앱의 요구사항으로 승격하지 않는다.
5. 새 검증은 commit·환경·입력·기대/관찰 결과를 함께 남긴다. 중요한 신규 fixture와 결과는 Git에서 찾을 수 있게 한다.
6. v2/Tauri 구조를 병합하거나 Python 아키텍처를 대규모 정리하는 작업은 이 복구의 종료 조건이 아니다.

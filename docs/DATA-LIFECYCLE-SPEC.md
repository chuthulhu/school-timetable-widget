# Data Lifecycle Specification

## Scope and Evidence

M3 **COMPLETE / CHARACTERIZED**: 데이터 생성·저장·backup/restore·sharing import·restart의
Golden Reference. Production behavior 개선이나 deployed v1.0.1 exact source 복원 선언이 아니다.
남은 MUST는 [M4 Windows reference runbook](RECOVERY-COMPLETION-AUDIT.md) 하나다.

기준: `chuthulhu/school-timetable-widget`, `recovery-v1-release`,
`b966f464167b6cded02dc88cfb2ae0d878770a4a`, 2026-09-08 clean tree에서 시작.
이 HEAD에 문서와 test-only 변경을 더한 결과이며, 기준 HEAD 자체에 M3 tests가 있었다는 뜻은 아니다.

| Evidence | 의미 |
| --- | --- |
| S | 현재 production source 확인 |
| T | 선행 characterization의 고유 TEMP profile, 실제 offscreen Qt 객체·event·QSS·파일 관찰 |
| P | 선행 TEMP launcher 정상 종료 후 별도 Widget process 재실행 |
| A | [전용 M3 contracts](../src/utils/test_data_lifecycle_contracts.py), TEMP JSON/Qt 및 별도 manager subprocess |

원본 TEMP logs/이미지는 영구 의존 링크로 사용하지 않는다. 아래 절차·관찰과 checked-in fixtures/tests가
재현 근거다. 실행 결과와 runtime 버전은 [검증 기록](LEGACY-RECOVERY-STATUS.md)의 M3 절을 따른다.
기존 [M1](TIMETABLE-BEHAVIOR-SPEC.md)/[M2](SETTINGS-BEHAVIOR-SPEC.md)의 세부 편집·appearance 계약은 재정의하지 않는다.

## Profile Files

`P`는 [paths.py](../src/utils/paths.py)의 data directory다. 이미 존재하는
`SCHOOL_TIMETABLE_DATA_DIR`를 우선하며, 아니면 appdirs의 `SchoolTimetableWidget` / `TimeTableDev`
사용자 data directory를 사용한다. 생성 실패 시 TEMP fallback이 있다. 존재하지 않는 환경변수 경로를
지정하면 그 경로가 자동 선택된다고 가정하지 않는다. 테스트는 먼저 TEMP directory를 만든다. (S)

| File | Purpose | Owner / loader | Save trigger / strategy | Backup | Restart authority |
| --- | --- | --- | --- | --- | --- |
| widget_settings.json | position, size, lock, screen_info, auto_start_enabled | SettingsManager.load_widget_settings | Widget/Settings 옵션 → 250ms snapshot debounce, temp/fsync/replace | 존재하면 copy | JSON에서 manager load, Widget startup에서 admissible geometry 적용 |
| style_settings.json | theme, 색상, opacity, legacy/header/cell font | SettingsManager.load_style_settings | Apply/OK, light/dark theme → 직접 write | 존재하면 copy | 기본 스타일 위에 JSON 적용 |
| timetable_data.json | 요일 → 문자열 교시 → 문자열 내용 | SettingsManager.load_timetable_data | editor Save/import → 직접 write | 존재하면 copy | JSON 전체 load, 없는 셀은 빈 표시 |
| time_settings.json | 문자열 교시 → start/end HH:mm | SettingsManager.load_time_settings | time editor Save/import → 직접 write | 존재하면 copy | 기본 7교시에 파일의 교시 overlay |
| notification_settings.json | notification_enabled, next_period_warning, warning_minutes | NotificationManager.load_notification_settings | setters, Settings Apply → 직접 write | 존재하면 copy | 별도 manager가 기본 true/true/5 위에 load |

이 5개가 이전 검증의 **원본 profile 5파일**이다. 별도 style 파일명은 없다.
save path는 모두 `P/<위 파일명>`이다. `src/settings`의 예시는 자동 runtime seed가 아니다.
`logs/`, 기존 `backups/`, frozen startup의 `default_timetable.csv`, OS Startup 바로가기는
5파일 snapshot에 포함되지 않는다. CSV는 현재 시간표 loader의 입력이 아니다. (S)

최초 5파일이 없으면 manager 초기화는 memory defaults만 구성하며 JSON 5개를 일괄 생성하지 않는다.
첫 write는 해당 save trigger에 달려 있다. main의 logging/resource side effect와 구분한다. (T/S)

## Data Ownership

| Caller | Persistence / runtime responsibility |
| --- | --- |
| Widget | SettingsManager widget save 요청; geometry intent 확정 |
| SettingsDialog | SettingsManager style/widget + NotificationManager 저장 |
| Timetable editor | SettingsManager.update_timetable_data; 표시 갱신 |
| Time editor | manager time_ranges 변경 + save_time_settings; 호출 Widget이 Accepted 후 재계산 |
| ImportDialog | manager memory 변경 + save; 성공 경로의 Widget refresh |
| SettingsManager backup | 직접 파일 copy + load_all_settings |
| BackupRestoreDialog | restore 결과 메시지 + Widget refresh orchestration |
| NotificationManager | 자체 JSON read/write, 별도 runtime state |

각 UI가 JSON을 직접 open하는 구조는 아니지만, 저장 경계와 refresh 책임은 UI/manager에 분산된다.
.NET의 `Infrastructure/Persistence` 및 explicit runtime apply coordinator를 고려할 근거이며,
이번 문서가 새 아키텍처를 확정하지는 않는다. (S)

## Save Semantics by File

[SettingsManager](../src/utils/settings_manager.py)는 widget snapshot만 250ms debounce한다.
마지막 요청을 같은 디렉터리 임시 JSON에 쓰고 flush/fsync 후 `os.replace`한다.
실패하면 기존 파일과 pending을 유지하지만 timer는 정지하며 자동 retry를 보장하지 않는다.
ApplicationManager cleanup은 Widget intent 확정 → manager flush 순서다. (S/기존 contracts)

나머지 4파일은 동기 `open(..., 'w')`/JSON write다. atomic multi-file profile은 아니다.
style 실패는 DataError, timetable/time/notification save 실패는 log 후 삼킨다.
UI가 memory를 먼저 바꾼 뒤 save하므로 disk 실패가 memory rollback을 뜻하지 않는다. (S)

일반 style Preview는 memory/QSS만 바꾼다. light/dark theme 변경은 현재 whole-style을 즉시 저장하여
다른 Preview 값도 함께 persist할 수 있다. custom theme 선택과 Cancel quirks는 M2를 따른다.
이 heterogeneous persistence는 **LEGACY CHARACTERISTIC / .NET REDESIGN**이다.

## Backup Format

`P/backups/<name>/` 폴더이며 archive가 아니다. copy 순서는 timetable → time → style → widget → notification.
존재하는 파일만 `shutil.copy2`하고 마지막에 UTF-8 `description.txt`를 쓴다.
없는 파일을 defaults로 채우거나 JSON 내용의 유효성을 검증하지 않는다. (A/T/S)

schema version, manifest, checksum, transactional snapshot marker, retention, scheduled backup은 없다.
손상된 style/widget 파일을 `backups/` 아래 별도 이름으로 **이동**하는 보존 기능은 있지만,
이것은 예약 full-profile backup이 아니다. 전체 snapshot의 원자성·동시 writer 격리는 보장하지 않는다. (S)

## Backup Snapshot Boundary

**Backup flushes SettingsManager pending snapshots, but does not automatically finalize every
Widget-level pending user intent.** 최신 visible Widget 전체를 항상 캡처한다는 계약은 없다.

| Backup 직전 상태 | Captured data | Evidence |
| --- | --- | --- |
| manager 250ms snapshot pending | flush한 최신 snapshot | 기존 7 contracts / T |
| resize release 후 Widget 40ms 확정 pending, manager pending 없음 | 이전 persisted geometry | A/T |
| font Preview: memory18 / file10 | file10 | A/T |
| Preview18 후 light/dark theme immediate save | 새 theme와 current memory font18 | A/T |
| Settings Apply | 저장된 style 포함; geometry는 Widget→manager 경계에 주의 | A/T |
| Timetable editor Save / Time editor Save | 저장된 내용 / 시각 포함 | A/T |

한 profile 안에서 서로 다른 commit 시점의 값이 합쳐질 수 있다. backup은 일반 style Preview를
강제로 Apply하지 않으며 timetable/time memory를 다시 serialize하지도 않는다.

## Backup Naming and Metadata

| Item | Behavior |
| --- | --- |
| create_backup() | `backup_YYYYMMDD_HHMMSS` |
| create_backup("manual-name") | explicit name 사용 |
| UI 초기 이름 | `Timetable_YYYYMMDD` |
| description.txt | `시간표 백업 - YYYY년 MM월 DD일 HH:MM:SS` |
| 사용자 description 입력 | 없음 |
| API sanitization | 없음; 경로 성분을 안전하게 정규화하는 API 계약도 없음 |
| UI sanitization | trim 후 `\ / * ? : " < > \|` → `_`; 완전한 Windows filename validator는 아님 |
| duplicate | 기존 folder 재사용, 같은 파일 overwrite; 누락 source의 이전 backup 파일은 잔존 |

duplicate 폴더는 서로 다른 시점의 파일을 포함할 수 있으며 기본 이름의 초 단위 충돌 방지도 없다. (A/T/S)
explicit name의 `now` UnboundLocalError 수정은 **current recovery corrected behavior**다.
deployed v1.0.1도 반드시 같은 동작이었다고 주장하지 않는다. 날짜/설명은 versioned metadata가 아니다.

## Restore Disk Semantics

**DISK REPLACE != RUNTIME STATE REPLACE.**

- Backup에 있는 expected file은 전체 bytes를 현재 파일에 copy한다. JSON key merge가 아니다.
- Backup에 없는 expected file은 현재 file을 유지한다. 삭제/default/error가 아니다.
- Profile에만 있는 기타 file도 삭제하지 않는다.
- copy 순서는 backup과 같고, 완료 후 `load_all_settings()`를 호출한다. (A/T/S)

## Runtime Reload Semantics

`load_all_settings`: style → time → timetable → widget. NotificationManager reload는 없다.

| Data | Existing manager reload |
| --- | --- |
| timetable | 로드 성공 시 memory 전체 교체 |
| style | 누락 fields는 기존 값; 개별 font는 legacy font fallback과 섞일 수 있음 |
| time | 입력 periods만 overlay. 기존 extra period도 남을 수 있음 |
| widget | 누락 position/size는 기존 값; lock/autostart는 false, screen_info는 null fallback |
| notification | 별도 manager 유지; 명시 load 또는 새 manager 생성까지 기존 값 |

대표 partial style `{ "cell_font_size": 18 }`의 disk는 이 값만 남는다. runtime dark는 남지만
새 manager는 기본 light다. partial time file에 없는 runtime 9교시는 남지만 새 manager에서는 없다.
따라서 부분 profile에서 새 process는 Config defaults + persisted files의 authoritative 결과다. (A/T)

## UI Restore Behavior

[BackupRestoreDialog](../src/gui/dialogs/backup_dialog.py)는 manager 성공 후 재시작을 안내하고,
부모의 update_timetable_display / update_styles / update_current_period를 호출한다.
manager API만 호출하면 이 UI refresh는 없다. (A/T/S)

| 정상 full A backup 복원 | File | Memory | Immediate Widget | Restart |
| --- | --- | --- | --- | --- |
| timetable | A | A | A text | A |
| time | A | A | 현재 period 재계산 | A |
| style | A | A | A QSS | A |
| geometry | A | manager A | actual/preferred는 B 유지 | startup에서 A 의도 적용 |
| notification | A | NotificationManager B | B 옵션 유지 | A |

geometry A 적용은 기존 DPI/minimum/HFW 계약을 따른다. 플랫폼별 exact pixels를 이 절에서 고정하지 않는다.
`restore completed`가 모든 runtime state의 즉시 교체를 뜻하지 않는다. 이후 사용자 저장은 현재
runtime 값을 다시 persist할 수 있으므로 재시작 전 조작에도 주의가 필요하다. (S)

## Pending Save Interaction

**Protected manager pending:** B snapshot → flush B → copy A → pending 없음/timer stop.
선행 TEMP에서 400ms 후에도 A 파일 hash 유지. 기존 테스트는 timeout signal 재발행도 보호한다.

**Unprotected Widget pending / LEGACY QUIRK:** resize release → Widget 40ms intent 대기 → restore A →
Widget intent 확정 → 새 manager snapshot → A geometry 덮어쓰기. 선행 관찰은 A600×550 후690×590이었다.
이 숫자는 플랫폼 요구사항이 아니다. A는 real Qt mouse event handler와 owned timer callback을 순서대로
실행해 pending 관계 및 최종 파일을 검증하며 wall-clock 40ms race나 native 입력을 재현했다고 주장하지 않는다.

이것은 오래된 manager snapshot의 재실행이 아니라 **Widget이 뒤늦게 만드는 새로운 save**다.
기존 manager flush contract를 all pending UI intents protected로 확대하지 않는다. .NET REDESIGN.

## Restart Semantics

T/P 절차: full A backup → B profile/Widget → UI restore A → runtime 혼합 상태 기록 →
Widget.closeEvent / QApplication 정상 종료(exit0) → 별도 Python Widget process.
종료 전 files는 A 유지, 새 process는 style/timetable/time/notification A와 A geometry 의도를 load했다.
이는 TEMP launcher이며 전체 main/tray/updater startup은 아니다.

A의 자동 contract는 동일 full restore 뒤 안전한 persistence cleanup 순서를 실행하고,
별도 QCoreApplication process에서 두 manager의 5 data classes를 검증한다.
subprocess에서는 실제 Widget render/OS geometry 적용을 검사하지 않는다. P의 별도 증거와 구분한다.

## Partial / Missing / Malformed Backup

| Input | Current behavior | Evidence |
| --- | --- | --- |
| 없는 path | False, 찾을 수 없음 | A/T |
| 빈 folder | True, file 유지 후 reload | A/T |
| backup path가 regular file | True, expected children 없으므로 copy 없이 reload | A/T |
| 일부 expected file 없음 | 해당 현재 file 유지 | A/T |
| timetable malformed JSON | True, memory {}, corrupt file 유지 | A/T |
| time malformed JSON | True, 당시 time memory 유지 | T/S; loader는 M1 |
| style malformed JSON | corrupt file 이동, DataError, restore False | A/T |
| widget malformed JSON | corrupt file 이동, 당시 memory 유지, restore True | T/S |
| notification malformed JSON | True, 기존 runtime 유지; 새 NotificationManager는 defaults | T/S |
| description 비 UTF-8 | restore에서는 무시; listing은 전체 [] 반환 | T/S |

style syntax error는 첫 loader에서 전파되어 manager initialization 자체를 중단할 수 있다.
다른 4파일이 정상이어도 모두 계속 load한다는 fault-isolation 계약은 없다. restore에서는 이미 file copy가
끝났어도 첫 reload 실패로 이전 runtime state가 남을 수 있다. (A/T/S)
구문상 유효하지만 wrong-schema인 데이터의 모든 조합은 새로 검사하지 않는다. M1 invalid-data 한계를 따른다.

## Failure Behavior

| Failure | Observable result |
| --- | --- |
| Backup 두 번째 copy 실패 | False, 첫 timetable file만 든 partial folder 잔존; source profile 유지 |
| Restore 두 번째 copy 실패 | False, timetable disk만 A, 나머지 B, reload 전 실패라 memory B |
| manager pending flush 실패 | backup/restore abort, pending 유지, timer stop, automatic retry 보장 없음 |
| Backup target folder 자리에 file | False |

첫 두 경우는 A의 안전한 copy failure injection으로 결과 파일·return value를 확인한다.
단순 call count 검사가 아니다. flush 실패는 기존 7 contracts를 재사용한다.
directory 생성/read/copy/description write 예외는 catch/log 후 False다. 이미 수행한 write를 rollback하거나
partial folder를 제거하지 않는다. UI는 결과에 따라 failure dialog를 호출한다. (A/T/S)

Backup 자체는 JSON serialization을 하지 않는다. JSON serialization 실패는 선행 widget flush에서 발생할 수 있다.
완성된 corrupt JSON도 backup에 복사된다. profile 작업은 **non-transactional multi-file operation**이다.

## Backup UI

목록은 이름/생성일/설명 3열, 단일 행 선택, 첫 행 자동 선택이다. timestamp 기본 이름은 날짜를 parsing해
최신순 정렬하지만 일반 manual name은 created=None으로 생성일 `알 수 없음`; 실제 생성일 순서를 보장하지 않는다.
잘못된 `backup_*` timestamp parsing의 fallback은 폴더 mtime다. 반환 record에는 path가 있으나 목록 열에는 없다.
생성 완료 메시지에 path가 나온다. (T/S)

복원 확인은 Yes/No, **default No**. 성공 메시지는 재시작을 안내한다. “현재 설정과 시간표가 모두 대체”라는
문구는 누락 file 유지·runtime 혼합을 완전히 설명하지 못한다. 삭제는 확인 후 folder 전체 삭제다.
외부 backup folder/file picker, archive import/export UI는 없다. native dialog 외관은 미검증이다.

## JSON / QR Sharing Import

Backup과 별도 workflow이며 [ImportDialog](../src/gui/dialogs/import_dialog.py)와
[QRShareDialog](../src/gui/dialogs/qr_share_dialog.py)가 담당한다. 공유 envelope 예:

```json
{
  "timetable": {"월": {"1": "예시 과목\n예시 교실"}},
  "time_settings": {"1": {"start": "09:00", "end": "09:50"}}
}
```

JSON file은 envelope를 직접 읽는다. QR은 `JSON(ensure_ascii=False) → UTF-8 → Base64 ASCII`다.
raw timetable_data.json은 envelope가 아니다. 공유할 두 category를 선택할 수 있다.
QR image 생성/PNG 저장 기능은 있지만 별도 JSON export UI는 없다. camera/image import 경로도 있다. (S)

| Import selection / failure | Result |
| --- | --- |
| selected timetable | memory/file 전체 교체 |
| selected time | 입력 periods만 기존 time_ranges에 merge, 이후 전체 time save |
| unselected category | file 유지 |
| 정상 적용 | Widget timetable/current period refresh |
| JSON parse failure | 이전 imported_data 및 Apply enabled가 남을 수 있음 |
| timetable commit 후 time conversion failure | timetable만 저장, 예외 전파, 최종 Widget refresh 미실행 가능 |

A는 production serializer에서 QR encoder에 전달하는 payload를 캡처하여 독립 envelope와 비교하고,
실제 Base64 decoder/import로 왕복한다. numpy/PIL/qrcode import dependencies만 test-local stub하고
encoder 입구에서 멈춘다. production serializer/JSON/Base64/import 로직을 대신 구현하지 않는다.
실제 QR image encoding/recognition 성공 증거가 아니다. JSON picker도 고유 TEMP path로 대체한다.
tests는 optional dependency 설치나 skip 없이 실행되며 canonical production module cache를 오염시키지 않는다.

## Legacy Quirks

manager/Widget pending 경계 차이, disk/runtime/restart 차이, notification/geometry 지연 적용,
duplicate backup의 이전 파일 잔존, 빈 folder/regular file 성공, description 오류의 목록 전체 실패,
style 오류의 initialization 중단, import stale payload/partial application이 알려진 특성이다.
현재 계약을 기록한 것이며 Python 수리나 .NET MUST reproduce 요구가 아니다.

## .NET Compatibility Contract

| Behavior | Classification | .NET requirement | Evidence |
| --- | --- | --- | --- |
| Manual user-profile backup/restore | MATCH | 사용자 복원 기능 제공 | A/T/S |
| 정상 full restore의 restart 유지 | MATCH | 복원한 데이터를 다시 load | A/P |
| 선택 timetable/time sharing | MATCH | category 선택 공유/가져오기 | A/S |
| Legacy 5 JSON | COMPATIBLE | field 의미·구 format 읽기 | A/S |
| Legacy backup folder | COMPATIBLE | 기존 snapshot 입력 읽기 | A/T/S |
| JSON/QR envelope | COMPATIBLE | UTF-8/Base64 envelope 입력 | A/S |
| Heterogeneous save strategies | REDESIGN | 일관된 저장 성공·내구성 경계 | S |
| Non-transactional backup/restore, rollback 없음 | REDESIGN | 부분 결과·실패 복구 정책 명시 | A/T/S |
| Widget pending overwrite | REDESIGN | 복원과 미확정 UI intent 순서 조율 | A/T |
| Runtime/restart mixed state | REDESIGN | 일관된 runtime 적용 정책 | A/P |
| Naming collision, version/manifest/checksum 없음 | REDESIGN | 충돌 및 완전성 검증 정책 | A/T/S |
| Import partial application/error state | REDESIGN | validate/commit 및 실패 상태 명확화 | A/T |
| Persistence ownership dispersion | REDESIGN | 저장과 runtime apply 책임 정리; 구조 미확정 | S |

## Native / Platform Evidence Limits

M3는 추가 native UI가 필수인 단계가 아니었다. 실제 file picker/confirmation dialog appearance,
IME/Tab/focus/native mouse, QR camera/image recognition, full main/tray startup을 native VERIFIED로 표시하지 않는다.
Window Tool+Frameless+Bottom flags는 Qt 테스트에서 유지했지만 offscreen 결과가 native rendering과
같다는 뜻은 아니다. system clock/clipboard/input/OS autostart/notification delivery는 변경·실행하지 않았다.

## Known Unknowns / Out of Scope

M4의 native startup/tray/windowing/autostart/notification/runbook은 남는다. 다른 DPI에서 저장한 geometry의
원래 design size 복원, concurrent process writers, power loss/디스크 장애 전체 matrix, camera/decoder 수리,
release EXE byte-identical 재현은 M3 COMPLETE에 포함되지 않는다. optional UI details 전체 자동화도 gate가 아니다.

전용 module은 22 cases다: full restore/UI, subprocess reload, missing-file replace, partial style/time,
Preview/theme/Apply snapshot, editor snapshot, Widget pending quirk, missing/empty/regular path 3개,
malformed style restore/startup 및 timetable, copy failure 2개, duplicate, QR envelope,
JSON selection 2개, import partial failure/stale payload.
기존 [recovery contracts](../src/utils/test_v101_recovery_contracts.py)의 7개 backup tests는 그대로 유지한다:
`test_create_backup_flushes_pending_widget_settings`,
`test_create_backup_without_name_uses_existing_automatic_name_format`,
`test_create_backup_with_explicit_name_succeeds`,
`test_explicit_backup_name_preserves_description_format`,
`test_restore_backup_cannot_be_overwritten_by_an_older_pending_snapshot`,
`test_create_backup_stops_when_pending_widget_flush_fails`,
`test_restore_backup_stops_when_pending_widget_flush_fails`.
M3는 이들의 이름/flush 단위 검사를 복제하지 않고 profile/UI 관계를 추가한다.

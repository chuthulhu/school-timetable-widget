# School Timetable Widget — Product Contract v0.1

## Status

**Approved baseline v0.1 — ready for new repository bootstrap (2026-09-08).**
현재 legacy Python 저장소에 두는 새 .NET 제품의 new product planning artifact다.
사용자가 P1–P10을 승인하고 A4/A5를 추가 승인하여 제품 계약 baseline을 확정했다.
새 저장소 bootstrap 시 복사하고 링크·용어를 정규화한다. DEFERRED 구현 상세는 남아 있으며
모든 설계 완료, release-ready 또는 모든 상세의 implementation-ready를 뜻하지 않는다.
이번 작업은 승인 반영 문서 수정까지다. 새 repo/project 생성, 구현, package 설치, commit/push/PR은 하지 않는다.

| Reference | Value |
| --- | --- |
| Repository | `chuthulhu/school-timetable-widget` |
| Branch | `recovery-v1-release` |
| Golden Reference commit | `84de32a555633120bd6363a609a19cbc0a15e8ea` |
| 시작 상태 | 최초 초안은 clean에서 시작. 이번 승인 반영은 위 branch/HEAD와 기존 planning 문서 4개만 untracked인 상태에서 시작 |
| Recovery 판정 | COMPLETE AS GOLDEN REFERENCE; remaining MUST 0 |

Golden Reference는 사용자 동작·호환 입력·과거 결함의 증거다. Python 구현 template이 아니다.
기존 문서의 단계별 HEAD, 당시 미커밋/잔여 milestone 표현은 과거 기록으로 보존한다.
현재 계획은 위 고정 commit의 문서를 읽은 결과이며 recovery 완료 상태를 다시 변경하지 않는다.

### Evidence sources

| Source | 이 문서에서 사용하는 근거 |
| --- | --- |
| [Recovery status](LEGACY-RECOVERY-STATUS.md) | 완료 판정, DPI/geometry 및 검증의 범위 |
| [Completion audit](RECOVERY-COMPLETION-AUDIT.md) | 정상 기능, known quirks, document-only/skip 구분 |
| [Feature map](FEATURE-MAP.md) | 5 JSON 의미, 데이터 소유권, sharing envelope |
| [Timetable spec](TIMETABLE-BEHAVIOR-SPEC.md) | 내용 왕복, 교시, 강조, 병합·AutoText 결함 |
| [Settings spec](SETTINGS-BEHAVIOR-SPEC.md) | Preview/Apply/Cancel, theme, precision, minimum |
| [Data lifecycle spec](DATA-LIFECYCLE-SPEC.md) | backup/restore/import, pending, partial failure |
| [Windows runbook](WINDOWS-REFERENCE-RUNBOOK.md) | tray/lifecycle, Windows evidence 및 미검증 범위 |

기존 automated/Qt object/native/source-only 증거의 등급을 그대로 구분한다.
특히 실제 notification delivery, autostart 등록/재로그인, 전체 lock/taskbar/overlap,
사라진 monitor, frozen 실행의 검증 완료를 주장하지 않는다. 이번 작업은 문서 검토만 수행했다.

## Product Goal

Windows 바탕화면에서 주간 시간표와 현재 수업을 빠르게 확인하고, 내용을 안전하게 편집하며,
모양·위치·크기를 유지하고, 기존 데이터를 새 제품으로 옮길 수 있는 작은 개인용 위젯을 만든다.
정상 사용자 의미는 유지하고, 호환 입력은 변환하며, 데이터 손실과 불명확한 저장 동작은 새로 설계한다.
세부 동작의 결정 상태는 아래 표를 따른다.

## Non-Goals

| 범위 | Status | 의미 |
| --- | --- | --- |
| QR 생성, QR image import, camera scan | OUT OF SCOPE — A3 APPROVED | 현재 제품에서 제외; 모바일 앱/동기화 workflow가 실제 범위에 들어올 때만 재검토 |
| 셀 병합·추정 span | OUT OF SCOPE — A2 APPROVED | 초기 제품은 독립 35셀; 향후 실제 요구 시 명시적 merge metadata를 별도 설계 |
| Portable 필수 배포 | OUT OF SCOPE — A1 APPROVED | 초기 출시 필수조건이 아님; 영구 금지는 아님 |
| Legacy bugs 재현 | OUT OF SCOPE | 증거 보존과 제품 요구를 구분하는 사용자 지침; quirk를 자동 이식하지 않음 |
| Python source vendor / architecture copy | OUT OF SCOPE | [ADR 0001](adr/0001-golden-reference-policy.md)의 Accepted 정책 |
| System clock synchronization utility / Windows 시간 설정 변경 | OUT OF SCOPE — A5 APPROVED | 앱 내부 기준시각만 동기화. Windows system clock mutation 금지 |
| Time server 관리 UI / 임의 timezone·world clock | OUT OF SCOPE | 학교 시간표 위젯의 현재 제품 범위가 아님 |
| 모바일 sync | OUT OF SCOPE | 실제 제품 범위에 들어올 때 별도 검토; QR 재도입 근거가 아님 |
| Gap 이름 지정(점심시간 등) | OUT OF SCOPE | 긴 gap도 쉬는시간. 이름 지정은 향후 별도 feature |

## Decision Status Legend

| Status | 의미 |
| --- | --- |
| APPROVED | 사용자가 명시적으로 확정한 결정. 다시 승인 요청하지 않음 |
| PROPOSED | 향후 추천안에 사용할 상태. 현재 P1–P10은 모두 APPROVED |
| DEFERRED | 해당 구현 단계의 ADR/UI 설계에서 결정 |
| OUT OF SCOPE | 현재 제품 범위에서 제외 |
| LEGACY EVIDENCE | 과거 동작의 근거이며 새 제품 요구가 아님 |

**MATCH / COMPATIBLE / REDESIGN은 이식 분류이며 승인 상태가 아니다.**
A1–A5, P1–P10 및 연결된 MATCH/COMPATIBLE/REDESIGN의 제품 수준 계약과 invariants는 APPROVED다.
명시적 DEFERRED 항목은 구현 단계에서 결정하며 승인 상태를 전파하지 않는다.
이번 승인의 근거는 사용자 승인 결과다. 기존 RECOMMENDED, updater/build B 판정이나 테스트 존재만으로 승인한 것이 아니다.

## Approved Product Decisions

| ID | Status | 확정된 제품 결정 | 확정하지 않은 상세 |
| --- | --- | --- | --- |
| A1 | APPROVED | 일반 사용자 단위 설치형 기본 배포, Windows 시작 시 실행 옵션, 정상 uninstall, Portable 초기 필수 아님 | installer technology와 updater library는 DEFERRED; autostart 기본 OFF는 P7 |
| A2 | APPROVED | 월~금 × 7교시 독립 35 cells, 초기 셀 병합 없음. 반복 문자열에서 병합 의도 추론 금지. import는 문자열 보존 | 향후 병합 요구가 생기면 새 metadata 기능으로 별도 검토 |
| A3 | APPROVED | QR 기능 제외. 공유는 PC ↔ PC 파일 기반을 기본으로 함 | timetable/time 선택 공유 상세는 P10, 파일 format은 DEFERRED |
| A4 | APPROVED | Current Status Header: 요일 헤더 위의 독립된 고정 높이 영역에 현재 시각 `HH:mm:ss`(24시간제)와 학교 시간 상태를 항상 함께 표시 | countdown formatting, font/layout 구현, Upcoming 보조 강조는 DEFERRED |
| A5 | APPROVED | Application Clock / Standard Time Source: 공통 앱 시간원, KRISS 대한민국 표준시(KST) 우선, PC local time으로 즉시 시작 및 동기화 불가 시 fallback, Windows system clock 변경 금지 | endpoint/NTP/timeout/retry/resync/correction/monotonic 구현 및 test injection은 DEFERRED; [ADR 0004](adr/0004-application-time-source.md) |

## Approved Decisions — P1–P10

| ID | Status | 승인된 제품 결정 | 상세 / 유보 경계 |
| --- | --- | --- | --- |
| P1 | APPROVED | WPF + .NET 10 LTS + CommunityToolkit.Mvvm | WinUI 3 비교 및 위험은 [ADR 0002](adr/0002-windows-desktop-stack.md); 구조·installer·updater 미확정 |
| P2 | APPROVED | Committed → Draft → Live Preview, 성공 Apply마다 baseline 갱신 | Theme/Reset도 동일 규칙; [ADR 0003](adr/0003-settings-transaction.md) |
| P3 | APPROVED | preferred size와 applied size 구분, Preview에서도 content minimum 재측정 | actual < minimum 금지; 화면보다 큰 minimum의 overflow UX는 DEFERRED |
| P4 | APPROVED | current-period 구간 `[start, end)` | 시작 포함·종료 제외; legacy exact-end inclusive를 의도적으로 변경 |
| P5 | APPROVED | 신규 설치 알림 OFF, 활성화 시 시작/사전 알림, 빈 수업 제외, 중복 방지, resume 후 지난 알림 몰아 보내지 않음 | scheduling policy와 Windows delivery 분리 |
| P6 | APPROVED | tray icon/show-hide/명시적 Exit 완전 종료, 사용자/profile당 writer 하나, 이동 잠금·resize 허용, taskbar 미표시 위젯 | 두 번째 실행은 기존 instance 표시/활성화; main close 의미는 DEFERRED |
| P7 | APPROVED | 신규 설치 autostart OFF, Settings에서 명시적 활성화 | migration의 true는 선호로만 표시하고 사용자 승인 후 OS 등록 |
| P8 | APPROVED | source 표시 → read-only parse → validation → 변환 preview/report → 사용자 선택 → 새 profile 1회 commit | 원본 불변, partial import 금지, corrupt ≠ missing, 자동 재import 금지 |
| P9 | APPROVED | 전체 profile backup/restore 및 legacy backup importer, committed revision 하나에서 backup | 전체 검증 후 restore, 실패 시 기존 상태 유지/완전 rollback; format 상세 DEFERRED |
| P10 | APPROVED | timetable와 period/time settings를 선택적으로 파일 공유 | PC ↔ PC 파일 방식 자체는 A3 APPROVED; QR 제외; format DEFERRED |

## MATCH Product Contracts

아래는 Golden Reference의 정상 사용자 의미를 추출한 APPROVED 제품 계약이다.
A4 Status Header와 A5 Application Clock은 새 제품 결정이며 legacy MATCH 증거로 분류하지 않는다.
각 성공 조건은 persistence 성공을 전제로 하며 실패를 성공처럼 처리하는 legacy quirk는 제외한다.

| ID | 영역 | 새 제품에서 유지할 사용자 의미 | Reference / 관련 결정 |
| --- | --- | --- | --- |
| M1 | Timetable | 월~금 × 7교시, 독립 35셀, 빈 셀 허용. 한글/Unicode, 앞뒤 공백, whitespace-only, newline 보존. 입력을 plain text로 표시 | Timetable spec; A2, R3. plain text는 기존 editor 의미를 유지하고 main AutoText를 변경 |
| M2 | Editing | Save 성공 즉시 화면에 반영하고 재시작 후 유지. Cancel/X는 미저장 편집만 폐기 | Timetable spec; R16 |
| M3 | Period/time | 7교시 편집 및 아래 기본 profile 제공. 저장 성공 후 current-period 즉시 재계산 | Timetable spec; exact boundary는 APPROVED P4 `[start,end)` 및 A5 공통 clock 적용 |
| M4 | Highlight | 평일 current weekday/current period의 body cell 하나만 강조. 빈 셀도 강조. 쉬는 시간/주말에는 강조 없음 | Timetable spec; 날짜 stale 제거 R4, layout 불변 R5 |
| M5 | Appearance | font/colors/opacity live preview, Apply 후 persistence, restart restore. header/body 및 highlight의 설정 의미 유지 | Settings spec; transaction은 P2, 크기/minimum은 P3 |
| M6 | Window | move, resize, geometry restore, hide/show, DPI/multi-monitor의 자연스러운 크기 변화와 왕복 안정성 | Recovery status / Windows runbook; P3/P6 |
| M7 | Data | 사용자 profile backup/restore, 파일 기반 timetable/time sharing | Data lifecycle spec; P8/P9/P10. legacy에 JSON export UI가 있었다고 주장하지 않음 |

| 기본 교시 | 시간 |
| --- | --- |
| 1 | 09:00–09:50 |
| 2 | 10:00–10:50 |
| 3 | 11:00–11:50 |
| 4 | 12:00–12:50 |
| 5 | 14:00–14:50 |
| 6 | 15:00–15:50 |
| 7 | 16:00–16:50 |

P4 예: 09:00:00 및 09:49:59는 1교시, 09:50:00은 쉬는 시간 또는 그 시각에 시작하는 다음 교시다.
기존 Timetable spec의 exact-end inclusive MATCH 표기는 **LEGACY EVIDENCE**로만 유지한다.
새 제품은 **APPROVED P4 `[start,end)`**를 A5 Application Clock이 제공하는 날짜·시각에 적용한다.
Current-period, break, countdown, notification scheduling은 같은 clock과 같은 interval semantics를 따른다.
UI 갱신 지연 허용치와 clock/resume 처리 세부는 DEFERRED다.

## Current Status Header

**APPROVED — A4.** 월/화/수/목/금 요일 헤더 위에 시간표 grid와 독립된 고정 높이의 Status Header를 둔다.
35-cell timetable data model에 새 셀/행을 추가하지 않는 별도 UI 영역이다.
항상 현재 시각 `HH:mm:ss`(24시간제)와 현재 학교 시간 상태를 함께 표시한다.
현재 시각·날짜·학교 상태·countdown은 모두 A5의 동일한 Application Clock을 사용한다.

| 상태 | 현재 시각 예 | 학교 상태 예 | Current body cell |
| --- | --- | --- | --- |
| 평일 수업 전 | 08:42:11 | 1교시까지 17분 | 강조 없음 |
| 수업 중 | 09:23:18 | 1교시 · 종료까지 26분 | 해당 요일/current period 1셀을 강하게 강조; 빈 셀도 포함 |
| 쉬는시간 | 09:54:07 | 쉬는시간 · 2교시까지 5분 | 강조 없음 |
| 긴 교시간 공백 | 13:07:42 | 쉬는시간 · 5교시까지 52분 | 강조 없음 |
| 마지막 수업 이후 | 16:58:26 | 오늘 수업 종료 | 강조 없음 |
| 주말 | 11:24:03 | 오늘은 수업이 없습니다 | 강조 없음 |

표는 기본 교시 profile의 UX 예다. 분 표시의 반올림/버림 규칙을 확정한 예가 아니다.
수업 중 countdown은 현재 교시 종료까지, 수업 전/쉬는시간은 다음 교시 시작까지의 남은 시간을 뜻한다.
P4 `[start,end)`에 따라 정확한 종료 시각에는 종료한 교시를 current로 강조하지 않는다.
주말에는 시각상 수업 구간과 겹쳐도 주말 상태를 표시하며 current 강조가 없다.
Gap 길이로 점심시간을 추론하지 않는다. 4→5교시 공백도 일반적인 쉬는시간이다.
사용자가 gap 이름을 붙이는 기능은 현재 계약 밖의 별도 feature다.

**APPROVED layout invariants:** 상태/시각 변경으로 Header 높이가 흔들리지 않는다.
초 단위 갱신으로 widget 전체 geometry가 바뀌지 않고, 시각 문자열 폭 변화도 layout을 흔들지 않는다.
가능하면 tabular numeral 특성을 활용하는 방향이며 font/layout 구현은 DEFERRED다.
Header update는 35셀 전체 layout 재측정을 매초 요구하지 않는다.
Current highlight 변경도 layout measurement를 바꾸지 않는다.

**DEFERRED:** 다음 교시 Upcoming 보조 highlight는 optional UX candidate이며 필수가 아니다.
Current와 Upcoming을 혼동하지 않는다. 초 단위 countdown 표시 여부, 분 반올림/버림,
`1분 미만`, 정확히 00분 및 transition 직전 문자열은 formatting policy에서 결정한다.
현재 시각의 초 표시(`HH:mm:ss`)는 APPROVED이며 countdown 정밀도 유보와 구분한다.

## Application Time Source

**APPROVED — A5**, [ADR 0004](adr/0004-application-time-source.md).
기본적으로 KRISS 대한민국 표준시(KST)에 동기화한 앱 내부 시간을 authoritative clock으로 사용한다.
앱 시작은 시간 서버 응답을 기다리지 않는다:

1. PC local time으로 즉시 시간표와 Header를 표시한다.
2. Background에서 KRISS 대한민국 표준시 동기화를 시도한다.
3. 성공하면 공통 Application Clock을 synchronized KST 기준으로 전환한다.
4. 동기화가 불가능하면 PC local time fallback을 사용한다. 시작 시 실패하면 PC 시각을 계속 사용한다.
5. 동기화 실패가 앱 시작이나 기본 시간표 사용을 막지 않는다.

앱은 **Windows system clock을 변경하지 않으며**, 동기화에 관리자 권한이나 시스템 clock mutation을 요구하지 않는다.
동기화 성공 뒤 매초 서버를 조회하지 않는다. 동기화한 reference에서 앱 내부 clock이 자연스럽게 진행한다.
가능하면 monotonic elapsed-time source로 wall clock 변경/timer jitter 영향을 줄이는 방향이며,
구체적 monotonic source와 시간 보정 알고리즘은 DEFERRED다.

### Single Application Clock

**APPROVED architecture invariant:** 하나의 공통 application time abstraction을 사용한다.
이름은 ApplicationClock 또는 TimeProvider 같은 개념 예시이며 구현 type을 확정하지 않는다.
Header의 `HH:mm:ss`, current-period, break, 다음 교시 countdown, 수업 종료,
weekday/date, notification scheduling은 모두 이 source를 사용한다.
기능별 직접 `DateTime.Now` / `DateTimeOffset.Now` 읽기를 금지한다.
PC fallback을 읽는 clock 경계 외부에서 별도 system clock을 사용하지 않는다.
Header는 KRISS, period calculator는 PC 시각, notification은 별도 clock을 읽는 구조는 허용하지 않는다.

모든 기능은 동일한 clock source/revision을 관찰한다. 한 번의 관련 상태 계산은 일관된 날짜·시각 snapshot을 사용하여
자정이나 sync 전환 중 서로 다른 source의 결과를 섞지 않는다. 여기서 clock revision은 동기화 reference/source의
일관성을 뜻하며 persistence의 committed profile revision과 구분한다. 구체적인 전파/주입 방식은 DEFERRED다.
Current-period와 break/countdown/notification scheduling은 같은 clock과 APPROVED `[start,end)` 경계를 따른다.

### Synchronization Details UX

**APPROVED:** 메인 Header는 현재 시간 + 학교 상태에 집중한다. 기술 동기화 상태를 상시 반복 노출하지 않는다.
시간 기준, 마지막 동기화, fallback 여부는 Settings 또는 tooltip/status detail에서 확인 가능하게 한다.
예: `시간 기준: 대한민국 표준시(KRISS) / 마지막 동기화: 13:02:14`.
Fallback 예: `시간 기준: PC 시각 / 표준시 동기화 실패 / 다음 동기화 시 다시 시도`.
예시 문구는 정확한 재시도 주기를 약속하지 않는다. 상세 표시 위치는 DEFERRED다.

**DEFERRED — Time Synchronization ADR / implementation spike:** 공식 KRISS endpoint, NTP client,
timeout, retry 횟수, periodic resync interval, drift correction, abrupt correction vs slew,
offline cache, monotonic 구현, test injection mechanism, suspend/resume 처리 상세.
공식 endpoint는 실제 구현 시 당시 공식 KRISS 문서로 재확인한다. 이 계획 문서에 임의 endpoint를 hard-code하지 않는다.
후속 spike는 clock 보정 시 상태 jump, fallback 오차, network 차단, resume와 notification 중복/지난 알림 억제를 검증해야 한다.

## COMPATIBILITY Requirements

**APPROVED — P8/P9.** 기존 JSON 의미를 읽고 새 내부 schema로 변환한다.
파일명/Qt 객체/저장 방식까지 새 내부 구조로 유지하는 요구는 없다.
기준은 [Feature map](FEATURE-MAP.md)과 [Data lifecycle spec](DATA-LIFECYCLE-SPEC.md)이다.

| ID | Legacy input | 보존할 의미 / 변환 경계 |
| --- | --- | --- |
| C1 | `widget_settings.json` | position, size, is_position_locked, screen_info, auto_start_enabled. source DPI가 없으므로 정확한 design geometry 복원을 주장하지 않고 변환 가정·보정을 보고. autostart는 P7 |
| C2 | `style_settings.json` | 6종 색상, header/cell/current-period/border opacity 0–255, theme, header/cell font. 개별 font 누락 시 구 font_family/font_size fallback 의미를 읽음. RGB/opacity 수치를 불필요하게 재양자화하지 않음 |
| C3 | `timetable_data.json` | 한국어 요일 → 문자열 교시 key → 문자열. 누락 셀은 빈 셀로 변환하고 report에 표시. 반복 문자열·공백·newline 그대로 보존. merge/span 복원 안 함(A2) |
| C4 | `time_settings.json` | 문자열 교시 → start/end. 정상 legacy `9:00` 등 읽을 수 있는 시각은 명시적 정규화 보고. 누락 교시는 기본 profile로 보충하고 보고. invalid/reversed/overlap/extra period는 조용히 적용하지 않음 |
| C5 | `notification_settings.json` | notification_enabled, next_period_warning, warning_minutes 선호 읽기. 신규 설치 OFF와 구 선호 변환을 구분하고 실제 delivery는 별도 사용자 설정/OS 상태에 따름 |
| C6 | legacy backup folders | 위 5파일 및 선택적 description.txt를 입력으로 읽음. 일부 파일만 있는 folder는 누락을 보고하고 전체 변환 candidate를 검증. 기존 profile과 암묵적 부분 혼합 금지 |
| C7 | sharing envelope의 JSON 부분 | DEFERRED — PC 파일 입력의 COMPATIBLE 후보이며 실제 지원 상세는 후속 format 검토에서 결정. `timetable`/`time_settings` 최상위 category를 식별하고 선택한 내용만 명시적으로 변환 |

raw timetable JSON과 sharing envelope는 서로 다른 입력이다:

```json
{"월": {"1": "국어\n2층"}}
```

```json
{"timetable": {"월": {"1": "국어\n2층"}}, "time_settings": {"1": {"start": "09:00", "end": "09:50"}}}
```

첫 예는 C3, 둘째는 C7이다. 잘못된 shape를 빈 시간표로 성공 처리하지 않는다.
Legacy QR은 envelope의 UTF-8 JSON을 Base64로 감싼 **LEGACY EVIDENCE**다.
Base64 payload decoder, QR image/camera compatibility는 필수 migration blocker가 아니며 현재 기능 범위 밖이다(A3).
Legacy의 이미 손실된 문자열/alpha나 없는 merge metadata를 복원할 수 있다고 약속하지 않는다.

## REDESIGN Requirements

왼쪽은 **LEGACY EVIDENCE**이며 오른쪽은 새 desired contract다.
오른쪽의 제품 수준 계약은 **APPROVED**, 명시한 구현 상세는 **DEFERRED**다. 기존 quirk를 새 요구로 자동 승격하지 않는다.

| ID | Legacy evidence | 새 desired contract / 관련 결정 |
| --- | --- | --- |
| R1 | Timetable L1/L2: `A,A,B` open/save → `A,A,A`, merge 인접 셀 overwrite | A2 APPROVED: 병합 기능 제외, 독립 셀 문자열 무손실 유지 |
| R2 | Timetable L3–L5: 반복값 추정 span 초과/분할 예외/일부 병합 누락 | A2 APPROVED: inferred merge/span logic 제외 |
| R3 | Timetable L10: QLabel AutoText가 `<b>과목</b>` 태그를 해석 | 입력 그대로 plain text 표시. markup 실행/해석 안 함 |
| R4 | Timetable L6: 같은 period이면 날짜가 바뀌어도 금요일 강조 잔존 | 날짜와 시각을 함께 재평가; 주말/쉬는 시간은 no-highlight |
| R5 | Timetable highlight border가 HFW required height를 +2px 늘릴 수 있음 | 강조 전후 layout measurement/geometry 불변; 그리는 방식은 DEFERRED |
| R6 | Timetable L8: invalid QTime이 새벽과 매칭, reversed/overlap 검증 없음 | 형식·범위·관계 검증 후 저장/계산. 잘못된 시간은 오류를 표시하고 commit 차단. 허용 관계 세부는 time ADR에서 DEFERRED |
| R7 | Timetable exact-end inclusive | P4 APPROVED: A5 공통 clock에 `[start,end)` 적용. 기존 exact-end inclusive는 LEGACY EVIDENCE / REDESIGN |
| R8 | Settings Apply 후 최초 rollback baseline 유지 | P2: 마지막 성공 Apply마다 committed/baseline 갱신 |
| R9 | Theme 선택이 Preview 값까지 whole-style 즉시 저장 | P2: Theme도 Draft/Preview, Apply 전 저장 없음 |
| R10 | Opacity percent↔byte 절삭 및 rollback signal 재진입으로 값 손실 | 편집하지 않은 값과 rollback baseline을 정확히 보존. 표시 변환이 원본 값을 덮어쓰지 않음 |
| R11 | Color picker alpha를 HexRgb 변환에서 손실 | alpha 입력 지원과 저장 표현을 일치시킴. 지원하지 않으면 해당 입력을 제공하지 않음; representation은 DEFERRED |
| R12 | Font Preview required height 증가에도 actual 유지, clipping | P3: Preview마다 minimum 재측정, actual ≥ content minimum; overflow UX 별도 설계 |
| R13 | Settings requested size/control과 실제 크기의 불일치 | P3: preferred/applied 차이와 보정 이유를 사용자에게 표현 |
| R14 | 위치 Reset target이 Cancel 뒤 남고 실제 위치와 불일치 | P2: Reset은 Draft만 변경; owned runtime position도 Cancel/실패 baseline으로 복원 |
| R15 | 일부 저장만 atomic/debounce, 나머지 직접 write | 일관된 committed revision과 저장 성공/실패 경계. persistence 기술은 DEFERRED |
| R16 | Timetable/time 저장 실패를 삼키고 Accepted 가능 | 실패는 오류 표시, 편집값 유지, 성공/종료로 가장하지 않음 |
| R17 | Non-transactional backup/restore, disk/runtime/restart 혼합 | P9: 단일 committed revision backup, 완전한 restore 검증·적용, restart도 같은 의미 |
| R18 | 두 번째 copy 실패 시 일부 restore만 남고 rollback 없음 | P8/P9: 기존 committed state 유지 또는 완전 rollback, partial commit 금지 |
| R19 | Widget pending intent가 restore 뒤 새 save를 만들어 덮어씀 | P8/P9: 이전 revision의 UI intent/pending write를 차단·정리한 뒤 전환; 과거 baseline의 Cancel도 복원 결과를 덮지 않음 |
| R20 | Backup 이름 충돌, 기존 folder 재사용으로 stale files 잔존 | P9: snapshot 간 파일 혼합 금지, 충돌을 명시적으로 처리. naming/metadata는 DEFERRED |
| R21 | Malformed profile partial state, corrupt를 빈 데이터/성공으로 취급, stale import payload | P8/P9: corrupt ≠ missing, 완전 검증 전 commit 금지. 실패한 입력에 이전 payload를 성공 대상으로 남기지 않음 |
| R22 | Updater running1.0.0/release1.0.1 불일치, TEMP 실행만으로 교체 미완료 | 일관된 제품 version identity와 확인 가능한 update 결과를 갖도록 재설계. updater 제공 범위/기술/서명·rollback 전략은 DEFERRED |
| R23 | Single-instance guard 없음; process killer는 guard가 아님 | P6: 사용자/profile당 writer 하나, 두 번째 실행은 기존 instance 표시/활성화 |
| R24 | 쉬는 시간 예고 callback 누락, 실제 toast는 미검증 | P5: scheduling과 delivery 분리, 시작/사전 알림·dedup·resume 정책을 독립 검증 |

R1–R7/R16은 Timetable spec, R8–R14는 Settings spec, R15/R17–R21은 Data lifecycle spec,
R22–R24는 Completion audit 및 Windows runbook에 근거한다. 개선 상세는 현재 .NET 검증 결과가 아니다.

## Data Safety Principles

**APPROVED — P2/P8/P9/P10 및 R15–R21.**
Commit은 검증과 persistence가 성공하여 하나의 새 revision을 authoritative state로 확정한 시점이다.
UI, runtime, 저장 데이터의 revision 관계를 설명할 수 있어야 하며, Preview는 명시적으로 구분한다.
Save/Import/Restore 실패는 성공처럼 보이지 않아야 한다. 선택 작업 전체가 성공하거나 기존 상태를 유지한다.
여러 legacy 파일을 읽더라도 새 profile에 partial committed state를 남기지 않는다.

Preview를 backup에 몰래 포함하지 않는다. 적용되지 않은 편집이 있으면 committed revision을 대상으로 함을 알린다.
Migration/restore 중에는 기존 Draft, geometry intent, debounce write가 새 revision을 덮어쓰지 않아야 한다.
동시 작업을 막을지, Draft를 폐기/재기준화할지의 구체적 UI/동시성 방식은 DEFERRED다.
프로세스 중단/전원 손실을 포함한 내구성 구현과 복구 방식은 persistence ADR에서 검증하며,
현재 Python의 atomic widget file 하나를 전체 transaction 증거로 사용하지 않는다.

## Settings Transaction Contract

**APPROVED — P2**, [ADR 0003](adr/0003-settings-transaction.md)와 동일한 승인 계약이다.

| Action | Draft / preview / owned runtime | Persistence / committed / rollback baseline |
| --- | --- | --- |
| Open | 마지막 committed state에서 Draft와 baseline 복사 | 저장 없음 |
| Preview | Draft를 visual runtime에 적용. font/layout 변경은 P3 minimum 재측정 | persistence 없음; committed/baseline 불변 |
| Theme | 다른 appearance와 같은 Draft/Preview | 즉시 whole-style save 없음 |
| Reset (위치 포함) | Draft 변경, preview하는 owned state도 추적 | Apply 전 저장/OS 변경 없음 |
| Apply 성공 | 검증한 결과 반영, controls 동기화, dialog 유지 | persistence 성공 후 committed와 rollback baseline을 같은 새 결과로 갱신 |
| OK | Apply 수행, 성공한 경우에만 닫기 | Apply와 같은 성공 경계 |
| Cancel / X | 마지막 성공 Apply baseline으로 controls + preview + owned runtime state 완전 복원 후 닫기 | baseline 이전으로 되돌리지 않음; 새 저장/OS 부작용 없음 |
| 검증/저장 실패 | Draft/dialog 유지, 오류 표시, 수정/재시도 가능 | committed/baseline 불변, partial commit 없음 |

예: 10pt에서 Open → 18pt Apply 성공 → 24pt Preview → Cancel/X는 18pt로 돌아간다.
18pt Apply가 실패하면 24pt 편집을 계속할 수 있으나 Cancel 기준은 여전히 10pt다.
Preview와 UI 변환만으로 opacity/alpha를 잃거나 signal 재진입으로 baseline을 바꾸지 않는다.
별도 timetable/time editor에서 성공한 Save를 Settings Cancel이 되돌리는 의미는 없다.
OS registration/delivery 실패는 profile persistence 실패와 구분하며 아래 lifecycle 원칙을 따른다.

## Window / Tray Contract

**APPROVED — P3/P6.**
사용자가 요청한 preferred size와 현재 content/layout이 허용하는 applied size를 구분한다.
Preview에서도 font/wrap/layout 변화에 따라 minimum을 재측정하며 actual < content minimum을 허용하지 않는다.
Controls는 두 크기 관계와 보정 이유를 알 수 있게 한다. 화면보다 큰 minimum을 처리할 overflow UX는 DEFERRED다.
DPI/monitor 전환은 preferred geometry를 누적 변형하지 않으며 hide/show와 restart도 저장 의도를 유지한다.
Legacy 저장값에 source DPI가 없는 경우 변환 보고에서 불확실성을 밝힌다.

Tray icon과 show/hide toggle을 제공하고 명시적 Exit는 widget/icon 및 소유 process를 완전히 종료한다.
Lock은 이동만 잠그고 resize는 허용한다. taskbar 미표시 desktop-widget 방향을 유지한다.
Legacy Bottom/Tool/Frameless flags 자체나 always-on-top을 새 제품 기본값으로 확정하지 않는다.
두 번째 실행은 같은 사용자/profile의 기존 instance를 표시하거나 활성화하며 writer를 추가하지 않는다.
Main close button의 hide/exit 의미, z-order, 사라진 monitor의 구체적 배치 정책은 DEFERRED다.

## Migration Contract

**APPROVED — P8.**

1. Legacy profile/backup을 탐지하고 실제 source 경로와 입력 종류를 표시한다.
2. 원본을 read-only로 읽는다. 접근 실패, 파일 없음, corrupt/wrong-schema를 구분한다.
3. 새 schema 후보 전체를 검증한다. 문자열은 보존하고 missing/default 보충, 지원 밖 key, geometry 가정을 보고한다.
4. Conversion preview/report를 보여주고 가져올 내용을 사용자가 선택한다. 오류가 있으면 commit하지 않는다.
5. 검증한 선택 결과를 새 profile에 한 번 commit한다. 실패하면 partial profile을 활성화하지 않는다.
6. 성공 후 자동 재import하지 않는다. 원본 파일 이동/수정/삭제 금지. legacy 앱 자체를 재구성하지 않는다.

DEFERRED: importer version, source hash, import 결과/revision 등 provenance 기록의 항목·schema와
source가 검토 중 바뀐 경우의 재검증 방식은 후속 persistence/importer 설계에서 결정한다.
기존 `auto_start_enabled=true`는 report의 선호이며 즉시 Windows 등록을 바꾸지 않는다(P7).
알림의 legacy 기본 true/true/5는 LEGACY EVIDENCE이고 신규 설치 기본 OFF 계약을 덮지 않는다(P5).

## Backup / Restore Contract

**APPROVED — P9.**
전체 profile의 시간표·교시·appearance·geometry/lock·notification/autostart 선호를 backup/restore 대상으로 한다.
실제 OS Startup registration이나 알림 전달 상태는 profile 값과 구분하며 backup 파일만으로 복원 성공을 주장하지 않는다.
새 backup은 하나의 committed revision을 담고 Preview/서로 다른 시점/stale files를 섞지 않는다.
성공한 snapshot과 실패한 불완전 출력을 구별한다. 충돌이 기존 backup을 조용히 덮어쓰지 않게 한다.

Restore는 전체 입력 검증과 대체 내용 검토 후 적용한다. 성공 시 runtime과 persisted state가 같은 revision을 따른다.
실패하면 기존 committed state를 유지하거나 완전 rollback한다. 과거 UI pending intent가 이후 덮어쓰지 못한다.
Legacy backup folder도 먼저 conversion candidate로 만든 뒤 같은 성공/실패 경계를 따른다.
누락 파일을 현재 runtime과 암묵적으로 섞는 legacy restore는 재현하지 않는다.
Manifest/schema/checksum, archive 여부, naming, durability/recovery 구현은 format ADR에서 DEFERRED다.

## Sharing Scope

**APPROVED — A3:** PC ↔ PC 파일 기반 공유. QR 생성/이미지 import/camera scan 제외.
**APPROVED — P10:** timetable와 period/time settings를 각각 또는 함께 내보내고 가져온다.
파일 공유는 전체 profile backup과 구분한다. 선택하지 않은 category는 유지하고, 선택한 내용은 검증 후 함께 commit한다.
가져올 범위, 대체/누락 보충 결과를 먼저 보여주며 취소/실패는 기존 committed state를 바꾸지 않는다.
원시 timetable JSON은 C3에 따라 처리한다. Legacy sharing JSON envelope 지원 상세는 C7의 DEFERRED 후보이며,
지원할 경우 raw timetable과 구분한다. P10의 선택적 파일 export/import 기능 자체는 APPROVED다.
새 파일 format, versioning, 부분 time 항목의 정확한 대체/보충 UX는 DEFERRED다.

## Installation / Lifecycle

**APPROVED — A1:** 일반 사용자 단위 설치, Windows 시작 시 실행 옵션, 정상 uninstall.
Portable은 초기 필수 요구가 아니다. 관리자 권한 의존 최소화는 설계 방향이며 실제 installer 권한 요건은 **DEFERRED**다.
A5의 시간 동기화는 이와 별개로 관리자 권한이나 Windows system clock 변경에 의존하지 않는다.
**DEFERRED:** MSIX/MSI/WiX/Squirrel/기타 installer technology, updater library 및 update 정책,
지원 Windows 버전, runtime 배포 방식, uninstall 시 사용자 데이터 보존/삭제 선택의 상세.

**APPROVED — P7:** 신규 설치 autostart 기본 OFF. Settings에서 사용자가 명시적으로 켠다.
Migration/restore에서 읽은 autostart 선호는 실제 OS registration과 구분하고 사용자 승인 후 적용한다.
**APPROVED — P5:** 신규 설치 알림 기본 OFF. 활성화하면 시작·사전 알림을 제공하되 빈 수업 제외,
중복 방지, sleep/resume 이후 지난 알림 몰아서 보내지 않음을 지킨다. whitespace-only를 빈 수업으로 볼지는
notification ADR에서 DEFERRED이며 원본 문자열을 trim하는 근거가 되지 않는다.

OS side effects(autostart/notifications/update)는 profile preference와 실제 OS state를 별도로 표현한다.
Profile 저장 성공이 OS 등록/전달 성공을 뜻하지 않는다. 외부 효과 실패는 오류/불일치를 드러내고 재시도 가능하게 한다.
OS 실패 시 preference 재조정/보상 순서의 기술 상세는 해당 adapter ADR에서 DEFERRED다.
정상 Exit는 pending 사용자 저장을 처리하고 소유 자원을 정리한다. 저장 실패를 숨긴 채 종료 성공으로
표시하지 않는다. 강제 종료/전원 손실의 내구성은 별도 검증하며 legacy aggressive process killer를 가져오지 않는다.

## Candidate Architecture

**APPROVED — P1:** WPF + .NET 10 LTS + CommunityToolkit.Mvvm.
**DEFERRED — candidate architecture:** feature-oriented 구성, Windows adapter isolation, persistence boundary,
거대한 AppState/MainWindowViewModel 방지, Shared/Utils에 책임을 몰아넣지 않는 구체적 구조.
A5의 공통 application clock 사용은 APPROVED invariant이며 type/배치/주입 방식만 DEFERRED다.
정확한 모듈·폴더·type·schema 및 P1에서 선택한 것 외의 library 선택은 DEFERRED다. 이 문서나 기존 Feature Map의 경로 예시만으로
새 repo structure를 이번 작업에서 생성하지 않는다. Bootstrap은 다음 단계에서 수행할 수 있다.

## Product-Level Invariants

I1–I14는 승인된 P1–P10에 맞춰 APPROVED로 정규화했다.
I15–I20은 A4/A5의 새 APPROVED invariant다. 구현 acceptance 기준이며 실행 검증 완료를 뜻하지 않는다.

| ID | Status | Invariant |
| --- | --- | --- |
| I1 | APPROVED | User-visible state와 persisted committed state의 차이는 명시적 Preview 외에도 이유/revision으로 설명 가능해야 한다 |
| I2 | APPROVED — P2 | Apply 성공 후 Cancel/X는 마지막 성공 Apply가 기준이다 |
| I3 | APPROVED | 실패한 Save/Import/Restore를 성공처럼 표시하지 않는다 |
| I4 | APPROVED — P8/P9 | Restore/import 실패가 일부 committed state만 남기지 않는다 |
| I5 | APPROVED — P8 | Migration은 legacy source data를 수정·이동·삭제하지 않는다 |
| I6 | APPROVED | 사용자 시간표 text를 암묵적으로 trim하거나 HTML/render transformation하지 않는다 |
| I7 | APPROVED — A2 | Repeated strings는 merge metadata가 아니다. 셀 간 내용을 자동 합치거나 덮어쓰지 않는다 |
| I8 | APPROVED — P3/P6 | DPI/monitor 변경은 preferred geometry를 누적 변형하지 않는다 |
| I9 | APPROVED | Visual highlight는 layout measurement를 바꾸지 않는다 |
| I10 | APPROVED — P2 | Settings Preview는 Theme/Reset을 포함해 Apply 전 persistence를 발생시키지 않는다 |
| I11 | APPROVED — P5/P7 | Autostart/notifications/update의 preference와 실제 OS state를 구분한다 |
| I12 | APPROVED — reference policy | Golden Reference quirk는 explicit REDESIGN review 없이 새 test expectation이 될 수 없다 |
| I13 | APPROVED — P2 | Cancel은 persisted data를 몰래 바꾸지 않는다 |
| I14 | APPROVED — P3 | Preview를 포함하여 actual size가 content minimum보다 작아지지 않는다 |
| I15 | APPROVED — A4 | Header의 초/상태 변경은 높이·문자열 폭·widget geometry/layout을 흔들지 않고, 매초 35셀 전체 layout 재측정을 요구하지 않는다 |
| I16 | APPROVED — A5 | 현재 시각/current-period/break/countdown/수업 종료/weekday/date/notification scheduling은 하나의 application clock을 사용한다 |
| I17 | APPROVED — A5 | 표준시 동기화 실패는 앱 시작과 기본 시간표 사용을 막지 않는다 |
| I18 | APPROVED — A5 | 앱은 Windows system clock을 변경하지 않으며 시간 동기화에 관리자 권한을 요구하지 않는다 |
| I19 | APPROVED — A5 | KRISS 동기화 unavailable 시 PC local time fallback을 사용한다 |
| I20 | APPROVED — A5 | 서버 동기화 주기와 무관하게 모든 기능은 동일 clock source/revision을 관찰하고 관련 상태 계산에 일관된 날짜·시각 snapshot을 사용한다 |

## Deferred Design Details

이 표는 지금 승인 요청하는 결정 목록이 아니다. 해당 구현 단계 전에 ADR/UX 검토로 정한다.

| 관련 결정 | Status | 후속 결정 |
| --- | --- | --- |
| A1/P1/P7 | DEFERRED | installer technology, 권한 실증, OS 지원 범위, runtime 배포, uninstall 데이터 정책 |
| P1/R22 | DEFERRED | updater 범위/library, version identity 구현, update 검증/복구 |
| P2/P8/P9 | DEFERRED | persistence schema/technology, revision/동시성, crash recovery, source provenance 형식 |
| P3/P6 | DEFERRED | 화면보다 큰 minimum overflow UX, main close 의미, z-order, monitor 제거 배치 |
| P4/P5 | DEFERRED | time validation 세부, clock/resume 갱신 지연, 알림 빈 수업 판정 및 delivery adapter |
| P9/P10 | DEFERRED | backup manifest/schema/checksum/naming, sharing format와 부분 적용 UX |
| P10/C7 | DEFERRED | legacy sharing JSON envelope의 실제 지원 상세; raw timetable JSON과 구분 |
| A4 | DEFERRED | countdown formatting(초/분, 반올림/버림, 1분 미만/00분/transition 표현), font/layout 구현, Upcoming optional 보조 강조 |
| A5 | DEFERRED | 공식 endpoint 재확인, NTP client, timeout/retry/resync, drift/correction/slew, offline cache, monotonic 구현, test injection, suspend/resume 처리 |
| A5 | DEFERRED | Settings/tooltip/status detail 중 sync 상세 표시 위치 |

## Bootstrap Readiness

| Gate | 현재 상태 |
| --- | --- |
| P1–P10 미승인 blocker | 0 — 모두 APPROVED |
| Golden Reference remaining MUST | 0 — COMPLETE AS GOLDEN REFERENCE |
| Product-level approval blocker | 0 — A1–A5 및 연결된 계약 확정 |
| 남은 결정 | DEFERRED implementation decisions; 해당 기능 구현 전 ADR/spike/UX 검토 |

**새 .NET repository bootstrap을 시작할 수 있는 제품 계약 baseline이 확보됐다.**
이번 작업에서는 repo/project를 생성하지 않는다. 이 판정은 release-ready나 모든 구현 상세 확정을 뜻하지 않는다.
QR compatibility 또는 legacy bug 수리를 새 blocker로 추가하지 않는다.
문서는 아직 미커밋이다. 최종 문서 review 후 bootstrap 전에 planning milestone commit을 하는 순서를 따른다.
이번에는 commit/push/PR을 하지 않는다.

다음 작업 딱 하나: **승인 반영된 Product Contract와 ADR 0001–0004의 최종 문서 review.**

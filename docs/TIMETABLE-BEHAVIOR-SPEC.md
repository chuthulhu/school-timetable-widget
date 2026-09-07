# Timetable Behavior Specification

## Scope and evidence

M1 **COMPLETE / CHARACTERIZED**: 시간표 내용 편집·교시 경계의 Golden Reference.
이는 legacy 결함 수정이나 전체 recovery 종료를 의미하지 않는다. 남은 범위는
[Recovery Completion Audit](RECOVERY-COMPLETION-AUDIT.md)의 M2–M4다.

- Reference branch: `recovery-v1-release`.
- Production reference HEAD: `bb30e3c9983c9faf8acf7a76e03dc79662e6818b`.
- Characterization 및 native 검증: 2026-09-07. 문서/contract 추가도 같은 production HEAD 위에서 수행.
- Windows, Python 3.12.14, PyQt5 5.15.11, Qt 5.15.2.
  실행 Python: `C:\CodexVenvs\school-timetable-widget-py312\Scripts\python.exe`.
- **A (VERIFIED / automated):** [test_timetable_behavior_contracts.py](../src/utils/test_timetable_behavior_contracts.py).
  실제 SettingsManager·Widget·dialogs를 offscreen/TEMP profile로 검사한다.
  현재 시각은 test process 안에서만 주입하고 알림은 stub이다. OS clock은 변경하지 않는다.
- **N (VERIFIED / native):** 사용자가 실제 Windows 창에서 직접 조작하고 확인한 아래 기록.
  실제 production Widget/dialog, native `windows` platform, TEMP launcher로 수행했다.
  IME·제목 표시줄 X·실제 화면 렌더링은 A가 대체하지 않는다.
- **S (SOURCE-CONFIRMED):** 실행 확대 없이 명확한 소스 흐름을 기록한 항목.
- **KNOWN QUIRK:** 관찰된 legacy 특이 동작. .NET 요구사항으로 자동 승격하지 않는다.
- **UNKNOWN:** 관찰로 확정하지 못한 항목. 마지막 절에 종료 blocker 여부를 명시한다.

Native 원본 PNG·JSON·launcher는 로컬 TEMP에만 있고 Git에 포함하지 않았다.
이 문서는 입력·절차·결과의 영구 기록이며 원본 이미지의 영구 보관을 주장하지 않는다.
당시 원본 설정 5개의 SHA-256/mtime 및 source/test/docs 44개 hash 불변을 확인했다.
updater/autostart/실제 알림은 실행하지 않았다. 소스 실행의 비교 기준이며 release EXE와의
byte-for-byte 일치 증거는 아니다. 이번 문서화 작업에서는 native 검증을 반복하지 않았다.

## Data Model

```json
{"월": {"1": "국어\n2층", "2": ""}}
```

월·화·수·목·금 × 문자열 교시 key `"1"`–`"7"`, 정상 값은 문자열이다.
본문 35셀과 헤더 13개로 총 48 QLabel을 사용한다. fresh manager는 `{}`이며
누락 요일/교시는 빈 문자열로 표시한다. editor 저장은 35셀을 모두 기록한다. (A/S)

빈 값은 `""`. trim이 없으며 whitespace-only, 앞뒤 공백, newline, 한글·emoji를 보존한다.
명시적 길이 제한은 없고 2,000자 fixture를 왕복했다. 무제한 크기에서 표시 품질을 보장하지 않는다.
추가 key는 main의 고정 grid에서 무시되지만 editor 재저장 시 제거된다. (A/S)
별도 span metadata는 없다. `src/settings`와 CSV 예시는 fresh runtime 기본값이 아니다. (S)

## Timetable Editing

[TimetableEditDialog](../src/gui/dialogs/timetable_dialog.py)는 ContiguousSelection의 7×5 QTableWidget이다.
plain-text QTextEdit delegate가 setPlainText/toPlainText로 모델과 값을 교환한다.
기본 trigger는 DoubleClicked, EditKeyPressed, AnyKeyPressed이며 F2 진입과 Enter newline을
기존 TEMP Qt 진단에서 확인했다. native에서는 직접 한글·두 줄 입력을 확인했다. (A/N/S)

같은 요일의 연속 범위만 수동 merge할 수 있고 첫 셀 내용을 사용한다. 서로 다른 요일이나
이미 병합된 범위는 warning 경로다. split은 첫 셀만 내용 유지, 나머지는 빈 값으로 만든다. (S)
재오픈 시 연속된 동일한 비어 있지 않은 과목을 자동 merge한다. 실제 저장 손실은 아래 quirk 참조.
main은 merge된 블록이 아니라 독립적인 35셀을 표시한다.

## Save / Cancel / Close

| 동작 | Memory / Widget | Disk | 재오픈·재실행 | Evidence |
| --- | --- | --- | --- | --- |
| 저장 | manager 교체, widget 즉시 갱신 | 즉시 write | 값 유지 | A; N 새 프로세스 포함 |
| 취소 | 기존값 유지 | 불변 | 기존값 | A/N |
| Qt close() | 기존값 유지 | 불변 | 기존값 | A |
| Native 제목 표시줄 X | 기존값 유지 | SHA-256/mtime 불변 | 기존값 | N |

실제 버튼은 **저장 / 취소**이며 별도 Apply는 없다. 저장 후 Accepted로 닫힌다.
위 계약은 정상 파일 write 조건이다. write 실패 시 성공 표시 보장은 아래 Persistence 참조.
manager 재생성 검사는 자동 reload 증거이고 전체 앱 재시작은 N에서 별도로 수행했다.

## Period / Time Model

```json
{"1": {"start": "09:00", "end": "09:50"}}
```

| 교시 | 시작 | 종료 |
| --- | --- | --- |
| 1 | 09:00 | 09:50 |
| 2 | 10:00 | 10:50 |
| 3 | 11:00 | 11:50 |
| 4 | 12:00 | 12:50 |
| 5 | 14:00 | 14:50 |
| 6 | 15:00 | 15:50 |
| 7 | 16:00 | 16:50 |

내부는 int key와 start/end QTime. UI는 두 개의 QTimeEdit/교시, 형식 `HH:mm`이다.
쉬는 시간·점심시간은 별도 필드가 아니라 수업 구간 사이의 공백이다.
저장/취소/close/reload 의미는 시간표와 같고, Widget.show_time_dialog의 Accepted 경로는
새 시간을 즉시 사용해 현재 교시를 재계산한다. 08:30에서 1교시를 08:00–08:50으로 바꾸면
timer를 기다리지 않고 1교시로 바뀐다. (A)

시작>종료·겹침·동일 시각·다음 교시가 더 빠른 설정에 대한 관계 validation은 없다. (TEMP Qt/S)
JSON loader는 `split(':')`/int 변환이므로 `9:00`을 읽는다. `09:00:00`은 parsing 오류다.
UI validator와 loader의 허용 범위는 같지 않다. validator 관찰은 `09:00` Acceptable,
`9:00` Intermediate, 빈 값/`oops`/`24:00`/`09:00:00` Invalid였다. 이는 native typing 판정과 별개다.

## Current Period Boundary Semantics

[SettingsManager.get_current_period](../src/utils/settings_manager.py)의 정확한 비교는
`start_time <= current_time <= end_time`이다. dictionary 순서의 **첫 matching 항목**을 반환한다.
정렬하거나 날짜를 검사하지 않는다. 정상 default의 아래 결과를 7교시 전체 parameterization으로 고정했다. (A)

| Case | 1교시 입력 | 4교시 입력 | 7교시 입력 | 반환값 | 평일 강조 |
| --- | --- | --- | --- | --- | --- |
| 시작 −1초 | 08:59:59 | 11:59:59 | 15:59:59 | None | 없음 |
| 정확한 시작 | 09:00:00 | 12:00:00 | 16:00:00 | 해당 교시 | 해당 요일·교시 1셀 |
| 시작 +1초 | 09:00:01 | 12:00:01 | 16:00:01 | 해당 교시 | 동일 |
| 종료 −1초 | 09:49:59 | 12:49:59 | 16:49:59 | 해당 교시 | 동일 |
| 정확한 종료 | 09:50:00 | 12:50:00 | 16:50:00 | 해당 교시 | 동일 |
| 종료 +1초 | 09:50:01 | 12:50:01 | 16:50:01 | None | 없음 |
| 종료 +1ms | 09:50:00.001 | 12:50:00.001 | 16:50:00.001 | None | 없음 |

종료 분 전체를 포함하지 않는다. 기존 42개 초 경계에 이번 contract의 +1ms 7개를 더했다.
겹치거나 동일한 구간은 먼저 삽입된 key가 우선한다. 시작>종료는 매칭되지 않으며
자정을 가로지르는 구간으로 해석하지 않는다. start=end는 정확히 그 point만 매칭한다. (A)

## Break / Weekday / Weekend Behavior

첫 교시 이전, 09:55 쉬는 시간, 13:00 점심, 마지막 교시 이후는 None이다.
월~금 09:10은 해당 요일·1교시 강조. 정상 startup 토·일 09:10은 내부 period=1이지만
day index=None이므로 강조가 없다. 빈 과목 여부는 계산에 관여하지 않는다. (A/N)

23:59:59 → 다음 날 00:00은 period=None, day index만 바뀐다. 다음 날 09:00에는 새 요일 강조다. (A)
시스템 로컬 QTime.currentTime와 datetime.now를 각 callback에서 읽는다. 시스템 clock 변경 전용
hook은 없고 다음 callback에서 반영된다. 두 호출의 날짜/시각은 원자적 snapshot이 아니다. (S)

Timer는 생성자 마지막에서 60초로 시작한다. 이후 기본 60초를 종료/다음 시작까지 남은 시간+1초,
예고까지 남은 시간+0.5초와 비교해 줄이며 최소 1초다. 코드의 10분 cap은 정상 경로에서
60초 기본 상한보다 크다. 계산의 exact boundary가 화면의 즉시 전환을 보장하지는 않는다. (S)
쉬는 시간에는 next_period=1로 잡아 이후 교시 시작을 정밀 예약하지 못한다. 정확한 종료 순간
남은 시간이 0이면 60초 재예약도 가능하다. 날짜만 변경 시 stale highlight는 아래 별도 quirk다.

## Highlight Behavior

해당 요일·교시의 한 body cell만 강조한다. 행·열·period/day header 전체가 아니며 빈 셀도 강조한다.
None으로 바뀌면 기존 강조를 제거한다. (A/N)

기본색 `#FFD700`, opacity `150/255`, 테두리 1px→2px, bold.
글자색·font family·size는 본문 설정과 같다. [styling.py](../src/utils/styling.py)와
[Widget.update_styles](../src/gui/widget.py)의 QSS를 적용한다. (A/S)


**VERIFIED legacy visual/layout interaction (A):** 현재 교시 강조의 테두리 1→2px는
위아래 각각 1px을 추가해 해당 셀의 HFW를 2px 늘릴 수 있다. 동일 content와
125% equivalent pixel font/layout에서 셀·grid·root required height가 각각 +2px이며,
강조 해제 시 복귀함을 전용 contract로 확인한다. 따라서 acceptable layout height는
강조 여부에 의존할 수 있다. 고정 widget minimumSize 자체가 항상 +2라는 뜻은 아니다.
M1 test pollution이나 DPI recovery failure가 아니라 legacy 시각 효과와 layout의 상호작용이다.
기존 DPI geometry contract는 월요일 08:10을 주입하여 강조 없는 scaling/복귀를 검증한다.
.NET 분류는 **LEGACY QUIRK / REDESIGN**: layout을 바꾸지 않는 강조를 고려하며,
inset border·overlay·background 등 구체적 구현 방식은 아직 확정하지 않는다.

## Persistence

`timetable_data.json` 및 `time_settings.json`: UTF-8, ensure_ascii=False, indent=2.
동기 직접 write이고 debounce/atomic replace가 없다. widget_settings의 250ms atomic 계약과 다르다.
SCHOOL_TIMETABLE_DATA_DIR는 **이미 존재하는** 디렉터리를 import/manager 생성 전에 지정한다. (S)

저장 오류는 logger로 기록하고 삼킨다. memory rollback·사용자 오류 안내를 보장하지 않으며
dialog는 Accepted로 닫힐 수 있다. 이 실패 UX는 S로 기록하고 permission matrix를 새로 만들지 않는다.
관련 소스: [load/save/update_timetable_data](../src/utils/settings_manager.py),
[TimeRangeDialog.save_time_ranges](../src/gui/dialogs/time_dialog.py).

## Native Rendering

650×540 native 창에서 `물리학\n실험 A반!`의 한글·두 줄 표시와 저장·재실행을 확인했다.
`과학 탐구 프로젝트 발표 및 토론 수업!`은 세 줄 자동 wrap, 명백한 clipping 없음. (N)
다른 크기·font·DPI에서 같은 표시 품질을 일반화하지 않는다.

JSON/editor의 `<b>과목</b>`는 main QLabel의 AutoText로 **굵은 과목**이 된다.
태그는 화면에서 숨겨진다. 사용자의 실제 화면 관찰과 native QWidget 캡처가 일치했다. (N/S)
.NET은 plain text rendering을 채택한다. 데이터 문자열은 변형 없이 읽어야 한다.

## Invalid / Malformed Data

| 입력 | Legacy 결과 | Evidence / .NET disposition |
| --- | --- | --- |
| timetable 없음 / `{}` | fresh 빈 dict, 표시 가능; 초기 파일 생성 없음 | A / COMPATIBLE |
| timetable malformed JSON | 로그 후 `{}`, 표시 가능 | A / REDESIGN 오류 안내 |
| 요일/교시 key 누락 | 누락 셀 빈 문자열 | A / COMPATIBLE |
| timetable `[]` 또는 `{"월":null}` | 로드는 통과, 표시 시 AttributeError | A / REDESIGN |
| 숫자 cell | 표시 시 TypeError | A / REDESIGN |
| time 없음 / `{}` / malformed | fresh 기본 시간 유지 | A / COMPATIBLE 또는 오류 안내 REDESIGN |
| time 일부 교시 누락 | 기존 default 유지 | A/S / COMPATIBLE |
| time end 누락 | 오류 지점에서 loop 중단, 이후 항목 적용 안 함 | A / REDESIGN |
| 일부 정상 적용 후 오류 | 이미 적용한 값 rollback 없음 | A / REDESIGN |
| start `25:00`, end `09:50` | invalid QTime 저장; 00:00·08:00도 1교시 매칭 | A / REDESIGN |

fresh 결과와 기존 manager 재로드를 구분한다. 없는 파일은 기존 memory를 지우지 않으며,
time 로드 오류도 새로 default를 재생성하는 것이 아니라 당시 값들을 유지한다. (S)
잘못된 schema로 표시 함수가 예외를 낸다는 증거이지, 모든 startup 오류 화면을 검증한 것은 아니다.

## Known Legacy Quirks

모두 **observed legacy behavior**, **.NET must reproduce가 아님**. 정상 데이터 문자열 호환은 유지한다.

| ID | 최소 재현 / 결과 | Evidence | .NET disposition |
| --- | --- | --- | --- |
| L1 | `A,A,B` open/save → `A,A,A` | A | REDESIGN 무손실 편집 |
| L2 | 1~2교시 수동 merge → 3교시까지 첫 값 overwrite | A | REDESIGN 범위 보존 |
| L3 | 6~7 동일 → span 3; 1~7 동일 → span 8 | A | REDESIGN 정확한 범위 |
| L4 | L3 자동 span split → AttributeError | A | REDESIGN 안전한 분할 |
| L5 | `A,A,"",B,B,"",""`에서 두 번째 블록 자동 merge 누락 | A | REDESIGN 명시적 병합 UX |
| L6 | 금요일 09:10→토요일 09:10, period 같으면 금요일 강조 잔존 | A | REDESIGN 날짜 포함 상태 갱신 |
| L7 | 09:55에 예고 callback 없음; 쉬는 시간 next_period=1 예약 | A/S; 실제 toast 미실행 | REDESIGN scheduler/notification |
| L8 | invalid QTime 매칭, 부분 로드, wrong-schema 표시 예외 | A | REDESIGN validation |
| L9 | 직접 write 실패 로그만 남기고 memory 변경/Accepted 가능 | S | REDESIGN 안전한 저장·실패 UX |
| L10 | editor plain text ↔ main AutoText/HTML | N/S | REDESIGN plain text rendering |

Tests의 legacy 이름과 주석은 이 구분을 유지한다. 후속 수정이 승인되면 새로운 사양과 테스트를
함께 변경할 수 있으며, 이 문서의 과거 참조 결과는 보존한다.

## .NET Compatibility Contract

| Behavior | Classification | .NET requirement | Evidence |
| --- | --- | --- | --- |
| 월~금 × 7교시 | MATCH | 같은 사용자 모델·35셀 | A/N/S |
| 문자열·공백·multiline·Unicode | MATCH | 내용 그대로 보존 | A/N |
| Save 즉시 반영, Cancel/X discard | MATCH | 정상 저장·취소 의미 유지 | A/N |
| 기본 period profile | MATCH | 위 표의 7개 구간 | A |
| 정상 current-period inclusive | MATCH | 시작/종료 point 포함, 종료 +1ms 제외 | A |
| 평일 1셀·빈 셀 강조 | MATCH | 해당 셀만 강조 | A/N |
| 정상 weekend | MATCH | 강조 없음 | A/N |
| legacy JSON key/value | COMPATIBLE | 기존 형식 읽기, 새 내부 schema 가능 | A/S |
| 반복 과목 | COMPATIBLE | 문자열 보존, destructive merge는 재현 금지 | A |
| merge/span L1–L5 | REDESIGN | 손실·과대 span·분할 예외 제거 | A |
| invalid/reversed/overlap·malformed | REDESIGN | 관계/형식 validation, 오류 안내 | A/S |
| stale date highlight | REDESIGN | 날짜 변화도 재평가 | A |
| scheduler/notification | REDESIGN | 입력 시각과 갱신·예고 정책 명시 | A/S |
| direct write/save failure | REDESIGN | 안전한 저장과 실패 UX | S |
| QLabel AutoText | REDESIGN | plain text 표시 | N/S |

## Native-only evidence

| Case | 실제 절차 및 결과 |
| --- | --- |
| IME | 직접 한글 `물리학`, Enter, `실험 A반!`; Save→main/file→reopen→종료/새 프로세스 모두 유지 |
| Cancel | 화요일 2교시 수정→취소→main/file/reopen 빈칸 유지 |
| Title-bar X | 수요일 3교시 `X 취소 검증`→실제 X→file SHA-256/mtime 불변→reopen 빈칸 |
| X 재시도 기록 | 첫 시도 중 사용자 실수 Save 및 복구 Save는 앱 결함으로 취급하지 않고 제외; 이후 위 X 검증을 별도 수행 |
| QTimeEdit `9:00` | 초기 09:00에서 입력 시도→표시 09:00→Save JSON 09:00 |
| QTimeEdit empty | Ctrl+A/Backspace 시도에도 09:00 유지→Save JSON 09:00 |
| QTimeEdit `oops` | 문자 입력되지 않음→종료 09:50을 마우스로 클릭→시작 09:00 유지→Save JSON 09:00 |
| Tab 정정 | 연속 입력 중 Tab은 분 section으로 이동. 앞선 대화창 왕복의 Tab 관찰은 다른 field 이동 증거로 사용하지 않음 |
| Render | 위 Native Rendering 절의 입력/650×540 결과 및 평일·빈 셀·새 프로세스 주말 강조 확인 |

Native 검증 당시 Tool/owned 창이 제어 도구 목록에서 누락되어 사용자 조작과 TEMP 로그/캡처를 결합했다.
자동 테스트 성공을 native IME·X·typing 성공으로 대체 보고하지 않는다.

## Known unknowns

- `9:00`이 자동 보정된 것인지, 초기 09:00이 유지된 것인지 구분 불가.
- `24:00`, `09:00:00`의 실제 native keyboard path 미검증.
- 이 대표 창 크기 밖의 모든 rendering 및 IME/OS 조합은 보장하지 않음.

위 항목은 **M1 종료 blocker가 아니다**. 정상 저장 결과·지원 형식·native 대표 경로와
.NET validation/표시 redesign 방침을 확정하는 데 충분하다. 나머지 M2–M4를 완료했다는 뜻도 아니다.

## Automated verification run

전용 모듈은 `src/utils/test_*.py` discovery 관례를 따른다. 기존 giant recovery test는 늘리지 않는다.
실행 시 `QT_QPA_PLATFORM=offscreen`, `PYTHONPATH=<repo>/src`, `PYTHONDONTWRITEBYTECODE=1`,
`SCHOOL_TIMETABLE_DATA_DIR=<existing unique TEMP>`를 설정한다. native 창·실제 입력은 사용하지 않는다.

순서: 새 모듈 → 기존 두 모듈 → root 전체 pytest. `-p no:cacheprovider`와 TEMP `--basetemp` 사용.
검증 결과는 [상태 문서](LEGACY-RECOVERY-STATUS.md)의 M1 validation 기록을 따른다.

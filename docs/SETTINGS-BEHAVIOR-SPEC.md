# Settings Behavior Specification

## Scope and Evidence

M2 **COMPLETE / CHARACTERIZED**: Settings / Appearance의 Golden Reference.
결함을 수정하거나 전체 recovery를 종료했다는 뜻이 아니다. 남은 MUST는
[감사 문서](RECOVERY-COMPLETION-AUDIT.md)의 M3 Data lifecycle / M4 Windows reference runbook이다.

- Reference branch: `recovery-v1-release`.
- Reference HEAD: `da21ece624985dfa2b60be9cfc0c2043c440e242`.
- Characterization/native: 2026-09-07, Windows / Python 3.12.14 / PyQt5 5.15.11 / Qt 5.15.2.
- **A — VERIFIED automated:** [전용 M2 contracts](../src/utils/test_settings_behavior_contracts.py).
  실제 Qt controls/Widget/managers, per-test TEMP JSON, offscreen, 월요일 08:10 process-local clock.
  OS 자동 시작과 알림 전달은 stub이다. QApplication font/style은 변경하지 않는다.
- **T — VERIFIED TEMP:** 앞서 실행한 격리 Qt 객체/이벤트 characterization. 영구 A와 구분한다.
- **N — VERIFIED native:** 사용자가 실제 Windows 창을 조작하고 시각 결과를 확인했으며,
  TEMP observer의 control/memory/JSON/geometry 기록과 대조했다. 자동 native 입력을 주장하지 않는다.
- **S — SOURCE-CONFIRMED:** 아래 연결된 production source의 흐름.

Native는 production Tool/Frameless/Bottom flags와 dialog ownership을 유지했다.
전체 main/updater 실행 대신 TEMP launcher를 사용했고 autostart/notification OS 효과는 차단했다.
원본 설정 5개의 SHA256/mtime 및 저장소 source/docs 33개 hash 불변, 소유 진단 프로세스 정상 종료를 확인했다.
원본 PNG/JSON 로그는 로컬 TEMP에 있었으며 Git에 영구 보관된 증거라고 주장하지 않는다.
이번 문서화에서는 native 검증을 반복하지 않았다. Release EXE와 byte-for-byte 일치 증거가 아니다.

Offscreen font database의 대체 글꼴은 native 맑은 고딕과 metrics가 다르다.
없는 글꼴의 combo fallback은 초기화 signal에도 영향을 주므로 A는 실제 사용 가능한 family를
명시적으로 seed한다. Windows의 792/1065px를 offscreen 절대 기대값으로 쓰지 않는다.

## Settings Inventory

[SettingsDialog](../src/gui/dialogs/settings_dialog.py)의 6탭: 테마, 색상, 폰트, 알림, 크기/위치, 일반.

| Setting | Control | Live preview | Persistence trigger | Widget effect | Evidence |
| --- | --- | --- | --- | --- | --- |
| Theme preset | light/dark preview tile | 있음 | 선택 즉시 style 전체 | 색상·opacity preset | A/T/N/S |
| Colors 6종 | header bg/text, cell bg/text, current period, border ColorButton | 있음 | Apply/OK; theme 예외 | QSS | A 대표/T 전체/S |
| Font family | header/cell QFontComboBox | 있음 | Apply/OK | 개별 글꼴 | T/S |
| Font size | header/cell QSpinBox 6–24 | 있음 | Apply/OK | 개별 pt | A/T/N/S |
| Opacity 4종 | header/cell/current period/border slider 0–100 | 있음 | Apply/OK | RGBA | A/T/S |
| Widget width/height | spin 200–800 / 150–600 | 설정창 0.3배 preview만 | Apply/OK, widget 지연 저장 | 허용된 실제 크기 | A/T/N/S |
| Position reset | 확인 메시지 버튼 | memory target만 | Apply/OK | 즉시 move 없음 | A/T/S |
| Notification | 시작/예고 checkbox, 1–10분 spin | 없음 | Apply/OK, notification JSON | 옵션 반영; 전달 미검증 | T/S |
| Lock | 위치 고정 checkbox | 없음 | Apply/OK, widget JSON | 이동 잠금 옵션 | T/S; native M4 |
| Autostart | Windows 부팅 checkbox | 없음 | Apply/OK, widget JSON와 OS helper | 시작 옵션 | T/S; 실제 OS M4 |

Custom tile에는 light/dark와 같은 클릭 handler가 없다. 수동 style 변경의 custom 전환은 pass이며,
Cancel은 ThemeSelector의 선택 표시까지 완전히 동기화하지 않는다. (S/T)
전체 factory reset, always-on-top toggle, border 두께/radius 설정은 없다.

## Legacy State Model

| State | 의미 | 대표 불일치 |
| --- | --- | --- |
| A Control | 현재 spin/slider/combo 값 | actual size와 다를 수 있음 |
| B Memory | SettingsManager/NotificationManager | Preview가 수정 |
| C Visual | Widget QSS/실제 geometry | appearance와 크기 확정 시점이 다름 |
| D Persisted | style/widget/notification JSON | Cancel로 복원하지 않음 |
| E Rollback baseline | dialog-open 시 initial_settings | Apply 후에도 최초 값 |

완전한 transaction이 아니다. E에는 style 색상/opacity/개별 font/theme가 들어가지만
geometry, notification, lock, autostart는 없다. legacy font aliases도 별도 완전 snapshot이 아니다. (S)

## Preview Semantics

일반 color/font/font-size/opacity 변경은 A→B→C로 전달하며 style JSON은 저장하지 않는다:
**PREVIEW != PERSIST**. 실제 ColorButton 결과 경로와 font-size control로 A에서 보호한다.
모든 style controls를 함께 읽으므로 변경하지 않은 opacity도 정수 변환을 거칠 수 있다.
size controls는 주 위젯의 live resize가 아니라 설정창 내부 preview만 바꾼다. (A/T/S)

## Apply Semantics

Apply는 현재 memory style 저장, notification 옵션 저장, widget 설정 저장/크기 적용,
autostart helper 호출 및 style 갱신을 수행하고 dialog를 유지한다. OK는 Apply 후 Accepted로 닫는다.
**E를 갱신하지 않는다.** 정상 저장 조건의 계약이며 write 실패 UX는 별도다. (A/T/S)

Style JSON은 직접 동기 write이며 Apply 시작/끝에서 저장한다. Notification setters도 각각
저장하며 마지막 explicit save가 있다. Widget JSON만 250ms debounce/atomic replace 경로다.
따라서 즉시 snapshot과 timer settle 후 snapshot을 구분한다. 모든 파일을 하나의 atomic
transaction으로 저장한다는 뜻은 아니다. (T/S)

## Cancel / Reject Semantics

최초 E의 style로 B를 복원하고 controls 갱신·style signal 후 Rejected로 닫는다.
그러나 control 갱신 signal이 재진입하므로 전체 rollback은 비원자적이다.
Native font 10→24 Preview→Cancel은 visual/control/memory 10, style file hash/mtime 불변이었다.
A의 font case는 같은 복원 의미와 semantic JSON 불변을 검사한다. (A/T/N/S)

## Native Title-Bar Close

실제 Windows X는 관찰한 font Preview 경로에서 Cancel과 같은 reject semantics였다.
A의 close()/reject()는 Qt 경로 증거이며 native title-bar click, IME 또는 OS focus 증거가 아니다.
모든 설정이 완벽하게 rollback된다고 일반화하지 않는다. (A/N/S)

## Apply → Preview → Cancel

최초 10pt → 18pt Apply → 24pt Preview → Cancel: **visual/memory 10pt, persisted 18pt**.
추가 Preview 없이 18pt Apply→X도 같은 불일치였다. 창 재오픈은 memory 10pt를 읽는다.
저장된 18pt의 새 프로세스 복원은 별도 Apply→X native 재시작과 A subprocess로 확인했다.
하나의 끊김 없는 native 세션으로 합쳐 서술하지 않는다. **LEGACY QUIRK / .NET REDESIGN**.

## Theme Immediate Persistence

[ThemeSelector](../src/gui/components/theme_selector.py)→
[SettingsManager.change_theme](../src/utils/settings_manager.py)는 preset 적용 후
**Apply 없이 현재 style 전체를 즉시 저장**한다. 이후 controls 갱신 중 signal이 발생할 수 있다.
파일 font18 / memory-control10에서 dark 선택 시 파일 font도 10으로 덮였다.
Cancel은 memory light로 돌아가도 파일 dark/font10을 되돌리지 않는다. 재시작은 dark를 읽었다.
A는 Apply 호출 없는 theme 저장과 whole-style overwrite/Cancel 불변을 보호한다. (A/T/N/S)
**LEGACY QUIRK / .NET REDESIGN**.

## Rollback Signal Re-entry

update_controls_from_settings는 signals를 차단하지 않는다. opacity sliders를 순서대로 갱신할 때
preview callback이 아직 복원되지 않은 다른 controls를 읽어 memory를 다시 쓸 수 있다.
대표 4 slider 50%는 memory [127,127,127,127], Cancel 후 [119,124,124,124]였다.
A는 이 observable 값과 파일 불변을 검사하며 production 계산을 복제하지 않는다.
T의 font+opacity 조합에서는 최신 font가 남는 경우도 있었다. 단일 native font 복원이 성공한
사실과 모순되지 않는다. **LEGACY QUIRK / REDESIGN**. (A/T/S)

## Opacity / Color Conversion

UI percent→byte는 `int(percent * 255 / 100)`, 역방향은 `int(byte * 100 / 255)`이다.
예: 50%→127, 재표시49%→124. 정수 truncation 때문에 round-trip 값 손실이 가능하다.
[ColorButton](../src/gui/components/color_button.py)은 ShowAlphaChannel과 DontUseNativeDialog를
설정하지만 accepted QColor를 HexRgb `#RRGGBB`로 변환한다. RGBA(18,52,86,50)는 #123456으로
저장되어 alpha를 잃는다. A는 picker accepted 결과를 주입하며 실제 사용자 picker 조작은 아니다.
opacity·alpha 손실은 **LEGACY QUIRK / REDESIGN**. (A/T/S)

## Widget Size / HFW Interaction

기존 [recovery native 기록](LEGACY-RECOVERY-STATUS.md): 550×520 요청은 actual/preferred/persisted
550×520, constrained 550×350은 550×473이었다. 이는 그 fixture/DPI의 역사적 값이다.
M2 A는 작은 요청→settled actual/persisted 일치와 재오픈 control의 actual 표시를 검사한다.
기존 열려 있는 control에는 요청값이 남는다. Qt 지연 timer를 settle한 후 읽는다.

M2 native 저장/control 550×520, font18 재시작 actual/HFW 550×792, control은 550×520이었다.
따라서 persisted geometry intent와 runtime content-constrained geometry는 다를 수 있다.
legacy size 읽기·content minimum 개념은 COMPATIBLE, control/actual 불일치 UX는 REDESIGN.
792/473을 새 cross-platform 자동 계약으로 고정하지 않는다.

## Font Preview / Layout Interaction

Native 24pt Preview: required height 약1065, actual height520 유지, clipping 확인.
18pt 저장 후 재시작은 actual792로 확장되었고 사용자가 글자/세로 확대를 확인했다.
Preview는 appearance와 layout normalization을 항상 함께 수행하지 않는다. (N/S)
A는 realized offscreen layout에서 font Preview 후 required height 증가/actual size 유지 관계만
검사한다. 정확한 픽셀과 native clipping 판단은 N이다. **LEGACY QUIRK / REDESIGN**.

## Position Reset

확인 Yes→memory target(100,100), Widget 즉시 move 없음, 파일 불변.
Cancel도 memory target을 복원하지 않는다. 같은 크기로 재오픈 Apply하면 위치가 저장되지만
Widget은 그 자리다. A는 이 경로를 검사한다. 크기 변경과 동시 적용은 후속 Widget 저장 경로가
실제 위치를 다시 기록할 수 있으므로 위 계약에 포함하지 않는다. (A/T/S)
전체 default reset은 없다. 다중 모니터 좌표/클램프의 native 범위는 M4. REDESIGN.

## Restart Semantics

새 process는 persisted JSON을 authoritative state로 읽는다.
A의 별도 Python subprocess는 Apply18→runtime reject10 후 manager load18을 검사한다.
전체 main/tray startup 자동화는 아니다. Native 새 Widget process에서 theme→Cancel→dark 복원,
Apply18→X10→restart18 복원을 따로 확인했다. (A/T/N)

## Separate Workflow Boundaries

Timetable editor, Time editor, Backup/import는 Widget menu/action의 별도 workflow다.
Settings에 이들을 여는 nested child transaction이 없으므로 Settings Cancel이 그 committed
결과를 취소한다는 계약은 **NOT APPLICABLE / SEPARATE WORKFLOW**. Backup/import는 M3. (S)

## Known Legacy Quirks

아래는 legacy characterization이며 .NET MUST reproduce가 아니다.

| Quirk | Evidence | Disposition |
| --- | --- | --- |
| Apply가 최초 rollback baseline 유지, Cancel/X memory/file 불일치 | A/T/N | REDESIGN |
| Theme 즉시 whole-style save 및 Cancel 후 파일 유지 | A/T/N | REDESIGN |
| Control signal 재진입, opacity precision loss | A/T; native 일부 값 관찰 | REDESIGN |
| Picker alpha 손실 | A/T/S | REDESIGN |
| Font Preview clipping, restart 크기와 control 불일치 | A 관계/N 수치 | REDESIGN |
| Reset target의 불완전 rollback/즉시 move 없음 | A/T/S | REDESIGN |
| Custom tile/선택 표시의 불완전 동기화 | T/S | REDESIGN |

## .NET Compatibility Contract

| Behavior | Classification | .NET requirement | Evidence |
| --- | --- | --- | --- |
| Appearance live preview | MATCH | 미리보기 UX 제공 | A/T/N |
| Apply 후 dialog 유지 | MATCH | 계속 편집 가능 | A/N |
| 정상 persisted appearance restart 복원 | MATCH | 저장한 상태 복원 | A/N |
| 지원 style field 의미 | MATCH | header/body/colors/highlight 구분 | A/T/S |
| Legacy JSON field/value 읽기 | COMPATIBLE | 구/개별 font key와 theme 입력 호환 | S |
| RGB/opacity migration | COMPATIBLE | 기존 RGB와 0–255 의미 읽기 | A/S |
| Persisted size intent/content minimum | COMPATIBLE | 입력 의도와 가독성 하한 수용 | A/N/S |
| Stale baseline, Cancel/X visual/file mismatch | REDESIGN | 명확한 Apply/취소 기준 | A/N |
| Theme immediate whole-style save | REDESIGN | 일관된 저장 경계 | A/N |
| Signal re-entry, opacity precision loss | REDESIGN | 원자적 복원·값 보존 | A/T |
| Alpha loss | REDESIGN | alpha 지원 여부와 저장 표현 일치 | A/S |
| Preview clipping | REDESIGN | preview 중 표시/크기 정책 명시 | A 관계/N |
| Size controls vs actual mismatch | REDESIGN | 사용자 크기 표시 일관성 | A/N |
| Position reset rollback | REDESIGN | 위치 적용·취소 경계 명시 | A/T |

## Native-only Evidence

| Input / procedure | Observed result |
| --- | --- |
| light, 맑은 고딕 header11/body10, 550×520 baseline | opacity bytes120/30/150/200, controls47/11/58/78 |
| font24 Preview→Cancel | visual10, style SHA256/mtime 불변 |
| font24 Preview→실제 title-bar X | visual10, style 파일 불변 |
| font18 Apply→font24 Preview→Cancel | visual10 / file18 |
| file18, memory10→dark 선택→Cancel | file dark/font10, visual light/font10 |
| 정상 종료→새 process | dark/font10 복원 |
| font18 Apply→추가 Preview 없이 X | visual10 / file18 |
| 정상 종료→새 process | font18, actual550×792 / control550×520; 사용자 확대 확인 |
| font24 Preview render | required 약1065 / actual520, clipping |

사용자 이동에 의한 widget position 저장은 Cancel의 저장 부작용으로 취급하지 않았다.
Tool/owned 창의 제어 도구 discovery 제한으로 사용자 조작과 read-only TEMP observer를 결합했다.
창 flags를 바꾸거나 가짜 대상 handle을 사용하지 않았다.

## Known Unknowns / Out of Scope

M2 대표 appearance semantics의 종료 blocker는 없다. 실제 autostart·notification delivery,
IME/Tab/focus/모든 DPI-font 조합·다중 모니터 위치·전체 main lifecycle은 완료 주장하지 않는다(M4).
Backup/import 및 malformed 전체 lifecycle은 M3. 저장 실패 UX는 정상 저장 contracts와 별개다.
이 문서와 테스트는 legacy reference를 고정하며 새로운 .NET 사양 구현은 아니다.

## Automated Verification

전용 module은 14 cases: Preview font/color, Cancel/Qt close, Apply→reject와 추가 Preview→reject,
OK, theme whole-style save, opacity rollback, alpha, constrained size 재오픈, subprocess load,
position reset, font/HFW 관계. Native X를 자동화한 case는 없다.
실행 결과와 full suite 기록은 [상태 문서](LEGACY-RECOVERY-STATUS.md)의 M2 절을 따른다.

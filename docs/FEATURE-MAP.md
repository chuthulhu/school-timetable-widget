# Feature Map

초기 기준: `recovery-v1-release` / `7a27e4192a0b6d13a9d18a193b1770b6abb58c2c`.
M2 기준 HEAD: `da21ece624985dfa2b60be9cfc0c2043c440e242` (production 무변경).
M1 후속 기준 production HEAD: `bb30e3c9983c9faf8acf7a76e03dc79662e6818b` (production 무변경).
이 문서는 [상태](LEGACY-RECOVERY-STATUS.md)나 [감사 판정](RECOVERY-COMPLETION-AUDIT.md)을 반복하는 대신,
기능의 호출 지점·데이터 소유권·이식 단위를 연결한다. .NET target은 **RECOMMENDED 방향**이며 확정 아키텍처가 아니다.
M1은 [시간표 명세](TIMETABLE-BEHAVIOR-SPEC.md), M2는 [설정 명세](SETTINGS-BEHAVIOR-SPEC.md), M3는 [데이터 수명주기 명세](DATA-LIFECYCLE-SPEC.md)와 전용 contracts로 COMPLETE / CHARACTERIZED다. M4도 [Windows Reference Runbook](WINDOWS-REFERENCE-RUNBOOK.md)의 source/Qt/native 범위에서 COMPLETE / CHARACTERIZED다. **남은 MUST 0, COMPLETE AS GOLDEN REFERENCE**. M4 시작 HEAD는 `07eaa43de6f55a0d4ba21fb74482dbf539b3636d`이며 문서만 미커밋 상태로 추가한다. 아래 파일 링크와 함수명은 기준 소스에서 확인했다.

## Feature to source / data mapping

| Feature | Legacy source / entry | Settings/data | Verification | .NET target module |
| --- | --- | --- | --- | --- |
| 시간표 표시 | [Widget.init_ui / update_timetable_display](../src/gui/widget.py) | timetable_data, 월–금 / 문자열 1–7, 여러 줄 text | V, M1 COMPLETE: 내용·native render | Features/Timetable |
| 교시 계산·강조 | [SettingsManager.get_current_period](../src/utils/settings_manager.py), Widget.update_current_period / set_next_update_timer | time_ranges, 현재 요일·QTime | V, M1 COMPLETE: inclusive·첫 일치·stale-date quirk | Features/Timetable |
| 편집·병합·분할 | [TimetableEditDialog](../src/gui/dialogs/timetable_dialog.py)의 merge_selected_cells / split_selected_cell / save_timetable | 같은 timetable JSON, 별도 span field 없음 | M1 CHARACTERIZED: 손실·마지막 span/분할 예외, REDESIGN | Features/Timetable |
| 교시 시각 편집 | [TimeRangeDialog.save_time_ranges](../src/gui/dialogs/time_dialog.py) | time_settings.json | M1 COMPLETE; backup/import M3 COMPLETE | Features/Settings |
| Font·colors·theme·opacity | [SettingsDialog](../src/gui/dialogs/settings_dialog.py), [ThemeSelector](../src/gui/components/theme_selector.py), [ColorButton](../src/gui/components/color_button.py), [styling](../src/utils/styling.py) | style_settings.json, Config.THEMES / DEFAULT_STYLES | M2 COMPLETE / CHARACTERIZED; Preview/Apply/Cancel/theme quirks는 설정 명세 참조 | Features/Settings |
| Explicit size | SettingsDialog.apply_settings → [Widget.apply_user_requested_size](../src/gui/widget.py) | widget_settings.size, runtime design preferred | V: HFW actual, hide/show, DPI; M2 constrained 재오픈/control 불일치 기록 | Features/Settings |
| Window geometry·drag·lock | Widget DragResizeMixin / apply_saved_position / save_widget_position | position, size, is_position_locked, screen_info | 저장/DPI V, M4 native resize/위치 복원; lock/겹침 전체는 source/document-only | Platform/Windows/Windowing |
| DPI·minimum·HFW | Widget.apply_minimum_cell_sizes / _apply_deferred_dpi_correction, styling.calculate_minimum_cell_size | runtime 96-DPI QSizeF, 현재 screen logical DPI | 자동+Windows V | Platform/Windows/Windowing |
| Tray·visibility·종료 | [TrayIcon](../src/tray_icon.py), [ApplicationManager.safe_exit](../src/main.py), Widget.closeEvent | visible state는 JSON에 저장 안 함 | M4 native menu/toggle/show/exit V; Settings는 Widget 메뉴 | Platform/Windows/Tray |
| Autostart | [auto_start](../src/utils/auto_start.py), ApplicationManager._sync_auto_start_setting | widget_settings.auto_start_enabled + Startup .lnk | JSON V; M4 source-confirmed semantics, read-only .lnk 부재; 실제 mutation/재로그인 document-only | Platform/Windows/Startup |
| 시작·정리 | ApplicationManager.run / cleanup_resources | data/log directory, singleton managers | M4 isolated full main/native tray exit0/restart; 외부3경계 차단, unmodified main/frozen 아님 | App / Platform/Windows/Lifecycle |
| Single instance | 현재 entry에는 guard 없음 | 공유 data directory만 있음 | M4 source-confirmed 부재, native A/B 생략; killer와 구분 | Platform/Windows/SingleInstance, 신설 여부 결정 |
| 교시 알림·예고 | [NotificationManager](../src/notifications/notification_manager.py) 및 Widget.update_current_period | notification_settings.json, in-memory last_notified_* | M1 예고 callback + M4 load/toggle/backend 경계 기록; 실제 delivery document-only | Features/Notifications / Platform/Windows/Notifications |
| JSON 위치·로드·저장 | [paths](../src/utils/paths.py), [SettingsManager](../src/utils/settings_manager.py) | 아래 5파일, appdirs, 환경변수 | widget V; timetable/time M1 완료; 전체 lifecycle M3 COMPLETE | Infrastructure/Persistence |
| Backup·restore·delete | [BackupRestoreDialog](../src/gui/dialogs/backup_dialog.py), SettingsManager.create_backup / restore_backup | backups/name/5파일 + description.txt | M3 COMPLETE: full 왕복/partial/failure/runtime-restart 경계 | Infrastructure/Persistence |
| QR 공유·PNG | [QRShareDialog.generate_qr_code](../src/gui/dialogs/qr_share_dialog.py) | 아래 공유 envelope, Base64 JSON | payload M3 COMPLETE, 실제 QR image 생성/scan 미검증 | Features/Sharing |
| QR camera/image·JSON import | [ImportDialog](../src/gui/dialogs/import_dialog.py) | 선택 timetable 전체 교체/time 입력 교시 merge | payload M3 COMPLETE, camera 환경 수리 제외 | Features/Sharing |
| Update/version | [Updater / main](../src/main.py), [version.py](../src/utils/version.py) | latest tag, 첫 .exe, TEMP download | 숫자 비교 V, 나머지 문서화 | Infrastructure/Update, 새 설계 |
| Packaging | [TimetableWidget.spec](../TimetableWidget.spec), [main.spec](../main.spec) | src/main.py, assets, 고정 version | build 미검증, 공개 release 제외 | .NET build/release pipeline |

## Persistence ownership and compatibility

실제 파일 위치는 `utils.paths`가 결정한다. 이미 존재하는 `SCHOOL_TIMETABLE_DATA_DIR` 환경변수가
우선이며, 없으면 appdirs의 `SchoolTimetableWidget` / `TimeTableDev` 사용자 data directory를 사용한다.
생성 실패 시 TEMP fallback이 있다. `src/settings/*.json`은 추적된 예시이며 자동으로 runtime 기본값으로
로드되는 경로가 아니다. Config의 별도 USER_DATA_DIR 상수와 실제 SettingsManager 경로를 혼동하지 않는다.

| File / owner | 저장 형식 | 기본값·호환성·실패 의미 |
| --- | --- | --- |
| widget_settings.json / SettingsManager | position: x/y, size: width/height, is_position_locked, screen_info: geometry/name 또는 null, auto_start_enabled | 기본 (100,100), (400,300), false, null, false. 실제 창 최소치가 기본 size보다 클 수 있음. size는 저장 당시 Qt geometry이며 source DPI 없음. corrupt JSON은 backup 후 기본값 유지 |
| style_settings.json / SettingsManager | header_bg_color, header_text_color, cell_bg_color, cell_text_color, current_period_color, border_color; header/cell/current_period/border_opacity; font_family/font_size; header_font_*, cell_font_*; theme | Config light 기본. 개별 font가 없으면 구 font 값 fallback. opacity 0–255. corrupt JSON은 backup 후 DataError 발생 |
| time_settings.json / SettingsManager | 문자열 교시 key → start/end HH:mm | 로드 시 int/QTime. 기본 7교시 위에 덮어씀. 일부 key 누락은 해당 기본값 유지. 오류 처리에 전체 transaction/엄격한 schema 검증 없음 |
| timetable_data.json / SettingsManager | 한국어 요일 key → 문자열 교시 key → 문자열 과목 | 초기 빈 dict. main은 없는 셀을 빈 문자열 표시. 줄바꿈은 문자열에 보존. 손상 로드 시 빈 dict. 별도 병합 metadata 없음 |
| notification_settings.json / NotificationManager | notification_enabled, next_period_warning, warning_minutes | 기본 true/true/5. SettingsManager.load_all_settings는 이 manager를 reload하지 않음. M3: restore 직후 runtime B 유지, 새 manager에서 A |

widget 파일만 debounce snapshot + atomic replace를 사용한다. 다른 네 파일은 직접 write이고,
backup은 존재하는 파일만 개별 copy한다. backup 성공이 “모든 파일 존재” 또는 전체 transaction을 뜻하지 않는다.
기본 교시 시각은 Config에서 09:00–09:50, 10:00–10:50, 11:00–11:50, 12:00–12:50,
14:00–14:50, 15:00–15:50, 16:00–16:50이다. 저장 예시의 다른 시각을 fresh default로 취급하지 않는다.

## Sharing envelope

다음은 공유 format 설명용 예시다. 같은 envelope 구조의 production serialize→Base64 decode/import 및 JSON 선택 적용을 M3 contracts로 검증했다. 실제 QR image encoding/recognition은 포함하지 않는다.

```json
{
  "timetable": {"월": {"1": "예시 과목\n예시 교실"}},
  "time_settings": {"1": {"start": "09:00", "end": "09:50"}}
}
```

QR은 이 envelope의 UTF-8 JSON을 Base64로 인코딩한다. JSON import는 envelope를 직접 읽는다.
둘 중 한 key만 공유할 수도 있다. ImportDialog는 사용자가 선택한 timetable을 전체 교체하고,
time_settings는 들어온 교시만 기존 time_ranges에 덮어쓴다. raw timetable_data.json은 envelope와 다르다.
QR 생성에는 qrcode/Pillow, import dialog 모듈에는 numpy, camera에는 OpenCV/pyzbar,
image decode에는 pyzbar/Pillow가 필요하다. 데이터 형식의 이식과 이 라이브러리들의 이식을 분리한다.

## Behavior boundaries for migration

- Runtime design geometry와 persisted current-screen geometry는 다른 값이다. .NET schema에 단위를 명시하되
  legacy 입력에서 없는 source DPI를 사실처럼 추정하지 않는다.
- Main widget은 bottom/tool/frameless, dialog는 top hint다. “항상 위”를 공통 기본값으로 옮기지 않는다.
- Merge는 editor 기능이고 main grid는 독립 셀이다. M1에서 병합 저장 손실과 AutoText를 확인했으며 .NET에서는 REDESIGN한다. .NET의 블록 표시를 추가하려면 별도 설계 결정이 필요하다.
- 스타일 Cancel·테마 즉시 저장·signal/opacity·위치 reset은 [M2 명세](SETTINGS-BEHAVIOR-SPEC.md)의 REDESIGN 분류를 따른다. 알림 예고는 감사 문서 K3을 따른다. 버그도 그대로 이식하라는 뜻이 아니다.
- M3에서 backup restore의 file/manager A, Widget geometry·notification runtime B, restart A를 고정했다. Disk file replace와 runtime partial merge는 다르다. manager pending 보호를 Widget pre-manager pending까지 일반화하지 않는다. 모두 [데이터 수명주기 명세](DATA-LIFECYCLE-SPEC.md)를 따른다.
- Process killer는 단일 실행 기능이 아니며 aggressive 종료 도구를 .NET 사양으로 옮기지 않는다.
- Source 실행법·의존 버전·fresh/copied TEMP 절차·외부 효과 차단은 [M4 runbook](WINDOWS-REFERENCE-RUNBOOK.md)에 고정했다. 다른 물리 PC의 install 성공이나 frozen 동일성을 주장하지 않는다.
- **Golden Reference = behavior reference, NOT implementation template.** reconstructed and characterized reference이며 exact deployed v1.0.1 source recovered 선언이나 current public release candidate가 아니다. 위 target 경로만으로 새 .NET 구조를 구현하지 않는다. MATCH / COMPATIBLE / REDESIGN을 적용한다.

# ADR 0002 — Initial Windows desktop stack

Status: **Accepted**

Date: 2026-09-08

Decision status: **APPROVED — P1, 2026-09-08 사용자 명시적 승인**.
현재 legacy repo의 new product planning artifact다. 제품 stack은 확정했으며 새 project는 생성하지 않았다.

## Context

[Product Contract](../PRODUCT-CONTRACT.md)의 대상은 작은 Windows desktop timetable widget이다.
Borderless/transparent rendering, 위치·resize, tray/lifecycle, DPI/multi-monitor, 한글 편집 및 데이터 안전성이 필요하다.
Python은 [ADR 0001](0001-golden-reference-policy.md)에 따른 behavior reference다.
새 스택 선택과 native 동작 검증은 별개이며 legacy 검증을 WPF 검증으로 재사용하지 않는다.

## Alternatives

| 후보 | 검토 근거 | 이 제품에서 확인할 점 |
| --- | --- | --- |
| WPF on .NET | Windows 전용 XAML UI, data binding/layout/style 기능을 제공하는 성숙한 desktop stack | transparent/borderless, tray interop, DPI/monitor, 현대 Windows adapter 및 배포 조합 |
| WinUI 3 / Windows App SDK | Microsoft가 새 Windows 앱에 권장하는 UI framework/platform | 작은 desktop widget에 필요한 window/tray/배포 통합과 유지보수 비용 |

WPF의 Windows 전용·layout/binding 특성은 [WPF overview](https://learn.microsoft.com/en-us/dotnet/desktop/wpf/overview/)에 근거한다.
Microsoft의 일반적인 신규 앱 권장은 WinUI 3이며 WPF에서도 Windows App SDK API를 사용할 수 있다.
[Windows development path](https://learn.microsoft.com/en-us/windows/apps/get-started/) (2026-09-08 확인).
따라서 WPF를 Microsoft의 모든 신규 앱 기본 권장이라고 서술하지 않는다.

## Decision

**WPF + .NET 10 LTS + CommunityToolkit.Mvvm**을 사용한다. 사용자가 P1을 승인하여 Accepted로 변경했다.
.NET 10은 LTS이며 공식 support policy의 지원 종료일은 2028-11-14다.
Patch version은 이 ADR에서 고정하지 않고 구현 시 지원되는 최신 servicing 상태를 확인한다.
[.NET support policy](https://dotnet.microsoft.com/en-us/platform/support/policy) (2026-09-08 확인).

CommunityToolkit.Mvvm은 UI framework에 종속되지 않는 MVVM 도구이며 WPF/WinUI 모두에서 사용할 수 있다.
Toolkit 자체가 WPF 선택을 강제하지 않는다.
[MVVM Toolkit overview](https://learn.microsoft.com/en-us/dotnet/communitytoolkit/mvvm/) (2026-09-08 확인).

## Reasons

다음은 이 제품에 대한 **설계 판단/검증 전 가설**이며 공식 비교 benchmark가 아니다.
작은 widget의 borderless/positioning, tray/window integration과 DPI/multi-monitor를 다루는 데
성숙한 desktop stack을 이용하고, UI 전반의 Windows App SDK 의존을 상대적으로 낮게 유지하려는 선택이다.
필요한 Windows 기능에 SDK adapter를 추가할 가능성은 열어 둔다.
MVVM의 binding/command와 명확한 기능 경계가 AI-assisted maintenance 및 검토에 도움이 될 것으로 기대한다.
이는 WinUI 3보다 유지보수가 반드시 쉽거나 native 요구가 자동 충족된다는 보장이 아니다.

Candidate architecture는 feature-oriented/MVVM, Windows adapter isolation, persistence boundary다.
거대한 AppState/MainWindowViewModel 및 Shared/Utils에 책임을 모으는 구성을 피하는 방향을 고려한다.
이 candidate의 구체적 구조는 stack 승인으로 확정되지 않는다.
Repo structure, module/type 배치 자체는 DEFERRED다.

## Risks

Transparent/borderless 창은 렌더링·input·resize·focus·z-order를 실제 Windows에서 검증해야 한다.
Tray와 notification은 UI framework 선택만으로 완성되지 않는다. OS/installer 조합별 adapter 검증이 필요하다.
DPI/monitor 이동에서 실제 geometry를 다시 preference로 저장하면 drift가 생길 수 있다.
한글 IME, keyboard/Tab/focus-loss 및 title-bar 동작은 object/event test만으로 입증할 수 없다.
Framework/library servicing과 Windows 지원 범위도 구현/배포 시점에 확인해야 한다.

## Validation needed

아래는 **후속 구현 단계에서 수행할 validation 계획**이다. 이번에는 prototype/package/native 실행을 하지 않았다.

| 검증 | 필요한 결과 |
| --- | --- |
| Transparent/borderless prototype | text/opacity가 의도대로 보이고 move/resize/focus가 일관됨; 실제 native 조건 기록 |
| Tray / instance | show-hide, Exit 완전 종료, 같은 profile에 두 writer가 생기지 않음(P6 APPROVED) |
| DPI / multi-monitor | 왕복 preferred geometry 불변, minimum 준수, 음수 좌표/사라진 monitor 정책 검증 |
| Installer | 사용자 단위 install/uninstall 및 autostart 선택, 관리자 권한 의존 최소화 가능성 확인 |
| Notification adapter | scheduling과 실제 Windows delivery 분리, resume/dedup 및 실패 표시 검증(P5 APPROVED) |

사용자가 다른 앱에서 작업 중이면 source/object/TEMP 검증을 우선한다.
실제 native input이 필요할 때에만 foreground 구간을 조율한다. 숨김/offscreen/수정 flags 결과를 원래 native 증거로 부르지 않는다.
이 문서가 그 foreground 구간을 지금 승인하는 것은 아니다.

## Consequences

P1 승인에 따라 WPF stack을 새 repository bootstrap의 기준으로 사용한다.
제품 수준 미승인 blocker는 0이며, 이번 작업은 승인 반영 문서 수정까지다.
Prototype이 주요 요구를 충족하지 못하면 WPF/WinUI 3 비교를 재검토한다.
새 repo/project 생성은 후속 bootstrap 작업에서 진행한다. 이번에 생성하지 않으며 Python 구조를 복사하지 않는다.
**DEFERRED:** persistence format, installer technology(MSIX/MSI/WiX/Squirrel 등), updater library.
이 ADR은 이들 기술을 선택하지 않는다.

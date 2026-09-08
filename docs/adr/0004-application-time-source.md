# ADR 0004 — Application Time Source and KRISS Synchronization

Status: **Accepted**

Date: 2026-09-08

Decision status: **APPROVED — A5 및 P4, 사용자의 명시적 승인**.
현재 legacy repo의 new product planning artifact다. 새 .NET repository bootstrap 시 복사/링크 정규화한다.
시간원과 제품 동작 원칙을 확정하며 endpoint, library, 구현 type을 선택하거나 동기화를 실행한 것은 아니다.

## Context

[Product Contract](../PRODUCT-CONTRACT.md)의 A4 Status Header는 현재 시각과 학교 시간 상태를 함께 표시한다.
현재 시각, current-period, break, countdown, 수업 종료, weekday/date, notification scheduling이
같은 authoritative clock을 사용해야 표시와 동작이 일치한다.
[Legacy timetable evidence](../TIMETABLE-BEHAVIOR-SPEC.md)는 QTime.currentTime과 datetime.now를
각 callback에서 읽고 날짜·시각의 원자적 snapshot을 보장하지 않았음을 기록한다.
이는 source evidence이며 새 기능마다 직접 PC 시간을 읽는 구조를 유지할 이유가 아니다.

사용자 의도는 KRISS 대한민국 표준시(KST)를 우선 사용하는 것이다.
네트워크가 막혔거나 서버 응답을 받을 수 없어도 앱 시작과 기본 시간표 사용은 가능해야 한다.
범용 system clock/NTP 관리 도구를 만드는 것은 범위 밖이다.

## Decision

하나의 application clock abstraction을 사용한다. ApplicationClock/TimeProvider는 개념적 이름이며
구체적 .NET type, 인터페이스, 모듈 배치, 주입 방법은 DEFERRED다.

1. 앱은 **PC local time으로 즉시 시작**한다. 시간 서버 응답을 기다리지 않는다.
2. Background에서 KRISS 대한민국 표준시 동기화를 시도한다.
3. 성공하면 앱 내부 authoritative clock을 synchronized KST 기준으로 전환한다.
4. 동기화 unavailable 시 PC local time fallback을 사용한다. 시작 시 실패하면 PC 시각을 계속 사용한다.
5. 동기화 실패는 앱 시작이나 기본 시간표 사용을 막지 않는다.
6. **Windows system clock을 수정하지 않는다.** 동기화는 관리자 권한이나 시스템 clock mutation에 의존하지 않는다.

Header의 `HH:mm:ss`, current-period, break, 다음 교시 countdown, 수업 종료, weekday/date,
notification scheduling이 모두 이 공통 source를 사용한다.
기능별 `DateTime.Now` / `DateTimeOffset.Now` 직접 읽기를 금지한다.
PC local time 읽기는 fallback clock 경계에 두며 UI/period/notification이 각자 system clock을 읽지 않는다.
모든 기능은 동일 clock source/revision을 관찰하고, 관련 상태 계산에는 일관된 날짜·시각 snapshot을 쓴다.
Clock revision은 동기화 reference/source의 일관성을 뜻하며 profile의 persisted revision과 구분한다.
이를 원자적으로 전달하는 구체적 구현은 후속 spike에서 정한다.

**APPROVED P4:** 공통 clock 기준으로 `[start,end)` 구간을 사용한다.
09:00–09:50 수업에서 09:00:00과 09:49:59는 1교시, 09:50:00은 쉬는시간 또는 해당 시각에 시작하는 다음 상태다.
Header, 강조, break/countdown, notification scheduling의 경계가 서로 다른 clock/interval을 쓰지 않는다.
주말에는 수업 시각과 겹쳐도 수업 없음 상태이며 current cell 강조를 표시하지 않는다.

동기화 성공 후 매초 서버를 조회하지 않는다. 동기화 reference를 기준으로 앱 내부 시간이 자연스럽게 진행한다.
가능하면 monotonic elapsed-time source로 wall clock 변경/timer jitter 영향을 줄이는 방향이다.
어떤 source를 쓸지와 보정 방식은 DEFERRED이며 단순 tick 횟수 누적 같은 구현을 여기서 정하지 않는다.

메인 Header는 현재 시각과 학교 상태에 집중한다. 시간 기준, 마지막 동기화, fallback/실패 상태는
Settings 또는 tooltip/status detail에서 확인할 수 있게 한다. 정확한 위치는 DEFERRED다.
Countdown의 제품 의미는 종료/다음 시작까지 남은 시간이지만 초/분 정밀도, 반올림/버림,
`1분 미만`/00분/transition 직전 문구는 별도 formatting policy로 결정한다.

## Consequences

기능 사이의 시간 기준을 맞추고, 동기화가 유효할 때 PC clock 오차를 완화할 수 있다.
Offline에서도 PC 시각으로 사용할 수 있으며 앱 내부 시간 처리에 관리자 권한이 필요 없다.
이는 모든 PC 환경에서 시간 정확도나 KRISS 서버 접근성을 보장한다는 뜻은 아니다.

| 위험 | 후속 검증에서 다룰 내용 |
| --- | --- |
| Network/NTP blocked 또는 timeout | 즉시 시작·PC fallback·비차단 오류 상세 확인 |
| PC fallback 자체의 오차 | 현재 시간 기준을 정확히 표시; fallback을 동기화 성공으로 표시하지 않음 |
| Clock correction에 따른 상태 jump | 모든 기능이 같은 source/revision으로 전환하고 current/countdown이 엇갈리지 않음 |
| Suspend/resume 및 drift | 재평가/보정 시점과 clock 진행 검증 |
| Forward/backward correction과 알림 | P5의 중복 방지, 지난 알림 몰아서 보내지 않음 유지 |

승인된 원칙을 구현하기 전에 Time Synchronization spike/test가 필요하다.
주입 가능한 시간/실패/suspend 조건으로 먼저 검증하며, Windows 시스템 시간을 바꾸어 시험하지 않는다.
이 문서는 동기화 성공, network 접근, 성능, native UI 검증 결과를 주장하지 않는다.

## Deferred

- 공식 KRISS endpoint: **실제 구현 시 당시 공식 KRISS 문서로 재확인**. 계획 단계에 임의 hard-code하지 않는다.
- NTP client implementation/library, protocol 세부 및 응답 검증.
- Timeout, retry 횟수/backoff, periodic resync interval, sync unavailable/stale 판정의 상세.
- Drift correction, abrupt correction vs slew, correction 시 source/revision 전환 구현.
- Offline cache 및 이전 sync reference 수명.
- Monotonic elapsed-time source 구현, suspend/resume 처리.
- Test injection mechanism, clock abstraction의 type/모듈/동시성 구현.
- Sync 상세 표시 위치와 countdown formatting.

설치 기술, updater library, persistence format은 이 ADR이 결정하지 않는다.
이번에는 허용된 planning 문서만 변경하며 repo/project 생성, package 설치, production/tests 변경,
commit/push/PR은 하지 않는다.

# ADR 0001 — Golden Reference usage policy

Status: **Accepted**

Date: 2026-09-08

Decision status: **APPROVED — 사용자의 명시적 reference 사용 지침**.
현재 legacy repo의 new product planning artifact이며 새 .NET repo 생성 승인 후 복사/링크 정규화한다.

## Context

`chuthulhu/school-timetable-widget`, `recovery-v1-release`,
`84de32a555633120bd6363a609a19cbc0a15e8ea`에 reconstructed and characterized Golden Reference가 있다.
[Recovery status](../LEGACY-RECOVERY-STATUS.md)와 [completion audit](../RECOVERY-COMPLETION-AUDIT.md)의
판정은 COMPLETE AS GOLDEN REFERENCE, remaining MUST 0이다.
이는 deployed v1.0.1의 exact source 복원이나 public release candidate를 의미하지 않는다.

## Decision

Golden Reference를 사용자-visible behavior, compatibility evidence, legacy quirks의 판단 근거로 사용한다.
구현 template으로 사용하지 않는다. 새 요구는 [Product Contract](../PRODUCT-CONTRACT.md)의
MATCH / COMPATIBLE / REDESIGN 분류와 별도의 승인 상태로 추출한다.

- MATCH: 정상 사용자 의미를 유지한다. Qt API/정확한 pixel/내부 구조 복제 요구가 아니다.
- COMPATIBLE: 기존 입력 의미를 읽어 변환한다. 기존 schema를 새 내부 schema로 고정하지 않는다.
- REDESIGN: 손실·불명확한 저장·lifecycle 등의 quirks를 분리하고 새 계약을 검토한다.

Characterization tests가 있다는 이유로 quirk를 새 expectation으로 채택하지 않는다.
기존 문서와 새 사용자 결정이 다르면 차이·승인 상태를 Product Contract에 명시한다.
셀 병합/QR 제외와 `[start,end)`, Settings transaction은 모두 APPROVED다.
P1–P10은 2026-09-08 사용자 명시적 승인으로 확정됐다. Reference 정책 Accepted에서 자동 전파된 승인이 아니다.

## Consequences

Python source vendor와 architecture copy를 금지한다. compatibility importer 작성은 가능하되 별도 구현 승인 범위다.
Visual/behavior comparison은 계속 사용하며 source/Qt object/native evidence를 구분한다.
Approved differences를 문서화하고 새로운 테스트는 승인된 새 계약에서 도출한다.
과거 recovery 기록을 새 제품 계획과 섞어 다시 쓰지 않는다.
새 repo의 모듈 구조는 legacy Feature Map의 예시만으로 결정하지 않는다.

이번에는 문서만 작성한다. 이 ADR은 repo/project 생성, production 변경, package 설치,
commit/push/PR 권한을 부여하지 않는다.

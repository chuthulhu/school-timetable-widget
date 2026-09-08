# ADR 0003 — Settings transaction

Status: **Accepted**

Date: 2026-09-08

Decision status: **APPROVED — P2, 2026-09-08 사용자 명시적 승인**.
현재 legacy repo의 new product planning artifact다. 기술 스택에 독립적인 제품 상태 전이 계약이다.

## Context

[Settings evidence](../SETTINGS-BEHAVIOR-SPEC.md)는 Apply 후에도 최초 baseline을 쓰는 Cancel/X,
theme의 즉시 whole-style 저장, opacity 손실, 위치 Reset 불완전 rollback을 기록한다.
사용자는 저장한 결과와 미리보기 결과를 구분하고, 취소할 때 마지막 저장으로 돌아갈 수 있어야 한다.
[Data lifecycle evidence](../DATA-LIFECYCLE-SPEC.md)의 partial save/restore도 같은 committed 경계가 필요함을 보여준다.
사용자가 P2를 승인하여 이 상태 전이 계약을 확정했다. Legacy quirk를 수정하거나 새 구현을 검증한 것은 아니다.

## Decision

[Product Contract의 Settings Transaction Contract](../PRODUCT-CONTRACT.md#settings-transaction-contract)를 기준으로 한다.

| State | 의미 |
| --- | --- |
| Committed | 검증과 persistence가 성공한 authoritative revision |
| Draft | dialog가 편집 중인 값; committed와 분리 |
| Preview / owned runtime | Draft의 시각적 적용 및 dialog가 임시 변경한 상태 |
| Rollback baseline | Open의 committed snapshot, 이후 성공 Apply마다 갱신 |

Open은 committed에서 Draft와 baseline을 만든다. Preview는 runtime에만 적용하고 저장하지 않는다.
Theme와 Reset(위치 포함)도 Draft 규칙을 따른다. Apply는 검증과 persistence가 성공한 뒤
committed/baseline을 같은 새 결과로 갱신하고 dialog를 유지한다. OK는 Apply 성공 후에만 닫는다.
Cancel/X는 마지막 성공 Apply baseline으로 controls, preview, owned runtime state를 완전히 복원한다.
취소 자체는 persistence나 OS registration을 발생시키지 않는다.
저장 실패는 Draft/dialog를 유지하고 오류를 표시하며 committed/baseline은 그대로 둔다.

## Review scenarios

아래 기대 결과는 **APPROVED acceptance examples**이며 실행한 테스트 결과가 아니다.

| 시나리오 | 기대 결과 |
| --- | --- |
| 10pt Open → 24pt Preview → Cancel/X | runtime/controls 10pt, persisted 불변 |
| 10pt Open → 18pt Apply 성공 → 24pt Preview → Cancel/X | runtime/controls/persisted 모두 18pt |
| 10pt Open → 18pt Apply 성공 → X | 18pt 유지 |
| Theme 선택 → Cancel/X | 원래 baseline theme, 다른 Preview 값도 저장 안 됨 |
| 위치 Reset → Cancel/X | baseline controls/target/owned runtime position 복원, persisted 불변 |
| Apply 저장 실패 → 편집 지속 → Cancel | 오류와 Draft 유지 후 마지막 성공 baseline으로 복원 |
| OK 저장 실패 | dialog 유지; Accepted/성공처럼 닫지 않음 |
| Opacity를 수정하지 않고 Open/Cancel 반복 | 저장값·baseline을 UI 표시 변환으로 손실시키지 않음 |

## Alternatives

Legacy의 dialog-open baseline을 계속 쓰는 방식은 성공 Apply를 취소한 것처럼 보이게 하므로 권하지 않는다.
Theme만 즉시 저장하는 예외도 다른 Preview를 함께 persist하므로 권하지 않는다.
Apply를 없애고 OK/Cancel만 두는 방식은 계속 편집하면서 저장하는 기존 의미를 바꾸므로 채택하지 않았다.

## Consequences and unresolved details

Controls의 signal/event 재진입이 baseline을 바꾸지 않도록 상태 소유권과 적용 경계를 설계해야 한다.
P3의 content minimum 재측정도 Preview와 rollback에서 함께 일관되게 적용해야 한다.
별도 editor의 성공한 Save는 Settings Cancel의 취소 범위가 아니다.
Restore/import가 revision을 바꿀 때 과거 Draft/Cancel/pending intent가 새 revision을 덮지 못해야 한다.

Autostart/notifications 등 OS side effects는 committed preference와 실제 적용 상태를 구분한다.
OS 실패를 숨기지 않으며 profile persistence와 단일 물리 transaction이라고 주장하지 않는다.
**DEFERRED:** storage technology/schema, concurrency 차단/재기준화 방식, crash recovery,
OS adapter 보상/재시도 상세, Reset UI 및 큰 minimum의 overflow UX.

이 ADR을 별도로 만든 이유는 성공 Apply baseline, 실패, Cancel/Theme/Reset 관계를 하나의 검토 단위로
참조하기 위해서다. P2 승인에 따라 Accepted로 변경했으며 Product Contract와 함께 일관성을 유지한다.
저장 format이나 OS adapter 상세까지 승인된 것으로 확대하지 않는다.
이번에는 문서만 작성했으며 production/tests/project/package 변경은 없다.

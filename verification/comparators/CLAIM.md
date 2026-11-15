# E05 scoped implementation claim

Authorised lane: **CiteLattice — E05 numerical comparator tests**.

## Exclusive write scope

- `verification/comparators/**`
- `docs/evaluation/method-parity.md`
- `tests/test_method_comparators.py`

This lane implements independent pinned bibliometrix/PyBibX comparator adapters,
synthetic known-answer fixtures, fail-closed comparison tests and scoped evidence.
It does not change production calculations or shared plans, contracts, manifests,
locks, CI or `conductor/evaluation-programme.json`. Shared requests belong in the
handoff. No merge is authorised for this lane.

## Ownership inspection

On 2026-11-15, inspected live main
`966ff7d8650568804b90f3a8d3af2dd94516c3b0`, all 23 published branches, open PRs
#9 and #19 (including changed-file lists and discussions), recent PRs, issue
searches for E05/comparator/claim, and the Conductor registry and Track 12.
The three write locations are absent at that main commit. The two open PRs touch
only `.github/workflows/offline-ai-security.yml` and `CONTRIBUTING.md`.
No published overlapping ownership claim was found. This does not establish the
absence of unpublished work or coordinator acknowledgement.

The active coordinator remains chat `6af2d103-38e4-8324-9afa-5ec1d36012f2`
(CiteLattice — Integration and event contracts). It retains producer
protocol/schema, durable recovery/spool, production crates, root Cargo/lock/CI,
registry/evaluation-programme and common plans. It has not acknowledged this
handoff. Recheck published ownership before publication; stop overlapping writes
if a conflicting claim appears.

## Prerequisite and evidence boundary

E04 is `planned` in the inspected evaluation registry. Its native CI receipt and
dependency-review artifacts are absent. Existing scoped CI receipts do not
qualify E04. Independent fixtures and the harness can proceed, but dependent
production numerical qualification remains blocked until the coordinator admits
an exact upstream source/contract/toolchain and E04 evidence revision.

Only public upstream source and repository-authored synthetic inputs are used.
Unknown counts remain unknown; integer values remain exact; g is capped at the
number of actual works. Comparator disagreements must remain visible.

## Work state

- [x] Inspect published ownership and E04 prerequisite.
- [x] Implement independent fixtures, pinned comparator harness and tests.
- [x] Execute available checks; distinguish unavailable runtimes and blocked qualification.
- [x] Review/fix scoped implementation. Exact published SHA and integrator handoff are recorded in PR #22.
- [!] E04 admission, production numerical qualification and R-native execution remain blocked.

Durable claim: <https://github.com/edithatogo/CiteLattice/pull/22>.
The coordinator has not acknowledged this lane; published overlap was rechecked
during implementation. No additional worker or chat was created.

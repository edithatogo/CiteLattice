# Project workflow

This is the brownfield adaptation of the upstream Conductor workflow to the
existing single-maintainer repository (see [AGENTS.md](../AGENTS.md)).

1. Read the index, requirements, design, active track plan, relevant contracts
   and existing issue/PR ownership. Use one scoped change and PR; no duplicate
   issue trees. Mark task [~] when started, [x] only after observed evidence.
2. Document interface, dependency and scientific-method changes before code.
   Use red-first tests for new behavior, minimal implementation, and green
   regression tests. A documentation/configuration change needs integrity
   verification, not fabricated RED/GREEN runtime evidence.
3. Run the applicable commands from the repository root:
   `python -m unittest discover -s tests -v`, `cargo fmt --all -- --check`,
   `cargo check --workspace`, `cargo clippy --workspace --all-targets -- -D warnings`,
   `cargo test --workspace`. Use non-interactive execution and preserve existing
   gates; coverage target >80% for new code where measured, never invent results.
4. Commit scoped changes. Record exact commit, required CI run and acceptance
   evidence in the plan/evidence or linked PR. Git notes are optional; PR and
   exact CI receipts are authoritative here. Independent review/approval and
   all applicable checks must precede integration. No merge on red, missing or
   unreviewed gates. Recheck receiving main.
5. At a phase boundary, reconcile requirements, test evidence, dependencies and
   track status. Do not mark scientific or interoperability work qualified
   from static checks. Keep rights, unsupported cases and negative results.
6. Destructive operations, restricted sharing, new permissions, registry
   publishing and scientific method changes require fresh owner consent.
   No automatic issue multiplication or release promotion.

The original upstream template is available at
[workflow](../vendor/gemini-conductor/skills/conductor-setup/assets/workflow.md).

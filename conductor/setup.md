# Repository-local Conductor setup

Existing Git submodule: `vendor/gemini-conductor`, pinned to upstream
`6e8f9a860bcdd6a2c423473c12e745200688c633` (version 0.3.0).
The repository-local Antigravity plugin link is
`.agents/plugins/conductor -> ../../vendor/gemini-conductor`.
No global or machine-specific plugin state is committed.

From a trusted CiteLattice checkout:

```sh
git submodule update --init vendor/gemini-conductor
git submodule status vendor/gemini-conductor
test -f .agents/plugins/conductor/plugin.json
python3 vendor/gemini-conductor/skills/conductor-setup/scripts/resume.py
python3 -m unittest discover -s tests -p 'test_conductor_setup.py' -v
```

The upstream resumption script at this pin sets setup_complete from index.md
alone. Require every checklist member to be true as well, and use the linked
artifact/registry checks in the repository tests. Schema CI initializes the
pinned submodule and runs the original resume script, verifies its complete
checklist and pin, and compares the two upstream style guides byte-for-byte. In a compatible agent host
reload the workspace plugin and invoke `/conductor:conductor-status` or
`/conductor:conductor-setup` for the native handshake.

Brownfield repair preserves existing requirements, design, dependencies and
track plans. General and Python guides are copied from the pinned upstream
assets; upstream has no Rust-specific guide at this pin. Rust style is adapted from the recovered historical guide and the current
workspace's rustfmt and Clippy configuration. Optional third-party skills
were not installed. The canonical roadmap remains the full registry table;
the native registry lists materialized tracks only. Agent-host activation is
not proven by source control. No live provider or model access is enabled.

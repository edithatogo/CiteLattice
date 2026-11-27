# Rust contracts and interface style

Adapted from the recovered bibx design.2 Rust guide for the current CiteLattice workspace.

- Prefer small crates with explicit dependencies and public boundaries.
- Document public types, variants, fields, aliases and trait methods, including semantics, units and missingness.
- Keep DOI, corpus, source, batch, graph and entity identities distinct. Do not conflate dense IDs across snapshots.
- Separate serializable wire contracts from runtime resources; schema shape does not prove semantic validity.
- Borrow from retained inputs only where safe; use owned messages across async boundaries. Do not fabricate static lifetimes, leak buffers or introduce unchecked self-references.
- Express absence, uncertainty, undefined metrics and insufficient coverage explicitly. Document definitions, windows, counting rules, provenance and coverage.
- Use typed stage interfaces and suitable Send bounds. Keep transitions under runtime ownership.
- Bound work and bytes, not just queue message count. Use deterministic graph merge or a single mutation owner.
- Keep optional backend sessions outside portable core contracts.
- Follow current workspace rustfmt, Clippy and test gates. Never claim a placeholder or historical declaration is an implemented method.

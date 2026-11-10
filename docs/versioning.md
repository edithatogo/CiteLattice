# Dynamic revision and invalidation model

Source revisions, entity reconciliation revisions, methods, parameters, implementations, result tables, scientific scenes, rendering and reports are separately identified.

The run manifest pins exact inputs, time-of-knowledge (first observed) and time-of-publication, observation window, provider citation universe, content digest, rights, method formula, counting policies and backend version. Dynamic aliases such as latest are resolved **before** a run.

A source correction invalidates dependent identity resolution, methods and all downstream artifacts. A method change creates a new scientific lineage. A font/palette change only invalidates render artifacts. A rights revocation invalidates all exposed layers, including hover text and cached tiles; retain only lawful tombstones.

Recompute dependency DAGs may use Salsa, but never substitute in-memory memoization for durable checkpoints. Incremental and full-replay results must agree within declared deterministic/numerical tolerances. Timestamp-only observation changes may early-cut when semantic source data are identical.

Signed or hashed assets provide provenance of bytes, **not truth** of provider content or scientific quality. Unknown major schema versions, stream gaps and repeated event identity with inconsistent payload must fail closed.

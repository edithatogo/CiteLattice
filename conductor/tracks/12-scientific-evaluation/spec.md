# Track 12 — verification, evaluation and measured frontier advances

**Status:** executable programme specified; initial citation slice source-authored,
not Rust-compiled in this authoring session. No empirical superiority is claimed.

## Objective

Move CiteLattice from a broad contract catalogue to reproducible scientific
software. Establish exact conventional results first. Then test specific advances
in coverage-aware conclusions, incremental analysis, evidence-linked imaging and
research decisions. A larger feature list or newer library is not the endpoint.

Canonical task state and dependencies: [evaluation-programme.json](../../evaluation-programme.json).
Implementation files and acceptance commands: [plan.md](plan.md).
Sources and dataset qualifications: [source register](../../../docs/evaluation/sources.md).

## Scope and method definitions

The first scientific unit calculates h, actual-N-capped g, i10, and exact total
citations. It consumes a citation-count sidecar keyed to publications; canonical
CSL remains separately preserved. It does not claim author disambiguation, a
complete citation database, field normalisation or Searchright runtime support.

For N uniquely identified works, observed counts are exact nonnegative integers
in a named citation universe and cutoff. Unknown counts remain null. `reject`
requires all counts; `bounds` calculates the monotone minimum and maximum indices
across completions of the unknown counts. Zero is a mathematical lower-bound
construction, not a substituted observation. Adding unknown *works*, citation
count error and false identity merges are separate assumptions and future tasks.

The lower g must include every actual work in N: for [100, null, null], g is
already 3 even when both unknown counts are zero. Computing g only on the observed
subpopulation would incorrectly return 1. Empty populations yield exact zero
indices; entirely unknown nonempty populations remain `unavailable` with bounds.
The intervals are not confidence intervals. Known total is a lower bound when
counts are missing; no identified upper total is fabricated.

## Evidence levels and claim limits

1. Authored contract/source: identifiable files and method definitions.
2. Native verification: exact commit compiles and passes schema, oracle,
   property, adversarial, stream and CLI tests.
3. Comparator qualification: independently executed, version-pinned numerical
   parity under matched conventions; differences retained.
4. Empirical research: frozen protocol and held-out data, meaningful baselines,
   uncertainty, ablations and failure strata.
5. Independent reproduction: an independently executed package reproduces the
   scoped result; failed and null results remain available.

Only the relevant level permits its claim. Python validation of synthetic
fixtures does not prove Rust behaviour. A checksum verifies bytes, not scientific
truth or authorization. A corpus snapshot is not a labelled ground-truth set.

## Beyond-frontier programme

**R01 — coverage-aware conclusions.** Evaluate false directional/ranking claims
and abstention burden under missing counts, works, references and identity error.
Use controlled perturbations of complete small universes, then source-held-out
snapshots. Compare naive zero filling, complete-case and point-score approaches.
Separate provable identification bounds from model-based calibrated intervals.
Freeze the primary endpoint, useful-effect threshold and permissible abstention
before confirmation. Improvements must hold beyond the development corpus.

**R02 — exact incremental research graphs.** Combine versioned observations with
selective recomputation. Add retractions, corrections, rights deletion, resolver
splits/merges and crash/restart. Test against full recomputation after every wave.
Reuse graph/storage/incremental dependencies only after same-work comparisons.
Performance gains never excuse stale or differently scoped scientific results.

**R03 — evidence-linked imaging.** Test whether provenance drill-down, separate
uncertainty layers and stable temporal layouts improve recognition of meaningful
changes. Control the data and tasks across baseline and enhanced views. Verify
geometry and source membership first; then evaluate interpretation accuracy,
time, calibration and accessibility. A visually attractive or fast GPU scene is
not evidence of scientific benefit. No generative quantitative geometry.

**R04 — adoption and research decisions.** Feed as-of bibliometric features to
Innovate and properly specified uncertainty/utility models to Voiage. Use external
adoption observations, rolling-origin tests, technology-family holdouts and
source-cost/rights sensitivity. Prediction improvement and decision value are
separate endpoints. Add Kairos/Paignia only for a question that requires them.
Perspective/heterogeneity are explicit secondary analyses, not pooled away.

## Dataset and baseline principles

Use repository-authored small oracles, bibliometrix/PyBibX on pinned matched
corpora, OpenAlex/OpenCitations snapshots for scale/source coverage, and S2AND for
entity labels after component-level rights review. Keep original upstreams and
personal forks distinguishable. Exact revisions, asset hashes and source terms
are mandatory before admitting external data. Do not assume a current API
supports replaying historical first-observed states.

Partition by entity/author block, topic, source and time as appropriate; overlapping
publications and duplicated reports cannot leak across partitions. Keep held-out
labels outside development prompts. Record denominator coverage and unavailable
fields. Restrict private/licensed data to approved local execution and prevent
redistribution through hover text, tiles, worksheets or report assets.

## Solo-maintainer delivery

One coherent work unit, one verification result, one PR. No automatic hundreds of
subissues, invented reviewers or mandatory approval for routine refactoring.
Fast tests on changes; targeted mutation/fuzz/concurrency checks on affected
components; longer comparisons on schedules/releases. New privileges, restricted
exports, destructive changes and publication still require appropriate authority.
A research paper or all optional integrations are not prerequisites for a useful
local core release.

Candidate publication routes are a software paper for a validated usable core,
a scientometrics methods paper for R01/R02, and a visual-analytics evaluation for
R03. These are research intentions, not submissions or acceptance claims.

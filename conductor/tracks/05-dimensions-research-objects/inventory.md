# Track 05: research-object receiving inventory (source-neutral)

**Status:** Inventory and one synthetic transport-schema test only. Track 05 remains **Planned** in the Conductor registry. This document is not a qualified Dimensions connector, licensed data entitlement or new production interface.

**Inspected main:** cfd72e73872b33ceddfc923381c51278f94ae428 (2026-11-19). **Scope:** CL-014, grants, patents, clinical trials, policy documents, datasets, and source-neutral cross-domain associations. No licensed-source calls or private records.

## Existing source and rights boundaries

- `crates/citelattice-core/src/contracts/source.rs` defines `ResearchObjectKind` (including all five types), `RightsClass` (redistributable, restricted, unknown, absent), `EvidenceRelation` (source/target identifier strings, predicate, source Revision, optional confidence) and separately identified provider metrics. These types alone do not validate edges or legal entitlements.
- The proposed Searchright `org.scholarly.stream/1.0.0-design.2` nonpublication upsert requires a namespaced key, kind, record artifact with schema ID and digest, and extensions; the event carries explicit rights for metadata, abstracts and full text plus a rights-policy artifact. The schema does **not** define full object fields or directed typed edges.
- `citelattice-ingest` is a bounded in-memory consumer, **not** a live Dimensions adapter or durable producer/consumer connection. Its declared rights strings are not proof that export is authorised.
- The existing citation analysis export permission is caller-declared, not an independent entitlement check. No changes to these integrator-owned interfaces are proposed in this receiving slice.

## Candidate field and typed relationship inventory

These are **publicly documented candidate Dimensions field names**, not a new mandatory schema, live schema introspection or a guarantee of licensed availability. Preserve provider-native IDs as separate namespaces and reconcile identity independently.

| Kind | Candidate fields | Source-directed typed links | Interpretation risks |
| --- | --- | --- | --- |
| Grant | `id`, `grant_number`, `project_numbers`, `funder_orgs`, `research_orgs`, `investigators` and roles, `start_date`, `end_date`, `funding_currency`, currency-specific award amounts, `date_inserted`, funding schemes | Publication `supporting_grant_ids` → grant; patent `associated_grant_ids` → grant; trial `associated_grant_ids` → grant; cross-source link documentation also describes grant `resulting_publication_ids` → publication, subject to field availability check | Award does not establish causal funding of any outcome. Yearly active funding figures must not be summed as new annual disbursements; funding-scheme labels are not normalised. |
| Patent | `id`, `application_number`, `family_id`, `priority_date`, `filing_date`, `publication_date`, `granted_date`, `legal_status`, `assignees`, CPC/IPCR | Patent `publication_ids` → publication; `reference_ids` → patent; `associated_grant_ids` → grant | Application ≠ family ≠ granted patent. Provisional patent references may be unresolved. Estimated expiry is not an authoritative legal determination; citation does not prove commercialisation. |
| Clinical trial | `id`, `registry`, `overall_status`, `phase`, `start_date`, `end_date`, `interventions`, `study_outcome_measures`, `research_orgs` | Trial `publication_ids` → **publications mentioned, excluding resulting publications**; `associated_grant_ids` → grant | Mention is not a reported result or validated clinical effect; registry, reporting and effective dates differ. No participant-level data is within this track. |
| Policy document | `id`, `title`, `year`, `publisher_org`, `publication_ids`, categories, `date_inserted` | Policy document `publication_ids` → cited/related publication | A citation is not policy adoption, effect or research impact; document text has distinct rights. |
| Dataset | `id`, `doi`, `repository`, `license_name`, `license_url`, `date_created`, `date_embargo`, `date_modified`, `authors`, `associated_publication_id` | Dataset `associated_publication_id` → publication; `associated_grant_ids` is **derived from the associated publication**, not direct dataset-funding evidence | Open dataset licence does not automatically license Dimensions-enriched metadata or linked relationships. Embargo/creation/publication dates must remain distinct. |

Provider categories and investigator/organisation resolution are version-sensitive and may be missing. Preserve original values, mapped identifier namespace, classification release and uncertain matches rather than silently joining incompatible populations.

## Proposed relationship and uncertainty requirements (not implemented)

Future receiving edges should record **typed endpoints** (kind and native/canonical identity), direction, predicate and original source-field vocabulary (e.g. supports, cites, mentions, associated_with), exact evidence and rights-policy revision, observed/as-of date, applicable effective dates, matching method, source coverage, and confidence only where independently justified. Keep unresolved endpoints explicitly unresolved. Do not turn a provider association into a causal claim.

Separate provider observation or insertion date from grant award, patent priority/filing, trial registration, policy publication and dataset embargo dates. A present-day record does not establish availability for historical forecasting. Coverage denominators and negative-space must distinguish unobserved, outside source scope, unlicensed, unresolved, withheld/embargoed, explicitly absent and true zero. Missing confidence remains null, never an invented score.

## Rights/entitlement matrix

| Content class | Existing stream transport | Required receiving and export posture |
| --- | --- | --- |
| Metadata | redistributable / restricted / unknown (not absent) | Unknown or restricted must not be inferred to permit redistribution; preserve policy revision and downstream inheritance. |
| Abstracts | redistributable / restricted / unknown / absent | Absent means not supplied, not cleared for export; titles, hover text and hidden marks require review. |
| Full text / documents | redistributable / restricted / unknown / absent | Independently evaluate legal right to store, derive and export; do not embed restricted text in worksheets, SVG, reports or caches. |
| Derived links and metrics | **No per-link entitlement or coverage contract yet** | Default deny external dissemination pending verified provider terms and provenance; version changes and revocations must invalidate derived outputs. |

Dimensions Free and Dimensions Analytics/API differ in source coverage and permitted access. Reading public documentation does not create an API or redistribution licence. Dataset licence fields apply to the underlying dataset under its own terms, not necessarily to provider-derived records. No licensed records were queried.

## One executable synthetic check

`python -m unittest discover -s tests -p 'test_track05_rights_transport.py' -v` validates the existing stream JSON Schema with all five artificial nonpublication kinds, explicit unknown metadata and restricted abstracts. It rejects unsupported rights classes, missing rights-policy artifacts, missing typed records and inappropriate CSL fields. This is **schema-level evidence only**; it does not exercise native Rust semantics, export enforcement, source coverage or real-source relationship matching.

## Dependency holds and handoff

1. The integrator and Track 01 owner must qualify any additional object-record schema, directed typed edge interface, source versioning, correction/deletion and rights propagation before implementation. No root CI, track registry, shared source type or producer schema changes here.
2. An authorised rights/entitlement determination and source coverage strategy is required for each provider/content class prior to licensed data access or redistribution.
3. Native exact-head validation, source coverage/as-of negatives, relation typing and output-disclosure audits remain pending. The full Track 05 is **not complete**.

## Public documentation consulted (no record queries)

- [Dimensions DSL source inventory](https://docs.dimensions.ai/dsl/data-sources.html), [grants](https://docs.dimensions.ai/dsl/datasource-grants.html), [patents](https://docs.dimensions.ai/dsl/datasource-patents.html), [clinical trials](https://docs.dimensions.ai/dsl/datasource-clinical_trials.html), [policy](https://docs.dimensions.ai/dsl/datasource-policy_documents.html), [datasets](https://docs.dimensions.ai/dsl/datasource-datasets.html), [cross-source links](https://docs.dimensions.ai/dsl/data-model.html) (consulted 2026-11-19).
- [Included content](https://help.dimensions.ai/en/articles/9780225), [relationship interpretations](https://help.dimensions.ai/en/articles/9780545), [Free versus Analytics](https://help.dimensions.ai/en/articles/9777473).

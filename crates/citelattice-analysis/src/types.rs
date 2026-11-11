//! Portable input/result wire types. Counts use decimal strings to avoid JSON precision loss.
use citelattice_core::contracts::versioning::Revision;
use serde::{Deserialize, Deserializer, Serialize};

/// Exact unsigned count; JSON representation is a canonical decimal string.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(try_from = "String", into = "String")]
pub struct CitationCount(pub u64);

impl TryFrom<String> for CitationCount {
    type Error = &'static str;

    fn try_from(value: String) -> Result<Self, Self::Error> {
        if value.is_empty()
            || (value.len() > 1 && value.starts_with('0'))
            || !value.bytes().all(|b| b.is_ascii_digit())
        {
            return Err("count must be a canonical unsigned decimal string");
        }
        value
            .parse::<u64>()
            .map(Self)
            .map_err(|_| "count exceeds u64")
    }
}

impl From<CitationCount> for String {
    fn from(value: CitationCount) -> Self {
        value.0.to_string()
    }
}

fn required_count<'de, D>(input: D) -> Result<Option<CitationCount>, D::Error>
where
    D: Deserializer<'de>,
{
    Option::<CitationCount>::deserialize(input)
}

/// An observation is keyed to an existing canonical publication identifier.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CitationObservation {
    /// Unique identity within the declared population; no silent deduplication.
    pub id: String,
    /// Explicit null means unknown, not zero. The field itself must be present.
    #[serde(deserialize_with = "required_count")]
    pub citations: Option<CitationCount>,
}

/// Scientific scope is mandatory even when counts happen to be identical.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CitationContext {
    /// Exact selected-publication population identity.
    pub population_id: String,
    /// Citation database/universe and counting policy identity.
    pub citation_universe: String,
    /// RFC3339 cutoff; not the current clock or an implied publication date.
    pub as_of: String,
}

/// Unknown counts are either rejected or represented by extremal bounds.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum MissingPolicy {
    /// Require a known count for every supplied publication.
    Reject,
    /// Retain unknown works and bound possible metric values.
    Bounds,
}

/// Caller-declared export policy; this is not independent proof of entitlement.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ExportPermission {
    /// Caller declares that derived outputs may be exported.
    Allowed,
    /// Local calculation may occur but library export paths must refuse.
    Denied,
    /// No verified declaration was supplied; export paths must refuse.
    Unknown,
}

/// One complete, bounded citation analysis; not a cross-request update event.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CitationRequest {
    /// Must be `org.citelattice.citation_request`.
    pub contract: String,
    /// Exactly `1.0.0` for this implementation.
    pub version: String,
    /// Caller-declared upstream source snapshot; external bytes are not fetched.
    pub source: Revision,
    /// Population, citation universe and observation cutoff.
    pub context: CitationContext,
    /// Explicit unknown-count behaviour.
    pub missing: MissingPolicy,
    /// Rights decision carried into the result and checked before output.
    pub export: ExportPermission,
    /// Actual publications, including those with unknown counts.
    pub observations: Vec<CitationObservation>,
}

/// Integer range over possible completions, not a confidence interval.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct IndexInterval {
    /// Minimum attainable value under the declared missing-count assumptions.
    pub lower: u64,
    /// Maximum attainable value over the supplied actual publications.
    pub upper: u64,
}

/// Coverage state of the supplied counts, not global database completeness.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum CitationStatus {
    /// Every supplied work has an observed count; includes the empty population.
    Complete,
    /// Some but not all supplied works have observed counts.
    Partial,
    /// Nonempty population with no observed counts.
    Unavailable,
}

/// Exact citation summaries plus explicit coverage-dependent metric intervals.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CitationSummary {
    /// Number of supplied actual works.
    pub works: u64,
    /// Number with a known citation count.
    pub observed: u64,
    /// Number whose citation count is unknown.
    pub missing: u64,
    /// Coverage state for this population.
    pub status: CitationStatus,
    /// Hirsch index over the declared population and citation universe.
    pub h: IndexInterval,
    /// g-index capped at the number of actual works (no fictitious extra works).
    pub g: IndexInterval,
    /// Number of works with at least ten citations.
    pub i10: IndexInterval,
    /// Sum of observed counts, and lower bound on total; exact decimal string.
    pub known_total: String,
    /// Exact same total when complete; null when unknown counts prevent identification.
    pub total_upper: Option<String>,
}

/// Fingerprints have distinct invalidation semantics.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct RunIdentity {
    /// Source, scope and identity-sorted observations.
    pub input_sha256: String,
    /// Input plus method, implementation and missing-count policy.
    pub calculation_sha256: String,
    /// Whole normalised request, including export permission.
    pub request_sha256: String,
}

/// Executable identity; an absent build revision means source attestation is unavailable.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ImplementationIdentity {
    /// Cargo package identifier.
    pub package: String,
    /// Cargo package version.
    pub version: String,
    /// Optional build-time revision injected by trusted CI; never inferred.
    pub build_revision: Option<String>,
}

/// Hashable result payload, deliberately excluding its enclosing digest.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ResultBody {
    /// Result contract identifier.
    pub contract: String,
    /// Result contract version.
    pub version: String,
    /// Scientific definition identifier.
    pub method: String,
    /// Definition version independent of crate version.
    pub method_version: String,
    /// Actual package/build identity.
    pub implementation: ImplementationIdentity,
    /// Upstream source revision supplied by the caller.
    pub source: Revision,
    /// Scope retained with the numerical result.
    pub context: CitationContext,
    /// Permission re-evaluated by every provided output route.
    pub export: ExportPermission,
    /// Content-addressed dependency identities.
    pub identity: RunIdentity,
    /// Scientific values and their coverage state.
    pub summary: CitationSummary,
}

/// Deterministic output envelope. A hash detects changed bytes, not dishonest recomputation.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct AnalysisResult {
    /// Actual result; no embedded raw abstracts or paper lists.
    pub body: ResultBody,
    /// Domain-separated RFC 8785/SHA-256 fingerprint of `body` only.
    pub sha256: String,
}

/// Rendering dependency key input; no renderer is implemented by this type.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct RenderSpec {
    /// Exact graphics engine revision.
    pub renderer: Revision,
    /// Scientific scene fingerprint, including transforms and layout.
    pub scene_sha256: String,
    /// Style, fonts and other asset manifest fingerprint.
    pub assets_sha256: String,
}

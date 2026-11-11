//! Offline citation summaries with explicit missingness, exact totals and provenance.
//!
//! This module consumes citation-count sidecars keyed to canonical publication IDs.
//! It does not acquire citations, resolve author identities or implement the
//! Searchright event protocol. Native verification is required before release.
#![forbid(unsafe_code)]

mod identity;
mod metrics;
mod stream;
mod types;
mod validate;

pub use identity::render_key;
pub use metrics::analyze;
pub use stream::{StreamError, StreamLimits, run_jsonl};
pub use types::*;

/// Maximum number of actual publications in one analysis request.
pub const MAX_OBSERVATIONS: usize = 100_000;
/// Scientific definition version, independent of the executable package version.
pub const METHOD_VERSION: &str = "1.0.0";
/// Stable method identifier; g is capped at the supplied publication count.
pub const METHOD_ID: &str = "org.citelattice.citation-summary.actual-n";

/// Validation failures are intentionally non-disclosing and exclude raw inputs.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum AnalysisError {
    /// An incompatible contract or method request was supplied.
    #[error("unsupported contract version")]
    Version,
    /// A label, source fingerprint or source revision is invalid.
    #[error("invalid identifier, revision or digest")]
    Metadata,
    /// The observation cutoff cannot be parsed as RFC3339.
    #[error("invalid observation cutoff")]
    Date,
    /// A work appears more than once; deduplication must be explicit upstream.
    #[error("duplicate publication identity")]
    DuplicateId,
    /// The selected policy forbids unknown counts.
    #[error("missing citation count under reject policy")]
    MissingCounts,
    /// An observation or numeric safety limit was exceeded.
    #[error("analysis resource or arithmetic limit exceeded")]
    Limit,
    /// Serialisation or canonicalisation failed.
    #[error("canonical encoding failed")]
    Encoding,
    /// The caller did not declare permission for derived export.
    #[error("derived export permission is absent or denied")]
    ExportDenied,
    /// A result no longer matches its declared content fingerprint.
    #[error("result integrity check failed")]
    Integrity,
}

//! Version identities must not conflate source, scientific meaning and rendering.
use serde::{Deserialize, Serialize};

/// SemVer identity plus exact content fingerprint of a schema, method or tool.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Revision {
    /// Namespaced stable identifier.
    pub id: String,
    /// Exact semantic version, not a dynamic `latest` alias.
    pub version: String,
    /// Lowercase SHA-256 hex over canonical bytes (semantic validation required).
    pub sha256: String,
}

/// Evidence and reproducibility fingerprints at different dependency stages.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct AnalysisLineage {
    /// Source data and rights snapshot; immutable in one run.
    pub input: Revision,
    /// Definition of the computation, including cited method and conventions.
    pub method: Revision,
    /// Explicit parameters, entity resolution, coverage, and corpus membership.
    pub parameter_digest: String,
    /// Executable implementation and deterministic backend identity.
    pub implementation: Revision,
    /// Optional seed for random methods; null for non-random calculations.
    pub seed: Option<u64>,
}

/// Result, scientific scene and render may vary independently.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct OutputLineage {
    /// The calculation that produced the authoritative result table.
    pub analysis: AnalysisLineage,
    /// Typed Arrow/table-schema revision.
    pub table: Revision,
    /// Independent scientific scene/mark specification.
    pub scene: Option<Revision>,
    /// Renderer, fonts, layout, tolerances and selected output medium.
    pub render: Option<Revision>,
}

/// Why dependent artifacts must be invalidated.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum InvalidationReason {
    /// A meaningful input observation or corpus scope changed.
    SourceChanged,
    /// Identity resolution or evidence linkage changed.
    EntityResolutionChanged,
    /// Scientific method or population policy changed.
    MethodChanged,
    /// Only display style or graphics engine changed.
    RenderOnly,
    /// Rights permit only a redacted/tombstoned derivative.
    RightsChanged,
}

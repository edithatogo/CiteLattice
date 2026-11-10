//! Evidence-bearing quantitative images: geometry is data, never invented by an LLM.
use serde::{Deserialize, Serialize};
use super::versioning::Revision;

/// Epistemic sources must not be merged into a single decorative error band.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum UncertaintyKind {
    /// Sampling and statistical estimation.
    Statistical,
    /// Incomplete source and citation universe.
    SourceCoverage,
    /// Conflicting author, institution, publication or trial identities.
    EntityResolution,
    /// Model/embedding sensitivity and calibration.
    Model,
    /// Stochastic or approximation-related drawing/layout variability.
    Layout,
}

/// A mark is grounded by exact row keys and transformation lineage.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct EvidenceMark {
    /// Stable mark ID across render variants.
    pub id: String,
    /// Referenced Arrow/Parquet table artifact.
    pub table: Revision,
    /// Exact contributing row keys, or membership artifact for large aggregates.
    pub row_keys: Vec<String>,
    /// Required when aggregated membership cannot fit within the mark.
    pub membership: Option<Revision>,
    /// Explicit transform or layout method revision.
    pub transform: Revision,
    /// Quantitative value (if applicable); never substitute zero for missing.
    pub value: Option<f64>,
    /// Source of uncertainty associated with the mark.
    pub uncertainty: Vec<UncertaintyKind>,
}

/// Scientific scene is separate from underlying results and device render.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct EvidenceSceneContract {
    /// Scene version and full semantic fingerprint.
    pub scene: Revision,
    /// Scientific chart/graph specification, e.g. Vega-Lite or custom graph scene.
    pub grammar: String,
    /// Exact source/derived table artifacts.
    pub tables: Vec<Revision>,
    /// Every visible mark must resolve to a scientific source or aggregate.
    pub marks: Vec<EvidenceMark>,
    /// Exact comparison snapshots, ordered by evidence time.
    pub timeline: Vec<Revision>,
    /// Stable coordinate/label/cluster alignment method.
    pub alignment: Option<Revision>,
    /// Sampling/LOD membership and conservation diagnostics.
    pub level_of_detail: Option<Revision>,
    /// Accessible equivalent table and text semantics.
    pub accessible_data: Revision,
    /// Policy for hidden layers, tiles, SVG metadata, hover text and interaction.
    pub disclosure_policy: Revision,
}

/// Rendering is independently versioned; cosmetic changes do not change metrics.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct RenderReceiptContract {
    /// Exact scientific scene input.
    pub scene: Revision,
    /// Implementation, font assets, graphics backend and device settings.
    pub renderer: Revision,
    /// Output artifact with media type specified by format/manifest.
    pub output: Revision,
    /// Deterministic or bounded-tolerance reproducibility classification.
    pub reproducibility: String,
    /// Quantitative geometry and source-value audit reference.
    pub geometry_check: Revision,
    /// Accessibility and privacy leak-check result.
    pub disclosure_check: Revision,
}

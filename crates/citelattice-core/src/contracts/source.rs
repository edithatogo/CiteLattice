//! Input and cross-domain research-object contracts.
use super::versioning::Revision;
use serde::{Deserialize, Serialize};

/// A provider-identified research object; publications have separate canonical CSL.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ResearchObjectKind {
    /// Scholarly publication, including preprints and book chapters.
    Publication,
    /// Awarded research grant.
    Grant,
    /// Patent family or application.
    Patent,
    /// Registered trial or other prospective study registry item.
    ClinicalTrial,
    /// Policy or clinical guideline document.
    PolicyDocument,
    /// Data publication or repository dataset.
    Dataset,
    /// Research software release.
    Software,
    /// Technical report or grey literature.
    Report,
}

/// Rights are independent for each content class and downstream use.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum RightsClass {
    /// Licensed for redistribution under the declared licence.
    Redistributable,
    /// May be analysed locally, but export requires separate permission.
    Restricted,
    /// No verified rights determination exists.
    Unknown,
    /// This content class was not supplied.
    Absent,
}

/// Provenance-bearing relationship, not a claim of impact or causality.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct EvidenceRelation {
    /// Exact source object reference.
    pub from: String,
    /// Exact target object reference.
    pub to: String,
    /// Provider-defined relation vocabulary/URI (e.g. cited-by, supported-by).
    pub predicate: String,
    /// Evidence set and retrieval provenance.
    pub source: Revision,
    /// Explicitly unknown when absent, rather than an invented confidence.
    pub confidence: Option<f64>,
}

/// Independent external metrics are observations, never silently re-computed synonyms.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ProviderMetric {
    /// Provider-defined name, e.g. dimensions:fcr or dimensions:rcr.
    pub metric_id: String,
    /// Numerical result when provider and eligibility supply it.
    pub value: Option<f64>,
    /// Provider, definition, calculation cohort, date and source data fingerprint.
    pub definition: Revision,
    /// Inclusion rules and any disclosed comparison universe.
    pub eligible_population: String,
    /// Coverage and known limitations.
    pub limitations: Vec<String>,
}

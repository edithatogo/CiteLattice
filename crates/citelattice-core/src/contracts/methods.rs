//! Explicit scientific definitions and eligibility, not generic metric-name strings.
use serde::{Deserialize, Serialize};
use super::versioning::Revision;

/// Distinct core scientific analysis families.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum AnalysisFamily {
    /// Publication distributions, production, Bradford/Lotka/Zipf analyses.
    Descriptive,
    /// Citation counts, h/g/e/m/i10, normalisation, citation trajectories.
    CitationIndicators,
    /// Intellectual, social or conceptual structure, coupling, co-citation.
    Network,
    /// Main paths, RPYS, burst detection, sleeping beauties and disruption.
    Temporal,
    /// Semantic content, keywords, topics, concept change and embeddings.
    Semantic,
    /// Grants, patents, trials, datasets, policy connections and portfolios.
    ResearchEcosystem,
    /// Coverage robustness, sensitivity, disagreement and multiverse analysis.
    Uncertainty,
}

/// Scientific output definition; citations and independent oracles are mandatory for promotion.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct MethodSpec {
    /// Stable outcome and exact definition revision.
    pub method: Revision,
    /// One declared family.
    pub family: AnalysisFamily,
    /// DOI/URL/reference for mathematical definition, independent of code.
    pub reference: String,
    /// Required input attributes; absence is a reported blocker.
    pub required_fields: Vec<String>,
    /// Source corpus, time horizon, citation universe and applicable counting conventions.
    pub population_rule: String,
    /// Normalization, missingness and edge-case policy.
    pub conventions: Vec<String>,
    /// Exact parameter-schema revision.
    pub parameters_schema: Revision,
    /// Exact result-schema revision.
    pub output_schema: Revision,
    /// Independent known-answer fixture IDs (empty => not scientifically qualified).
    pub oracle_fixtures: Vec<String>,
}

/// Method implementation state must not be inferred from a registered name.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum MethodMaturity {
    /// Named outcome with incomplete method definition.
    Inventoried,
    /// Complete scientific spec, independently specified oracle not yet executed.
    Specified,
    /// Implementation present, verification not yet observed.
    Implemented,
    /// Independent method and differential tests verified at exact revision.
    Validated,
}

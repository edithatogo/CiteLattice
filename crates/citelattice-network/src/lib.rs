//! Exact, bounded local citation, reference co-citation and bibliographic coupling.
#![forbid(unsafe_code)]

use std::collections::{BTreeMap, BTreeSet};

use petgraph::Direction::Incoming;
use petgraph::graph::{DiGraph, NodeIndex};
use serde::{Deserialize, Serialize};

/// Input coverage is observed, not inferred from an empty reference list.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ReferenceCoverage {
    /// Complete for the declared and externally established source universe.
    Complete,
    /// Source lists some but not necessarily all references.
    Partial,
    /// Completeness has not been established.
    Unknown,
}

/// Explicit, source-normalized cited IDs for a single publication.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct PaperReferences {
    /// Local stable paper key; not assumed globally canonical.
    pub paper_id: String,
    /// Exact declared cited identifiers; duplicate entries are ignored.
    pub references: Vec<String>,
    /// Reference-list completeness as explicitly reported by the source.
    pub coverage: ReferenceCoverage,
}

/// Upper limits for adversarially large graph expansion.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct NetworkLimits {
    /// Maximum number of distinct papers.
    pub max_papers: usize,
    /// Maximum references on any single paper.
    pub max_references_per_paper: usize,
    /// Maximum attempted pair operations across both coupling and co-citation.
    pub max_pair_operations: u64,
}
impl Default for NetworkLimits {
    fn default() -> Self {
        Self {
            max_papers: 100_000,
            max_references_per_paper: 100_000,
            max_pair_operations: 10_000_000,
        }
    }
}

/// Invalid scientific input and exceeded resource limits.
#[derive(Debug, thiserror::Error)]
pub enum NetworkError {
    /// An input paper identifier was repeated.
    #[error("duplicate paper identity")]
    DuplicatePaper,
    /// One identifier is missing/blank or references itself.
    #[error("invalid identifier or self-reference")]
    InvalidIdentifier,
    /// The corpus is too large.
    #[error("paper limit exceeded")]
    PaperBudget,
    /// One paper has too many declared references.
    #[error("reference list limit exceeded")]
    ReferenceBudget,
    /// Co-occurrence pair expansion exhausted the memory/work budget.
    #[error("pair operation budget exceeded")]
    PairBudget,
    /// Integer representability failed.
    #[error("count overflow")]
    Overflow,
}

/// Directed citation among papers in this supplied corpus only.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct DirectedCitation {
    /// Citing paper ID.
    pub citing: String,
    /// Cited paper ID.
    pub cited: String,
}

/// Unsigned edge count for either coupling or co-citation.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct WeightedPair {
    /// Canonically ordered left identity.
    pub a: String,
    /// Canonically ordered right identity.
    pub b: String,
    /// Number of shared evidence items.
    pub count: u64,
}

/// Inbound local citation count from the supplied corpus, not global citation impact.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct PaperInDegree {
    /// Source paper ID.
    pub paper_id: String,
    /// Number of citations from supplied publication records.
    pub count: u64,
}

/// Completeness status for the supplied reference lists.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub struct CoverageCounts {
    /// Lists declared complete in their source universe.
    pub complete: u64,
    /// Lists declared partial.
    pub partial: u64,
    /// Lists with unknown completeness.
    pub unknown: u64,
}

/// A deterministic, corpus-scoped structural network result.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct NetworkSummary {
    /// Contract identifier.
    pub schema_version: String,
    /// Observed local citation edges.
    pub direct: Vec<DirectedCitation>,
    /// Pairs of cited references, weighted by source papers mentioning both.
    pub co_cited: Vec<WeightedPair>,
    /// Pairs of papers, weighted by their shared cited references.
    pub coupled: Vec<WeightedPair>,
    /// Petgraph-derived inbound degree, restricted to known paper identities.
    pub in_degree: Vec<PaperInDegree>,
    /// Source-declared reference completeness.
    pub completeness: CoverageCounts,
    /// Universal limitation of this output.
    pub interpretation: String,
}

fn identifier_is_valid(id: &str) -> bool {
    !id.trim().is_empty() && id.trim() == id && !id.chars().any(char::is_control)
}

fn charge(used: &mut u64, max: u64) -> Result<(), NetworkError> {
    *used = used.checked_add(1).ok_or(NetworkError::Overflow)?;
    if *used > max {
        return Err(NetworkError::PairBudget);
    }
    Ok(())
}
fn increment<K: Ord>(values: &mut BTreeMap<K, u64>, key: K) -> Result<(), NetworkError> {
    let entry = values.entry(key).or_default();
    *entry = entry.checked_add(1).ok_or(NetworkError::Overflow)?;
    Ok(())
}

/// Calculate citation edges, co-citation, coupling and observed local in-degree.
///
/// # Errors
/// Rejects duplicate identifiers, unbounded pair expansion, self-citations,
/// invalid source identity and numeric overflows. Missing references are not
/// imputed. Incomplete lists make derived indicators provisional.
pub fn analyze(
    records: &[PaperReferences],
    limits: NetworkLimits,
) -> Result<NetworkSummary, NetworkError> {
    if records.len() > limits.max_papers {
        return Err(NetworkError::PaperBudget);
    }
    let mut observed = BTreeMap::<String, (Vec<String>, ReferenceCoverage)>::new();
    let mut completeness = CoverageCounts { complete: 0, partial: 0, unknown: 0 };
    for row in records {
        if !identifier_is_valid(&row.paper_id) {
            return Err(NetworkError::InvalidIdentifier);
        }
        if row.references.len() > limits.max_references_per_paper {
            return Err(NetworkError::ReferenceBudget);
        }
        if row.references.iter().any(|value| !identifier_is_valid(value) || value == &row.paper_id) {
            return Err(NetworkError::InvalidIdentifier);
        }
        let refs: Vec<String> = row.references.iter().cloned().collect::<BTreeSet<_>>().into_iter().collect();
        if observed.insert(row.paper_id.clone(), (refs, row.coverage)).is_some() {
            return Err(NetworkError::DuplicatePaper);
        }
        match row.coverage {
            ReferenceCoverage::Complete => completeness.complete += 1,
            ReferenceCoverage::Partial => completeness.partial += 1,
            ReferenceCoverage::Unknown => completeness.unknown += 1,
        }
    }
    let mut graph = DiGraph::<String, ()>::new();
    let mut nodes = BTreeMap::<String, NodeIndex>::new();
    for id in observed.keys() {
        nodes.insert(id.clone(), graph.add_node(id.clone()));
    }
    let mut direct = Vec::new();
    let mut co_citation = BTreeMap::<(String, String), u64>::new();
    let mut inverted = BTreeMap::<String, BTreeSet<String>>::new();
    let mut operations = 0_u64;
    for (id, (refs, _)) in &observed {
        for reference in refs {
            inverted.entry(reference.clone()).or_default().insert(id.clone());
            if let Some(target) = nodes.get(reference) {
                graph.add_edge(nodes[id], *target, ());
                direct.push(DirectedCitation { citing: id.clone(), cited: reference.clone() });
            }
        }
        for (i, first) in refs.iter().enumerate() {
            for second in refs.iter().skip(i + 1) {
                charge(&mut operations, limits.max_pair_operations)?;
                increment(&mut co_citation, (first.clone(), second.clone()))?;
            }
        }
    }
    let mut coupling = BTreeMap::<(String, String), u64>::new();
    for papers in inverted.values() {
        let members: Vec<_> = papers.iter().collect();
        for (i, first) in members.iter().enumerate() {
            for second in members.iter().skip(i + 1) {
                charge(&mut operations, limits.max_pair_operations)?;
                increment(&mut coupling, ((*first).clone(), (*second).clone()))?;
            }
        }
    }
    let mut in_degree = Vec::new();
    for (id, node) in nodes {
        let count = u64::try_from(graph.neighbors_directed(node, Incoming).count())
            .map_err(|_| NetworkError::Overflow)?;
        in_degree.push(PaperInDegree { paper_id: id, count });
    }
    Ok(NetworkSummary {
        schema_version: "org.citelattice.network.v1".to_owned(),
        direct,
        co_cited: co_citation.into_iter().map(|((a,b),count)| WeightedPair {a,b,count}).collect(),
        coupled: coupling.into_iter().map(|((a,b),count)| WeightedPair {a,b,count}).collect(),
        in_degree,
        completeness,
        interpretation: "observed corpus only; missing references, source coverage and entity identities are not inferred".to_owned(),
    })
}

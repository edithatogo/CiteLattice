use citelattice_analysis::{
    CitationContext, CitationCount, CitationObservation, CitationRequest, ExportPermission,
    MissingPolicy,
};
use citelattice_core::contracts::versioning::Revision;

pub fn request(counts: &[Option<u64>]) -> CitationRequest {
    CitationRequest {
        contract: "org.citelattice.citation_request".to_owned(),
        version: "1.0.0".to_owned(),
        source: Revision {
            id: "synthetic:source".to_owned(),
            version: "1.0.0".to_owned(),
            sha256: "a".repeat(64),
        },
        context: CitationContext {
            population_id: "synthetic:population".to_owned(),
            citation_universe: "synthetic:citations".to_owned(),
            as_of: "2026-11-10T00:00:00Z".to_owned(),
        },
        missing: MissingPolicy::Bounds,
        export: ExportPermission::Allowed,
        observations: counts
            .iter()
            .enumerate()
            .map(|(i, n)| CitationObservation {
                id: format!("work:{i}"),
                citations: n.map(CitationCount),
            })
            .collect(),
    }
}

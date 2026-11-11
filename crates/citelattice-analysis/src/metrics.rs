use crate::{
    identity, validate, AnalysisError, AnalysisResult, CitationRequest, CitationStatus,
    CitationSummary, IndexInterval, ResultBody, METHOD_ID, METHOD_VERSION,
};

struct Indices {
    h: u64,
    g: u64,
    i10: u64,
    total: u128,
}

fn indices(mut counts: Vec<u64>) -> Result<Indices, AnalysisError> {
    counts.sort_unstable_by(|a, b| b.cmp(a));
    let mut result = Indices { h: 0, g: 0, i10: 0, total: 0 };
    for (offset, count) in counts.into_iter().enumerate() {
        let rank = u64::try_from(offset + 1).map_err(|_| AnalysisError::Limit)?;
        result.total = result.total.checked_add(u128::from(count)).ok_or(AnalysisError::Limit)?;
        if count >= rank {
            result.h = rank;
        }
        let rank_squared = u128::from(rank) * u128::from(rank);
        if result.total >= rank_squared {
            result.g = rank;
        }
        if count >= 10 {
            result.i10 += 1;
        }
    }
    Ok(result)
}

fn summary(request: &CitationRequest) -> Result<CitationSummary, AnalysisError> {
    let works = u64::try_from(request.observations.len()).map_err(|_| AnalysisError::Limit)?;
    let observed = u64::try_from(request.observations.iter().filter(|r| r.citations.is_some()).count())
        .map_err(|_| AnalysisError::Limit)?;
    let lower = indices(request.observations.iter().map(|r| r.citations.map_or(0, |v| v.0)).collect())?;
    // Under MAX_OBSERVATIONS, u64::MAX exceeds every relevant h/g/i10
    // threshold. It is a mathematical upper construction, not imputed data.
    let upper = indices(request.observations.iter().map(|r| r.citations.map_or(u64::MAX, |v| v.0)).collect())?;
    let status = if observed == works {
        CitationStatus::Complete
    } else if observed == 0 {
        CitationStatus::Unavailable
    } else {
        CitationStatus::Partial
    };
    Ok(CitationSummary {
        works,
        observed,
        missing: works - observed,
        status,
        h: IndexInterval { lower: lower.h, upper: upper.h },
        g: IndexInterval { lower: lower.g, upper: upper.g },
        i10: IndexInterval { lower: lower.i10, upper: upper.i10 },
        known_total: lower.total.to_string(),
        total_upper: (observed == works).then(|| lower.total.to_string()),
    })
}

/// Calculate a reproducible citation summary over supplied actual publications.
///
/// Observed counts are assumed exact within the declared universe. Bounds cover
/// missing **counts**, not missing publications, misassigned authors or erroneous
/// observations. They are identification ranges, not confidence intervals.
/// Local calculation is allowed independently of derived-export permission.
///
/// # Errors
/// Rejects unsupported versions, invalid scope/revisions, duplicate identities,
/// oversized populations and missing counts under the reject policy.
pub fn analyze(request: &CitationRequest) -> Result<AnalysisResult, AnalysisError> {
    validate::request(request)?;
    let mut normalized = request.clone();
    normalized.observations.sort_by(|a, b| a.id.cmp(&b.id));
    let implementation = identity::implementation();
    let identity = identity::identity(&normalized, &implementation)?;
    let body = ResultBody {
        contract: "org.citelattice.citation_result".to_owned(),
        version: "1.0.0".to_owned(),
        method: METHOD_ID.to_owned(),
        method_version: METHOD_VERSION.to_owned(),
        implementation,
        source: normalized.source.clone(),
        context: normalized.context.clone(),
        export: normalized.export,
        identity,
        summary: summary(&normalized)?,
    };
    let sha256 = identity::fingerprint("citelattice.result.v1", &body)?;
    Ok(AnalysisResult { body, sha256 })
}

use std::collections::BTreeSet;

use citelattice_core::contracts::versioning::Revision;
use time::{OffsetDateTime, format_description::well_known::Rfc3339};

use crate::{AnalysisError, CitationRequest, MAX_OBSERVATIONS, MissingPolicy};

pub(crate) fn text(value: &str) -> bool {
    !value.is_empty()
        && value.len() <= 1024
        && value.trim() == value
        && !value.chars().any(char::is_control)
}

pub(crate) fn digest(value: &str) -> bool {
    value.len() == 64
        && value
            .bytes()
            .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
}

pub(crate) fn revision(value: &Revision) -> Result<(), AnalysisError> {
    if !text(&value.id)
        || !text(&value.version)
        || semver::Version::parse(&value.version).is_err()
        || !digest(&value.sha256)
    {
        return Err(AnalysisError::Metadata);
    }
    Ok(())
}

pub(crate) fn request(value: &CitationRequest) -> Result<(), AnalysisError> {
    if value.contract != "org.citelattice.citation_request" || value.version != "1.0.0" {
        return Err(AnalysisError::Version);
    }
    if value.observations.len() > MAX_OBSERVATIONS {
        return Err(AnalysisError::Limit);
    }
    revision(&value.source)?;
    if !text(&value.context.population_id) || !text(&value.context.citation_universe) {
        return Err(AnalysisError::Metadata);
    }
    if value.context.as_of.len() > 64
        || OffsetDateTime::parse(&value.context.as_of, &Rfc3339).is_err()
    {
        return Err(AnalysisError::Date);
    }
    let mut seen = BTreeSet::new();
    for observation in &value.observations {
        if !text(&observation.id) {
            return Err(AnalysisError::Metadata);
        }
        if !seen.insert(&observation.id) {
            return Err(AnalysisError::DuplicateId);
        }
        if observation.citations.is_none() && value.missing == MissingPolicy::Reject {
            return Err(AnalysisError::MissingCounts);
        }
    }
    Ok(())
}

//! Independent fixtures and missing-count mathematical bounds.
mod common;
use citelattice_analysis::{AnalysisError, CitationStatus, MissingPolicy, analyze};
use serde::Deserialize;
#[derive(Deserialize)]
struct Oracle {
    cases: Vec<Case>,
}
#[derive(Deserialize)]
struct Case {
    id: String,
    counts: Vec<u64>,
    expected: Expected,
}
#[derive(Deserialize)]
struct Expected {
    h: u64,
    g: u64,
    i10: u64,
    total: String,
}

#[test]
fn independent_subset_oracles() -> Result<(), Box<dyn std::error::Error>> {
    let fixture: Oracle =
        serde_json::from_str(include_str!("../../../verification/citation-oracles.json"))?;
    for c in fixture.cases {
        let counts: Vec<_> = c.counts.iter().copied().map(Some).collect();
        let result = analyze(&common::request(&counts))?;
        let s = &result.body.summary;
        assert_eq!(s.h.lower, c.expected.h, "{}", c.id);
        assert_eq!(s.g.lower, c.expected.g, "{}", c.id);
        assert_eq!(s.i10.lower, c.expected.i10, "{}", c.id);
        assert_eq!(s.known_total, c.expected.total, "{}", c.id);
        assert_eq!(s.h.lower, s.h.upper);
        assert_eq!(s.g.lower, s.g.upper);
        assert_eq!(s.status, CitationStatus::Complete);
    }
    Ok(())
}
#[test]
fn partial_population_includes_unknown_works() -> Result<(), AnalysisError> {
    let r = analyze(&common::request(&[Some(100), None, None]))?;
    assert_eq!((r.body.summary.h.lower, r.body.summary.h.upper), (1, 3));
    // g is capped at 3 actual works, not the one observed work.
    assert_eq!((r.body.summary.g.lower, r.body.summary.g.upper), (3, 3));
    assert_eq!((r.body.summary.i10.lower, r.body.summary.i10.upper), (1, 3));
    assert_eq!(r.body.summary.known_total, "100");
    assert_eq!(r.body.summary.total_upper, None);
    assert_eq!(r.body.summary.status, CitationStatus::Partial);
    Ok(())
}
#[test]
fn tight_h_upper_and_empty_unknown_distinction() -> Result<(), AnalysisError> {
    let r = analyze(&common::request(&[None, Some(0), Some(0)]))?;
    assert_eq!((r.body.summary.h.lower, r.body.summary.h.upper), (0, 1));
    assert_eq!(r.body.summary.g.upper, 3);
    let r = analyze(&common::request(&[None, None]))?;
    assert_eq!(r.body.summary.status, CitationStatus::Unavailable);
    assert_eq!(r.body.summary.h.upper, 2);
    let r = analyze(&common::request(&[]))?;
    assert_eq!(r.body.summary.status, CitationStatus::Complete);
    assert_eq!(r.body.summary.total_upper.as_deref(), Some("0"));
    Ok(())
}
#[test]
fn totals_exceeding_u64_are_exact() -> Result<(), AnalysisError> {
    let r = analyze(&common::request(&[Some(u64::MAX), Some(u64::MAX)]))?;
    assert_eq!(r.body.summary.known_total, "36893488147419103230");
    assert_eq!(r.body.summary.g.lower, 2);
    Ok(())
}
#[test]
fn reject_missing_and_duplicate_ids() {
    let mut r = common::request(&[None]);
    r.missing = MissingPolicy::Reject;
    assert!(matches!(analyze(&r), Err(AnalysisError::MissingCounts)));
    let mut r = common::request(&[Some(1), Some(2)]);
    r.observations[1].id = r.observations[0].id.clone();
    assert!(matches!(analyze(&r), Err(AnalysisError::DuplicateId)));
}
#[test]
fn metadata_validation() {
    let mut r = common::request(&[Some(1)]);
    r.source.sha256 = "A".repeat(64);
    assert!(analyze(&r).is_err());
    r.source.sha256 = "a".repeat(64);
    r.source.version = "latest".to_owned();
    assert!(analyze(&r).is_err());
    r.source.version = "1.0.0".to_owned();
    r.context.as_of = "2026-02-30T00:00:00Z".to_owned();
    assert!(analyze(&r).is_err());
}

#[derive(Deserialize)]
struct BoundsFixture {
    cases: Vec<BoundsCase>,
}

#[derive(Deserialize)]
struct BoundsCase {
    counts: Vec<Option<u64>>,
    lower: ThreeIndices,
    upper: ThreeIndices,
}

#[derive(Deserialize)]
struct ThreeIndices {
    h: u64,
    g: u64,
    i10: u64,
}

#[test]
fn independent_bounds_fixtures() -> Result<(), Box<dyn std::error::Error>> {
    let fixture: BoundsFixture =
        serde_json::from_str(include_str!("../../../verification/citation-bounds.json"))?;
    for case in fixture.cases {
        let result = analyze(&common::request(&case.counts))?;
        let s = &result.body.summary;
        assert_eq!(
            (s.h.lower, s.g.lower, s.i10.lower),
            (case.lower.h, case.lower.g, case.lower.i10)
        );
        assert_eq!(
            (s.h.upper, s.g.upper, s.i10.upper),
            (case.upper.h, case.upper.g, case.upper.i10)
        );
    }
    Ok(())
}

//! Property and metamorphic tests, separate from the independent known-answer fixtures.
mod common;
use citelattice_analysis::{analyze, CitationCount};
use proptest::prelude::*;

proptest! {
    #[test]
    fn indices_are_order_invariant_and_monotone(counts in prop::collection::vec(0_u64..1_000_000, 0..64)) {
        let values: Vec<_> = counts.iter().copied().map(Some).collect();
        let request = common::request(&values);
        let base = analyze(&request).map_err(|e| TestCaseError::fail(e.to_string()))?;
        let mut reordered = request.clone();
        reordered.observations.reverse();
        prop_assert_eq!(&base, &analyze(&reordered).map_err(|e| TestCaseError::fail(e.to_string()))?);
        prop_assert!(base.body.summary.h.lower <= base.body.summary.g.lower);
        prop_assert!(base.body.summary.g.lower <= base.body.summary.works);
        let mut increased = request;
        if let Some(first) = increased.observations.first_mut() {
            first.citations = Some(CitationCount(1_000_001));
            let next = analyze(&increased).map_err(|e| TestCaseError::fail(e.to_string()))?;
            prop_assert!(next.body.summary.h.lower >= base.body.summary.h.lower);
            prop_assert!(next.body.summary.g.lower >= base.body.summary.g.lower);
            prop_assert!(next.body.summary.i10.lower >= base.body.summary.i10.lower);
        }
    }

    #[test]
    fn actual_completion_is_inside_missing_count_bounds(counts in prop::collection::vec(0_u64..1000, 1..64)) {
        let values: Vec<_> = counts.iter().copied().map(Some).collect();
        let complete = analyze(&common::request(&values)).map_err(|e| TestCaseError::fail(e.to_string()))?;
        let masked: Vec<_> = values.into_iter().enumerate().map(|(i,v)| if i%2==0 { None } else { v }).collect();
        let partial = analyze(&common::request(&masked)).map_err(|e| TestCaseError::fail(e.to_string()))?;
        for (known, bounds) in [
            (complete.body.summary.h.lower, partial.body.summary.h),
            (complete.body.summary.g.lower, partial.body.summary.g),
            (complete.body.summary.i10.lower, partial.body.summary.i10),
        ] {
            prop_assert!(bounds.lower <= known);
            prop_assert!(known <= bounds.upper);
        }
    }
}

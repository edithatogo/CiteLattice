//! Small, independently specified network known-answer population.
use citelattice_network::{
    NetworkError, NetworkLimits, PaperReferences, ReferenceCoverage, analyze,
};

fn corpus() -> Vec<PaperReferences> {
    vec![
        PaperReferences {
            paper_id: "P1".into(),
            references: vec!["R1".into(), "R2".into()],
            coverage: ReferenceCoverage::Complete,
        },
        PaperReferences {
            paper_id: "P2".into(),
            references: vec!["R1".into(), "R2".into(), "P1".into()],
            coverage: ReferenceCoverage::Partial,
        },
        PaperReferences {
            paper_id: "P3".into(),
            references: vec!["R2".into(), "R3".into()],
            coverage: ReferenceCoverage::Complete,
        },
        PaperReferences {
            paper_id: "P4".into(),
            references: vec!["P2".into()],
            coverage: ReferenceCoverage::Unknown,
        },
    ]
}

#[test]
fn validated_network_projection_has_correct_known_edges() {
    let result = analyze(&corpus(), NetworkLimits::default()).unwrap();
    assert_eq!(result.direct.len(), 2);
    assert!(
        result
            .direct
            .iter()
            .any(|x| x.citing == "P2" && x.cited == "P1")
    );
    assert!(
        result
            .direct
            .iter()
            .any(|x| x.citing == "P4" && x.cited == "P2")
    );
    assert!(
        result
            .co_cited
            .iter()
            .any(|x| x.a == "R1" && x.b == "R2" && x.count == 2)
    );
    assert!(
        result
            .coupled
            .iter()
            .any(|x| x.a == "P1" && x.b == "P2" && x.count == 2)
    );
    assert_eq!(
        result
            .in_degree
            .iter()
            .find(|x| x.paper_id == "P1")
            .unwrap()
            .count,
        1
    );
    assert_eq!(result.completeness.partial, 1);
    assert_eq!(result.completeness.unknown, 1);
}

#[test]
fn input_order_and_duplicate_reference_order_do_not_change_results() {
    let input = corpus();
    let expected = analyze(&input, NetworkLimits::default()).unwrap();
    let mut altered = input.clone();
    altered.reverse();
    altered[3].references.reverse();
    altered[3].references.push("R1".into());
    let found = analyze(&altered, NetworkLimits::default()).unwrap();
    assert_eq!(expected.direct, found.direct);
    assert_eq!(expected.co_cited, found.co_cited);
    assert_eq!(expected.coupled, found.coupled);
    assert_eq!(expected.in_degree, found.in_degree);
}

#[test]
fn invalid_population_and_pair_expansion_are_rejected() {
    let mut duplicate = corpus();
    duplicate.push(duplicate[0].clone());
    assert!(matches!(
        analyze(&duplicate, NetworkLimits::default()),
        Err(NetworkError::DuplicatePaper)
    ));
    let tiny = NetworkLimits {
        max_papers: 10,
        max_references_per_paper: 10,
        max_pair_operations: 1,
    };
    assert!(matches!(
        analyze(&corpus(), tiny),
        Err(NetworkError::PairBudget)
    ));
}

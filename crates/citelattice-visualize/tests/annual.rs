//! Evidence-linked annual visualisation invariants and negative conditions.
use std::io::Cursor;

use citelattice_ingest::{AnnualCount, ExportApproval, PublicationSummary, SourceLimits, summarize_reader};
use citelattice_visualize::{SceneError, SceneLimits, build_annual_scene};

fn source() -> PublicationSummary {
    let jsonl = include_str!("../../../examples/searchright/native-records.jsonl");
    summarize_reader(Cursor::new(jsonl.as_bytes()), SourceLimits::default()).unwrap()
}

#[test]
fn every_authoritative_annual_row_is_traced_by_one_scene_mark() {
    let mut summary = source();
    summary.annual = (2000..2017).map(|year| AnnualCount { year, count: 1 }).collect();
    summary.record_count = 17;
    summary.undated = 0;
    let output = build_annual_scene(&summary, ExportApproval::Allowed, SceneLimits::default())
        .unwrap();
    assert_eq!(output.scene.marks.len(), 17);
    assert_eq!(output.svg.matches("<rect ").count(), 17);
    assert_eq!(output.accessible_rows, summary.annual);
    assert!(output.svg.contains("data-row-key=\"2016\""));
    assert!(output.scene.marks.iter().any(|mark| mark.row_keys == vec!["2016"]));
    assert_eq!(
        output.vega_lite["data"]["values"].as_array().unwrap().len(), 17
    );
    assert_eq!(
        output.receipt.scene.sha256,
        output.scene.scene.sha256
    );
    assert_eq!(output.receipt.output.sha256.len(), 64);
}

#[test]
fn an_unrepresentable_count_is_not_rounded_for_browser_rendering() {
    let mut summary = source();
    summary.annual[0].count = u64::MAX;
    assert!(matches!(
        build_annual_scene(&summary, ExportApproval::Allowed, SceneLimits::default()),
        Err(SceneError::Precision)
    ));
}

#[test]
fn tampered_counts_and_duplicate_years_are_rejected() {
    let mut summary = source();
    summary.annual[0].count = 1;
    assert!(matches!(
        build_annual_scene(&summary, ExportApproval::Allowed, SceneLimits::default()),
        Err(SceneError::InconsistentTable)
    ));
    summary.annual = vec![AnnualCount { year: 2024, count: 1 }, AnnualCount { year: 2024, count: 1 }];
    assert!(matches!(
        build_annual_scene(&summary, ExportApproval::Allowed, SceneLimits::default()),
        Err(SceneError::InconsistentTable)
    ));
}

#[test]
fn denied_or_budget_exhausted_rendering_is_side_effect_free() {
    let summary = source();
    assert!(matches!(
        build_annual_scene(&summary, ExportApproval::Denied, SceneLimits::default()),
        Err(SceneError::Denied)
    ));
    assert!(matches!(
        build_annual_scene(&summary, ExportApproval::Allowed, SceneLimits { max_bars: 0 }),
        Err(SceneError::TooManyMarks)
    ));
}

#[test]
fn identical_numeric_geometry_can_have_distinct_source_lineage() {
    let original = source();
    let first = build_annual_scene(
        &original, ExportApproval::Allowed, SceneLimits::default()
    ).unwrap();
    let mut new_source = original;
    new_source.input_sha256 = "b".repeat(64);
    let second = build_annual_scene(
        &new_source, ExportApproval::Allowed, SceneLimits::default()
    ).unwrap();
    assert_ne!(first.scene.scene.sha256, second.scene.scene.sha256);
    assert_eq!(first.svg, second.svg);
    assert_eq!(first.receipt.output.sha256, second.receipt.output.sha256);
}

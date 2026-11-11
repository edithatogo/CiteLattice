//! Executable consumer contract against Searchright native JSONL export shape.
use citelattice_ingest::{
    ExportApproval, SourceError, SourceLimits, summarize_reader, write_outputs,
};
use std::io::Cursor;

const FIXTURE: &str = include_str!("../../../examples/searchright/native-records.jsonl");

#[test]
fn native_searchright_records_produce_descriptive_and_network_baselines() {
    let s = summarize_reader(Cursor::new(FIXTURE.as_bytes()), SourceLimits::default()).unwrap();
    assert_eq!(s.record_count, 3);
    assert_eq!(s.annual.len(), 1);
    assert_eq!(s.annual[0].year, 2024);
    assert_eq!(s.annual[0].count, 2);
    assert_eq!(s.undated, 1);
    assert_eq!(s.coauthors.len(), 2);
    assert!(
        s.coauthors
            .iter()
            .any(|e| e.a == "Ada Example" && e.b == "Ben Example" && e.works == 1)
    );
    assert!(
        s.coauthors
            .iter()
            .any(|e| e.a == "Ben Example" && e.b == "Cara Example" && e.works == 1)
    );
    assert_eq!(s.source_receipts.len(), 2);
    assert_eq!(s.schema_version, "org.citelattice.searchright-summary.v1");
}

#[test]
fn invalid_and_duplicate_records_fail_closed() {
    let bad = FIXTURE.replacen("org.searchright.bibliographic-record.v1", "bad.version", 1);
    assert!(matches!(
        summarize_reader(Cursor::new(bad.as_bytes()), SourceLimits::default()),
        Err(SourceError::InvalidContract(_))
    ));
    let doubled = format!("{FIXTURE}{}", FIXTURE.lines().next().unwrap());
    assert!(matches!(
        summarize_reader(Cursor::new(doubled.as_bytes()), SourceLimits::default()),
        Err(SourceError::Duplicate(_))
    ));
    let limit = SourceLimits {
        max_line_bytes: 16,
        max_records: 10,
    };
    assert!(matches!(
        summarize_reader(Cursor::new(FIXTURE.as_bytes()), limit),
        Err(SourceError::TooLarge)
    ));
}

#[test]
fn outputs_are_denied_without_positive_export_approval() {
    let s = summarize_reader(Cursor::new(FIXTURE.as_bytes()), SourceLimits::default()).unwrap();
    let dir = std::env::temp_dir().join(format!("citelattice-test-denied-{}", std::process::id()));
    assert!(write_outputs(&s, &dir, ExportApproval::Denied).is_err());
    assert!(!dir.exists());
}

#[test]
fn csv_svg_html_and_provenance_share_the_same_annual_table() {
    let s = summarize_reader(Cursor::new(FIXTURE.as_bytes()), SourceLimits::default()).unwrap();
    let dir = std::env::temp_dir().join(format!("citelattice-test-allowed-{}", std::process::id()));
    if dir.exists() {
        std::fs::remove_dir_all(&dir).unwrap();
    }
    let manifest = write_outputs(&s, &dir, ExportApproval::Allowed).unwrap();
    let csv = std::fs::read_to_string(dir.join("annual.csv")).unwrap();
    let svg = std::fs::read_to_string(dir.join("annual.svg")).unwrap();
    let html = std::fs::read_to_string(dir.join("annual.html")).unwrap();
    assert_eq!(csv, "year,publications\n2024,2\n");
    assert!(svg.contains("2024") && svg.contains('>'));
    assert!(html.contains("<td>2024</td><td>2</td>"));
    assert!(manifest.assets.iter().any(|a| a.path == "annual.csv"));
    assert!(dir.join("ro-crate-metadata.json").is_file());
    std::fs::remove_dir_all(dir).unwrap();
}

#[test]
fn svg_shows_all_years_without_silent_truncation() {
    let mut summary =
        summarize_reader(Cursor::new(FIXTURE.as_bytes()), SourceLimits::default()).unwrap();
    summary.annual = (2000..2017)
        .map(|year| citelattice_ingest::AnnualCount { year, count: 1 })
        .collect();
    let dir = std::env::temp_dir().join(format!("citelattice-years-{}", std::process::id()));
    if dir.exists() {
        std::fs::remove_dir_all(&dir).unwrap();
    }
    write_outputs(&summary, &dir, ExportApproval::Allowed).unwrap();
    let svg = std::fs::read_to_string(dir.join("annual.svg")).unwrap();
    assert_eq!(svg.matches("<rect ").count(), 17);
    assert!(svg.contains(">2016</text>"));
    std::fs::remove_dir_all(dir).unwrap();
}

#[test]
fn svg_handles_maximum_u64_count_without_arithmetic_overflow() {
    let mut summary =
        summarize_reader(Cursor::new(FIXTURE.as_bytes()), SourceLimits::default()).unwrap();
    summary.annual[0].count = u64::MAX;
    let dir = std::env::temp_dir().join(format!("citelattice-maxbars-{}", std::process::id()));
    if dir.exists() {
        std::fs::remove_dir_all(&dir).unwrap();
    }
    write_outputs(&summary, &dir, ExportApproval::Allowed).unwrap();
    let svg = std::fs::read_to_string(dir.join("annual.svg")).unwrap();
    assert!(svg.contains("18446744073709551615"));
    std::fs::remove_dir_all(dir).unwrap();
}

#[test]
fn oversized_author_list_is_rejected_before_pairwise_expansion() {
    let mut record: serde_json::Value =
        serde_json::from_str(FIXTURE.lines().next().unwrap()).unwrap();
    record["authors"] = serde_json::json!(
        (0..257).map(|i| format!("Author {i:03}")).collect::<Vec<_>>()
    );
    let input = serde_json::to_string(&record).unwrap();
    assert!(matches!(
        summarize_reader(Cursor::new(input.as_bytes()), SourceLimits::default()),
        Err(SourceError::TooManyAuthors)
    ));
}

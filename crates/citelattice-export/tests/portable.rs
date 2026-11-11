//! Independent table, workbook and reproducibility contract tests.
use std::fs::File;
use std::io::Cursor;

use citelattice_export::{ExportFormat, write_extended};
use citelattice_ingest::{ExportApproval, SourceLimits, summarize_reader};
use parquet::arrow::arrow_reader::ParquetRecordBatchReaderBuilder;

fn summary() -> citelattice_ingest::PublicationSummary {
    let data = include_str!("../../../examples/searchright/native-records.jsonl");
    summarize_reader(Cursor::new(data.as_bytes()), SourceLimits::default()).expect("source fixture")
}

#[test]
fn parquet_roundtrip_uses_exact_typed_annual_rows() -> Result<(), Box<dyn std::error::Error>> {
    let dir = tempfile::tempdir()?;
    let report = write_extended(&summary(), dir.path(), ExportApproval::Allowed)?;
    assert!(
        report
            .assets
            .iter()
            .any(|a| a.format == ExportFormat::Parquet)
    );
    let file = File::open(dir.path().join("annual.parquet"))?;
    let builder = ParquetRecordBatchReaderBuilder::try_new(file)?;
    let mut reader = builder.build()?;
    let batch = reader.next().ok_or("no batch")??;
    assert_eq!(batch.num_rows(), 1);
    assert_eq!(batch.schema().field(0).name(), "year");
    assert_eq!(batch.schema().field(1).name(), "publications");
    let count = batch
        .column(1)
        .as_any()
        .downcast_ref::<arrow_array::UInt64Array>()
        .ok_or("count type")?;
    assert_eq!(count.value(0), 2);
    Ok(())
}

#[test]
fn workbook_and_report_source_are_derived_from_the_same_rows()
-> Result<(), Box<dyn std::error::Error>> {
    let dir = tempfile::tempdir()?;
    let report = write_extended(&summary(), dir.path(), ExportApproval::Allowed)?;
    assert!(report.assets.iter().any(|a| a.format == ExportFormat::Xlsx));
    assert!(std::fs::read(dir.path().join("analysis.xlsx"))?.starts_with(b"PK"));
    let typst = std::fs::read_to_string(dir.path().join("report.typ"))?;
    assert!(typst.contains("[2024], [2]"));
    assert!(
        report
            .assets
            .iter()
            .any(|a| a.format == ExportFormat::TypstSource)
    );
    assert!(report.output_manifest.is_file());
    Ok(())
}

#[test]
fn denied_export_is_side_effect_free() -> Result<(), Box<dyn std::error::Error>> {
    let dir = tempfile::tempdir()?;
    let destination = dir.path().join("not-created");
    assert!(write_extended(&summary(), &destination, ExportApproval::Denied).is_err());
    assert!(!destination.exists());
    Ok(())
}

#[test]
fn transactional_export_publishes_verified_assets() -> Result<(), Box<dyn std::error::Error>> {
    use sha2::{Digest, Sha256};
    let parent = tempfile::tempdir()?;
    let destination = parent.path().join("complete");
    let receipt = citelattice_export::write_extended_transactional(
        &summary(), &destination, ExportApproval::Allowed,
    )?;
    assert_eq!(receipt.output_manifest, destination.join("extended-manifest.json"));
    assert!(receipt.output_manifest.is_file());
    for asset in &receipt.assets {
        let bytes = std::fs::read(destination.join(&asset.path))?;
        assert_eq!(asset.sha256, hex::encode(Sha256::digest(&bytes)));
    }
    let on_disk: citelattice_export::ExportReceipt =
        serde_json::from_slice(&std::fs::read(&receipt.output_manifest)?)?;
    assert_eq!(on_disk.output_manifest, receipt.output_manifest);
    Ok(())
}

#[test]
fn transactional_export_denied_and_missing_parent_leave_no_package(
) -> Result<(), Box<dyn std::error::Error>> {
    let parent = tempfile::tempdir()?;
    let denied = parent.path().join("denied");
    assert!(citelattice_export::write_extended_transactional(
        &summary(), &denied, ExportApproval::Denied,
    ).is_err());
    assert!(!denied.exists());
    let missing = parent.path().join("absent").join("package");
    assert!(citelattice_export::write_extended_transactional(
        &summary(), &missing, ExportApproval::Allowed,
    ).is_err());
    assert!(!missing.exists());
    Ok(())
}

#[test]
fn transactional_export_refuses_overwriting_existing_package(
) -> Result<(), Box<dyn std::error::Error>> {
    let parent = tempfile::tempdir()?;
    let destination = parent.path().join("existing");
    std::fs::create_dir(&destination)?;
    let sentinel = destination.join("do-not-touch");
    std::fs::write(&sentinel, b"unchanged")?;
    assert!(matches!(
        citelattice_export::write_extended_transactional(
            &summary(), &destination, ExportApproval::Allowed
        ),
        Err(citelattice_export::ExportError::DestinationExists)
    ));
    assert_eq!(std::fs::read(&sentinel)?, b"unchanged");
    Ok(())
}

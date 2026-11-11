//! Independent table, workbook and reproducibility contract tests.
use std::io::Cursor;
use std::fs::File;

use citelattice_export::{write_extended, ExportFormat};
use citelattice_ingest::{summarize_reader, ExportApproval, SourceLimits};
use parquet::arrow::arrow_reader::ParquetRecordBatchReaderBuilder;

fn summary() -> citelattice_ingest::PublicationSummary {
    let data = include_str!("../../../examples/searchright/native-records.jsonl");
    summarize_reader(Cursor::new(data.as_bytes()), SourceLimits::default()).expect("source fixture")
}

#[test]
fn parquet_roundtrip_uses_exact_typed_annual_rows() -> Result<(), Box<dyn std::error::Error>> {
    let dir = tempfile::tempdir()?;
    let report = write_extended(&summary(), dir.path(), ExportApproval::Allowed)?;
    assert!(report.assets.iter().any(|a| a.format == ExportFormat::Parquet));
    let file = File::open(dir.path().join("annual.parquet"))?;
    let builder = ParquetRecordBatchReaderBuilder::try_new(file)?;
    let mut reader = builder.build()?;
    let batch = reader.next().ok_or("no batch")??;
    assert_eq!(batch.num_rows(), 1);
    assert_eq!(batch.schema().field(0).name(), "year");
    assert_eq!(batch.schema().field(1).name(), "publications");
    let count = batch.column(1).as_any().downcast_ref::<arrow_array::UInt64Array>().ok_or("count type")?;
    assert_eq!(count.value(0), 2);
    Ok(())
}

#[test]
fn workbook_and_report_source_are_derived_from_the_same_rows() -> Result<(), Box<dyn std::error::Error>> {
    let dir = tempfile::tempdir()?;
    let report = write_extended(&summary(), dir.path(), ExportApproval::Allowed)?;
    assert!(report.assets.iter().any(|a| a.format == ExportFormat::Xlsx));
    assert!(std::fs::read(dir.path().join("analysis.xlsx"))?.starts_with(b"PK"));
    let typst = std::fs::read_to_string(dir.path().join("report.typ"))?;
    assert!(typst.contains("2024") && typst.contains("2"));
    assert!(report.assets.iter().any(|a| a.format == ExportFormat::TypstSource));
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

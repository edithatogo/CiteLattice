//! Result-table, figure, workbook and research-object packaging contracts.
use super::versioning::{OutputLineage, Revision};
use serde::{Deserialize, Serialize};

/// Physical interchange format with a declared semantic completeness policy.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ExchangeFormat {
    /// Canonical Citation Style Language JSON bibliographic item.
    CslJson,
    /// Searchright/CiteLattice versioned event JSON lines.
    JsonLines,
    /// Arrow IPC streaming/file format with Arrow schema metadata.
    ArrowIpc,
    /// Columnar Parquet with explicit logical types and field metadata.
    Parquet,
    /// Flattened CSV; losses and null conventions must be declared.
    Csv,
    /// Network export for tools outside Rust.
    GraphMl,
    /// Alternative graph exchange representation.
    Gexf,
    /// Declarative statistical graphics specification.
    VegaLite,
    /// Evidence-linked `CiteLattice` scene JSON.
    EvidenceScene,
    /// Scalable vector figure.
    Svg,
    /// Raster image suitable for publication and accessible alternatives.
    Png,
    /// Accessible interactive document.
    Html,
    /// Scientific workbook, not the canonical data store.
    Xlsx,
    /// Typst-created PDF document.
    Pdf,
    /// RO-Crate JSON-LD research package metadata.
    RoCrate,
}

/// Machine-readable table contract underlying metrics, figures and reports.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct TableContract {
    /// Exact Arrow schema fingerprint, including nullability and metadata.
    pub schema: Revision,
    /// Authoritative object digest, including rows in deterministic order.
    pub data_sha256: String,
    /// Row identity fields, including compound keys.
    pub primary_key: Vec<String>,
    /// Conventions for measurement units, dimensionless indicators and dates.
    pub units: Vec<(String, String)>,
    /// Missing is not zero: explicit null/not-applicable/withheld conventions.
    pub missingness_policy: String,
    /// Exact scientific and source lineage.
    pub lineage: OutputLineage,
    /// Allowed disclosures for all columns and derived labels.
    pub rights_policy: Revision,
}

/// Workbook sheet is a view over an existing table, not a second calculation.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct WorkbookSheet {
    /// User-facing sheet name, within XLSX constraints.
    pub name: String,
    /// Exact referenced table artifact.
    pub table: Revision,
    /// Range and column selection policy.
    pub view: String,
    /// Explicit row limit/truncation marker; never silently truncate.
    pub row_limit: Option<u64>,
    /// Figure references with artifact digests.
    pub figures: Vec<Revision>,
}

/// Self-contained export manifest, with missing or restricted assets listed.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ResearchBundle {
    /// RO-Crate 1.3 metadata artifact (separately validated).
    pub ro_crate: Revision,
    /// Table, scene, render, workbook, report and source artifacts.
    pub assets: Vec<Revision>,
    /// Assets excluded because of rights or availability restrictions.
    pub withheld: Vec<String>,
    /// Exact manifest revision and content identity.
    pub manifest: Revision,
}

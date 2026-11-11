//! Bounded, deterministic analysis of Searchright's existing bibliographic JSONL.
//!
//! This adapter consumes actual Searchright `BibliographicRecord` JSONL exports.
//! It does not claim support for the proposed revision/event envelope, complete
//! citation graphs, or name-disambiguated collaboration.
#![forbid(unsafe_code)]
use std::collections::{BTreeMap, BTreeSet};
use std::io::{BufRead, Read};
use std::path::Path;

use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

/// Searchright's native bibliographic-record schema identifier.
pub const SOURCE_SCHEMA: &str = "org.searchright.bibliographic-record.v1";
/// CiteLattice's descriptive-output contract identifier.
pub const RESULT_SCHEMA: &str = "org.citelattice.searchright-summary.v1";

/// Bounded input limits for independent native JSONL exports.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct SourceLimits {
    /// Maximum bytes for one line, including newline.
    pub max_line_bytes: usize,
    /// Maximum distinct publications admitted per run.
    pub max_records: usize,
}
impl Default for SourceLimits {
    fn default() -> Self {
        Self {
            max_line_bytes: 2_097_152,
            max_records: 100_000,
        }
    }
}

/// Errors are redacted: they never contain source titles or abstracts.
#[derive(Debug, thiserror::Error)]
pub enum SourceError {
    /// Input I/O failed.
    #[error("source input failed")]
    Io,
    /// Line exceeds the configured limit.
    #[error("source line too large")]
    TooLarge,
    /// Too many records were supplied.
    #[error("source record limit exceeded")]
    TooMany,
    /// The native record did not satisfy its supported contract.
    #[error("invalid native Searchright contract at line {0}")]
    InvalidContract(usize),
    /// A source record identity was repeated.
    #[error("duplicate record identity at line {0}")]
    Duplicate(usize),
    /// An exact metric count exceeded its permitted type.
    #[error("count overflow")]
    Overflow,
}

/// Export permission is explicitly supplied by a trusted caller.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ExportApproval {
    /// Derived export is explicitly permitted.
    Allowed,
    /// Derived export must not be written.
    Denied,
}

/// Public output errors intentionally exclude restricted bibliographic strings.
#[derive(Debug, thiserror::Error)]
pub enum OutputError {
    /// Export was not authorised.
    #[error("derived export is not authorised")]
    Denied,
    /// Output filesystem or encoding failed.
    #[error("output operation failed")]
    Write,
}

/// Year and exact paper count.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct AnnualCount {
    /// Publication year as reported by the producer.
    pub year: i32,
    /// Number of supplied reports in that year.
    pub count: u64,
}

/// Document-kind count under Searchright's provider-normalised vocabulary.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct KindCount {
    /// Searchright document-type label.
    pub kind: String,
    /// Count within the supplied stream.
    pub count: u64,
}

/// Coauthorship by exact raw author strings, without identity unification.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CollaborationEdge {
    /// Alphabetically lower source author string.
    pub a: String,
    /// Alphabetically higher source author string.
    pub b: String,
    /// Number of unique supplied works featuring both strings.
    pub works: u64,
}

/// Complete scoped descriptive result; no claim about global source coverage.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct PublicationSummary {
    /// Result schema identifier.
    pub schema_version: String,
    /// Input producer schema identifier.
    pub source_schema_version: String,
    /// SHA-256 of the exact source JSONL stream bytes.
    pub input_sha256: String,
    /// Number of unique supplied records.
    pub record_count: u64,
    /// Reports lacking a publication year.
    pub undated: u64,
    /// Authoritative annual production table.
    pub annual: Vec<AnnualCount>,
    /// Breakdown of document types.
    pub document_types: Vec<KindCount>,
    /// Raw exact-name coauthorship edges, explicitly unresolved identities.
    pub coauthors: Vec<CollaborationEdge>,
    /// Source receipt identities from the input.
    pub source_receipts: Vec<String>,
    /// This indicates that distinct strings may refer to the same person.
    pub author_resolution: String,
}

/// Assets in the emitted evidence package.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Artifact {
    /// Relative package path.
    pub path: String,
    /// SHA-256 of exact bytes.
    pub sha256: String,
    /// Media type.
    pub media_type: String,
}

/// Export result; the RO-Crate document is an independently verifiable subset.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ArtifactManifest {
    /// Exact source bytes digest.
    pub input_sha256: String,
    /// Output artifact digests, not including self-referential metadata.
    pub assets: Vec<Artifact>,
}

#[derive(Deserialize)]
struct NativeRecord {
    schema_version: String,
    record_id: String,
    source_receipt_id: String,
    native_id: String,
    title: String,
    kind: serde_json::Value,
    publication_year: Option<i32>,
    #[serde(default)]
    authors: Vec<String>,
}

fn nonempty(value: &str) -> bool {
    !value.trim().is_empty() && value.trim() == value && !value.chars().any(char::is_control)
}

fn document_kind(value: &serde_json::Value) -> Option<String> {
    value
        .as_str()
        .map(str::to_owned)
        .or_else(|| {
            value
                .as_object()
                .and_then(|obj| obj.get("other"))?
                .as_str()
                .map(str::to_owned)
        })
        .filter(|kind| nonempty(kind))
}

/// Parse a bounded genuine Searchright JSONL file into scoped descriptive statistics.
///
/// # Errors
/// Rejects malformed or mismatched records, duplicate identities, oversize input
/// and count overflow. Missing publication years remain explicitly undated.
pub fn summarize_reader<R: BufRead>(
    mut reader: R,
    limits: SourceLimits,
) -> Result<PublicationSummary, SourceError> {
    if limits.max_line_bytes == 0 || limits.max_records == 0 {
        return Err(SourceError::TooLarge);
    }
    let probe = u64::try_from(
        limits
            .max_line_bytes
            .checked_add(1)
            .ok_or(SourceError::TooLarge)?,
    )
    .map_err(|_| SourceError::TooLarge)?;
    let mut bytes = Vec::new();
    let mut digest = Sha256::new();
    let mut annual = BTreeMap::<i32, u64>::new();
    let mut kinds = BTreeMap::<String, u64>::new();
    let mut edges = BTreeMap::<(String, String), u64>::new();
    let mut receipts = BTreeSet::new();
    let mut seen = BTreeSet::new();
    let mut undated = 0_u64;
    let mut record_count = 0_u64;
    let mut line = 0_usize;
    loop {
        bytes.clear();
        let count = (&mut reader)
            .take(probe)
            .read_until(b'\n', &mut bytes)
            .map_err(|_| SourceError::Io)?;
        if count == 0 {
            break;
        }
        line = line.checked_add(1).ok_or(SourceError::Overflow)?;
        if count > limits.max_line_bytes {
            return Err(SourceError::TooLarge);
        }
        digest.update(&bytes);
        if bytes.iter().all(u8::is_ascii_whitespace) {
            continue;
        }
        if seen.len() >= limits.max_records {
            return Err(SourceError::TooMany);
        }
        let record: NativeRecord =
            serde_json::from_slice(&bytes).map_err(|_| SourceError::InvalidContract(line))?;
        if record.schema_version != SOURCE_SCHEMA
            || !nonempty(&record.record_id)
            || !nonempty(&record.source_receipt_id)
            || !nonempty(&record.native_id)
            || !nonempty(&record.title)
            || record.authors.iter().any(|name| !nonempty(name))
            || document_kind(&record.kind).is_none()
        {
            return Err(SourceError::InvalidContract(line));
        }
        if !seen.insert(record.record_id) {
            return Err(SourceError::Duplicate(line));
        }
        record_count = record_count.checked_add(1).ok_or(SourceError::Overflow)?;
        receipts.insert(record.source_receipt_id);
        if let Some(year) = record.publication_year {
            *annual.entry(year).or_default() += 1;
        } else {
            undated += 1;
        }
        let kind = document_kind(&record.kind).ok_or(SourceError::InvalidContract(line))?;
        *kinds.entry(kind).or_default() += 1;
        let distinct: Vec<String> = record
            .authors
            .into_iter()
            .collect::<BTreeSet<_>>()
            .into_iter()
            .collect();
        for (i, a) in distinct.iter().enumerate() {
            for b in distinct.iter().skip(i + 1) {
                *edges.entry((a.clone(), b.clone())).or_default() += 1;
            }
        }
    }
    Ok(PublicationSummary {
        schema_version: RESULT_SCHEMA.to_owned(),
        source_schema_version: SOURCE_SCHEMA.to_owned(),
        input_sha256: hex::encode(digest.finalize()),
        record_count,
        undated,
        annual: annual
            .into_iter()
            .map(|(year, count)| AnnualCount { year, count })
            .collect(),
        document_types: kinds
            .into_iter()
            .map(|(kind, count)| KindCount { kind, count })
            .collect(),
        coauthors: edges
            .into_iter()
            .map(|((a, b), works)| CollaborationEdge { a, b, works })
            .collect(),
        source_receipts: receipts.into_iter().collect(),
        author_resolution: "exact_source_strings_not_disambiguated".to_owned(),
    })
}

fn annual_csv(summary: &PublicationSummary) -> String {
    let mut out = String::from("year,publications\n");
    for row in &summary.annual {
        out.push_str(&format!("{},{}\n", row.year, row.count));
    }
    out
}

fn annual_svg(summary: &PublicationSummary) -> String {
    let largest = summary
        .annual
        .iter()
        .map(|r| r.count)
        .max()
        .unwrap_or(1)
        .max(1);
    let mut s = String::from(
        "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 640 400\" role=\"img\" aria-label=\"Publications by year\"><title>Publications by year</title>",
    );
    for (index, row) in summary.annual.iter().take(16).enumerate() {
        let x = 30 + index * 37;
        let height = row.count * 280 / largest;
        let y = 330 - height;
        s.push_str(&format!("<rect x=\"{x}\" y=\"{y}\" width=\"26\" height=\"{height}\" fill=\"#465f82\"/><text x=\"{x}\" y=\"350\" font-size=\"9\">{}</text><text x=\"{x}\" y=\"{}\" font-size=\"9\">{}</text>", row.year, y.saturating_sub(5), row.count));
    }
    s.push_str("</svg>");
    s
}

fn annual_html(summary: &PublicationSummary) -> String {
    let mut s = String::from(
        "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\"><meta http-equiv=\"Content-Security-Policy\" content=\"default-src 'none'; style-src 'unsafe-inline'\"><title>Annual publication production</title></head><body><h1>Annual publication production</h1><table><caption>Works grouped by reported publication year</caption><thead><tr><th>Year</th><th>Publications</th></tr></thead><tbody>",
    );
    for row in &summary.annual {
        s.push_str(&format!(
            "<tr><td>{}</td><td>{}</td></tr>",
            row.year, row.count
        ));
    }
    s.push_str("</tbody></table></body></html>");
    s
}

fn digest(bytes: &[u8]) -> String {
    hex::encode(Sha256::digest(bytes))
}

/// Write JSON, CSV, static SVG, accessible HTML and RO-Crate metadata from one table.
///
/// # Errors
/// Denied export does not create a directory. Filesystem/serialization errors
/// are reported without source text. A separate rights verification remains the
/// caller's responsibility; output is not written atomically across files.
pub fn write_outputs(
    summary: &PublicationSummary,
    directory: &Path,
    permission: ExportApproval,
) -> Result<ArtifactManifest, OutputError> {
    if permission != ExportApproval::Allowed {
        return Err(OutputError::Denied);
    }
    std::fs::create_dir_all(directory).map_err(|_| OutputError::Write)?;
    let summary_json = serde_json::to_vec_pretty(summary).map_err(|_| OutputError::Write)?;
    let assets = [
        ("summary.json", summary_json, "application/json"),
        ("annual.csv", annual_csv(summary).into_bytes(), "text/csv"),
        (
            "annual.svg",
            annual_svg(summary).into_bytes(),
            "image/svg+xml",
        ),
        (
            "annual.html",
            annual_html(summary).into_bytes(),
            "text/html",
        ),
    ];
    let mut records = Vec::new();
    for (path, bytes, media_type) in assets {
        std::fs::write(directory.join(path), &bytes).map_err(|_| OutputError::Write)?;
        records.push(Artifact {
            path: path.to_owned(),
            sha256: digest(&bytes),
            media_type: media_type.to_owned(),
        });
    }
    let manifest = ArtifactManifest {
        input_sha256: summary.input_sha256.clone(),
        assets: records,
    };
    let parts: Vec<_> = manifest
        .assets
        .iter()
        .map(|a| {
            serde_json::json!({
                "@id": a.path,
                "@type": "File",
                "encodingFormat": a.media_type,
                "sha256": a.sha256
            })
        })
        .collect();
    let doc = serde_json::json!({
        "@context": "https://w3id.org/ro/crate/1.3/context",
        "@graph": [
            {"@id": "ro-crate-metadata.json", "@type": "CreativeWork", "about": {"@id": "./"}},
            {"@id": "./", "@type": "Dataset", "name": "CiteLattice scoped publication summary",
             "conformsTo": {"@id": "https://w3id.org/ro/crate/1.3"},
             "hasPart": manifest.assets.iter().map(|a| serde_json::json!({"@id":a.path})).collect::<Vec<_>>(),
             "description": "Source-corpus descriptive statistics, not global scientometric coverage.",
             "sourceInputSha256": summary.input_sha256}
        ].into_iter().chain(parts).collect::<Vec<_>>()
    });
    std::fs::write(
        directory.join("ro-crate-metadata.json"),
        serde_json::to_vec_pretty(&doc).map_err(|_| OutputError::Write)?,
    )
    .map_err(|_| OutputError::Write)?;
    Ok(manifest)
}

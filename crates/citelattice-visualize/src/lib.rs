//! Evidence-linked, precise and bounded annual publication visualisations.
//! Scientific scene identity and static rendering are independently versioned.
#![forbid(unsafe_code)]

use std::fmt::Write as _;

use citelattice_core::contracts::imaging::{
    EvidenceMark, EvidenceSceneContract, RenderReceiptContract, UncertaintyKind,
};
use citelattice_core::contracts::versioning::Revision;
use citelattice_ingest::{AnnualCount, ExportApproval, PublicationSummary, RESULT_SCHEMA};
use serde::Serialize;
use serde_json::{Value, json};
use sha2::{Digest as _, Sha256};

/// Maximum number of marks in one directly rendered annual chart.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct SceneLimits {
    /// Caller-specified maximum, additionally capped at 512 marks.
    pub max_bars: usize,
}

impl Default for SceneLimits {
    fn default() -> Self {
        Self { max_bars: 512 }
    }
}

/// Errors are independent of untrusted bibliographic text.
#[derive(Debug, thiserror::Error)]
pub enum SceneError {
    /// Derived visualisation is not authorised.
    #[error("scientific scene export is not authorised")]
    Denied,
    /// Source summary is not a consistent authoritative annual table.
    #[error("scientific annual table is inconsistent")]
    InconsistentTable,
    /// Source values cannot be represented without silently rounding browser data.
    #[error("a scientific count is not exactly representable")]
    Precision,
    /// Too many annual marks for direct rendering; aggregation requires provenance.
    #[error("annual visualisation exceeds mark budget")]
    TooManyMarks,
    /// Canonical serialization failed.
    #[error("scientific scene encoding failed")]
    Encoding,
}

/// Data-preserving view over the supplied annual counts with verifiable receipts.
#[derive(Debug, Clone, Serialize)]
pub struct AnnualScene {
    /// Evidence-linkage contract for each quantitative mark.
    pub scene: EvidenceSceneContract,
    /// Vega-Lite v5 source specification; external renderer not claimed.
    pub vega_lite: Value,
    /// Offline self-contained static SVG with source-row keys.
    pub svg: String,
    /// Recorded renderer and artifact identities; self-check is not independent audit.
    pub receipt: RenderReceiptContract,
    /// Accessible, exact integer data underlying every mark.
    pub accessible_rows: Vec<AnnualCount>,
}

fn sha256(bytes: &[u8]) -> String {
    hex::encode(Sha256::digest(bytes))
}

fn hash_canonical<T: Serialize>(value: &T) -> Result<String, SceneError> {
    let canonical = serde_json_canonicalizer::to_vec(value).map_err(|_| SceneError::Encoding)?;
    Ok(sha256(&canonical))
}

fn revision(id: &str, version: &str, digest: String) -> Revision {
    Revision {
        id: id.to_owned(),
        version: version.to_owned(),
        sha256: digest,
    }
}

fn verify_table(summary: &PublicationSummary, limits: SceneLimits) -> Result<(), SceneError> {
    const SAFE_INTEGER: u64 = 9_007_199_254_740_991;
    if summary.annual.len() > limits.max_bars || summary.annual.len() > 512 {
        return Err(SceneError::TooManyMarks);
    }
    // Perform the precision check before conservation, so a large count does
    // not disappear behind an unrelated table-count mismatch.
    if summary.annual.iter().any(|row| row.count > SAFE_INTEGER) {
        return Err(SceneError::Precision);
    }
    if summary.schema_version != RESULT_SCHEMA
        || summary.input_sha256.len() != 64
        || !summary.input_sha256.bytes().all(|c| c.is_ascii_hexdigit() && !c.is_ascii_uppercase())
        || summary.undated > summary.record_count
    {
        return Err(SceneError::InconsistentTable);
    }
    let mut previous = None;
    let mut total = 0_u128;
    for row in &summary.annual {
        if previous.is_some_and(|year| row.year <= year) {
            return Err(SceneError::InconsistentTable);
        }
        previous = Some(row.year);
        total = total
            .checked_add(u128::from(row.count))
            .ok_or(SceneError::InconsistentTable)?;
    }
    if total != u128::from(summary.record_count - summary.undated) {
        return Err(SceneError::InconsistentTable);
    }
    Ok(())
}

fn table_revision(summary: &PublicationSummary) -> Result<Revision, SceneError> {
    #[derive(Serialize)]
    struct Table<'a> {
        source_schema: &'a str,
        input_sha256: &'a str,
        result_schema: &'a str,
        rows: &'a [AnnualCount],
    }
    Ok(revision(
        "citelattice:annual-publication-production",
        "1.0.0",
        hash_canonical(&Table {
            source_schema: &summary.source_schema_version,
            input_sha256: &summary.input_sha256,
            result_schema: &summary.schema_version,
            rows: &summary.annual,
        })?,
    ))
}

fn make_svg(summary: &PublicationSummary) -> Result<(String, String), SceneError> {
    let largest = summary.annual.iter().map(|r| r.count).max().unwrap_or(1).max(1);
    let width = 640_usize.max(80 + summary.annual.len() * 37);
    let mut image = format!(
        "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 {width} 400\" role=\"img\" aria-label=\"Annual publication counts\"><title>Annual publication production</title><desc>Counts of source-reported works; citation-universe coverage is not inferred</desc>"
    );
    let mut geometry = Vec::new();
    for (index, row) in summary.annual.iter().enumerate() {
        let x = 30 + index * 37;
        let height = u64::try_from(u128::from(row.count) * 280 / u128::from(largest))
            .map_err(|_| SceneError::Encoding)?;
        let y = 330_u64.saturating_sub(height);
        write!(
            image,
            "<rect data-row-key=\"{}\" x=\"{x}\" y=\"{y}\" width=\"26\" height=\"{height}\" fill=\"#465f82\"/><text x=\"{x}\" y=\"350\" font-size=\"9\">{}</text><text x=\"{x}\" y=\"{}\" font-size=\"9\">{}</text>",
            row.year,
            row.year,
            y.saturating_sub(5),
            row.count,
        )
        .map_err(|_| SceneError::Encoding)?;
        geometry.push((row.year, x, y, height, row.count));
    }
    image.push_str("</svg>");
    Ok((image, hash_canonical(&geometry)?))
}

/// Produce a typed evidence scene, declarative Vega-Lite chart and static SVG.
///
/// Numeric browser values are admitted only when exactly representable in
/// JavaScript. This is a scoped annual summary, not global bibliometric coverage.
/// Coordinates are computed from authoritative source rows; no LLM geometry.
///
/// # Errors
/// Refuses denied export, inconsistent annual counts, duplicate/unsorted years,
/// unsafe precision, excess marks and serialization failure.
#[allow(
    clippy::cast_precision_loss,
    reason = "counts are validated <= 2^53-1 before conversion to f64 marks"
)]
pub fn build_annual_scene(
    summary: &PublicationSummary,
    approval: ExportApproval,
    limits: SceneLimits,
) -> Result<AnnualScene, SceneError> {
    if approval != ExportApproval::Allowed {
        return Err(SceneError::Denied);
    }
    verify_table(summary, limits)?;
    let table = table_revision(summary)?;
    let transform = revision(
        "citelattice:annual-bar-layout",
        "1.0.0",
        sha256(b"citelattice annual bar layout v1: 37 px step, 280 px max"),
    );
    let marks: Vec<EvidenceMark> = summary
        .annual
        .iter()
        .map(|row| EvidenceMark {
            id: format!("year:{}", row.year),
            table: table.clone(),
            row_keys: vec![row.year.to_string()],
            membership: None,
            transform: transform.clone(),
            value: Some(row.count as f64),
            uncertainty: vec![UncertaintyKind::SourceCoverage],
        })
        .collect();
    let policy = revision(
        "citelattice:caller-declared-export-approval",
        "1.0.0",
        sha256(b"caller declares allowed; not independently verified"),
    );
    let semantic = json!({
        "data": table,
        "marks": marks,
        "grammar": "citelattice.annual-publication.v1",
        "accessibility": table,
        "policy": policy
    });
    let scene_revision = revision(
        "citelattice:annual-publication-scene",
        "1.0.0",
        hash_canonical(&semantic)?,
    );
    let scene = EvidenceSceneContract {
        scene: scene_revision.clone(),
        grammar: "citelattice.annual-publication.v1".to_owned(),
        tables: vec![table.clone()],
        marks,
        timeline: Vec::new(),
        alignment: None,
        level_of_detail: None,
        accessible_data: table,
        disclosure_policy: policy,
    };
    let vega_lite = json!({
        "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
        "description": "Scoped source-reported annual publication counts; not a global universe.",
        "data": {
            "values": summary.annual.iter().map(|row| json!({
                "year": row.year,
                "publications": row.count
            })).collect::<Vec<_>>()
        },
        "mark": "bar",
        "encoding": {
            "x": {"field": "year", "type": "ordinal", "title": "Publication year"},
            "y": {"field": "publications", "type": "quantitative", "title": "Publications"}
        },
        "usermeta": {
            "source_sha256": summary.input_sha256,
            "table_sha256": scene.tables[0].sha256,
            "scene_sha256": scene_revision.sha256
        }
    });
    let (svg, geometry_digest) = make_svg(summary)?;
    let receipt = RenderReceiptContract {
        scene: scene_revision,
        renderer: revision(
            "citelattice:static-svg-bars",
            "1.0.0",
            sha256(b"citelattice no-network static annual SVG rendering v1"),
        ),
        output: revision("annual.svg", "1.0.0", sha256(svg.as_bytes())),
        reproducibility: "deterministic-integer-geometry-v1; self-check only".to_owned(),
        geometry_check: revision("citelattice:annual-svg-geometry-selfcheck", "1.0.0", geometry_digest),
        disclosure_check: revision(
            "citelattice:annual-numeric-only-disclosure-selfcheck",
            "1.0.0",
            sha256(b"numeric labels only; caller export approval"),
        ),
    };
    Ok(AnnualScene {
        scene,
        vega_lite,
        svg,
        receipt,
        accessible_rows: summary.annual.clone(),
    })
}

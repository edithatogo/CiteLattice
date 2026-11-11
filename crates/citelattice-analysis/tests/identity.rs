//! Scientific identity, separate render changes and accidental-tamper detection.
mod common;
use citelattice_analysis::{analyze,render_key,AnalysisError,ExportPermission,RenderSpec};
use citelattice_core::contracts::versioning::Revision;
fn spec() -> RenderSpec {
    RenderSpec {
        renderer: Revision { id:"test:renderer".into(), version:"1.0.0".into(),sha256:"b".repeat(64) },
        scene_sha256:"c".repeat(64), assets_sha256:"d".repeat(64),
    }
}
#[test]
fn order_invariant_source_sensitive() -> Result<(),AnalysisError> {
    let mut r=common::request(&[Some(10),Some(1),None]);let first=analyze(&r)?;
    r.observations.reverse();assert_eq!(first,analyze(&r)?);
    r.context.citation_universe="different:universe".to_owned();
    assert_ne!(first.body.identity.calculation_sha256,analyze(&r)?.body.identity.calculation_sha256);
    Ok(())
}
#[test]
fn permission_change_preserves_science_but_blocks_output() -> Result<(),AnalysisError> {
    let mut r=common::request(&[Some(10)]);let first=analyze(&r)?;
    r.export=ExportPermission::Denied;let denied=analyze(&r)?;
    assert_eq!(first.body.identity.calculation_sha256,denied.body.identity.calculation_sha256);
    assert_ne!(first.body.identity.request_sha256,denied.body.identity.request_sha256);
    assert!(matches!(render_key(&denied,&spec()),Err(AnalysisError::ExportDenied)));
    Ok(())
}
#[test]
fn render_assets_separate_and_modified_result_rejected() -> Result<(),AnalysisError> {
    let mut r=analyze(&common::request(&[Some(3)]))?;let mut s=spec();let a=render_key(&r,&s)?;
    s.assets_sha256="e".repeat(64);assert_ne!(a,render_key(&r,&s)?);
    r.body.summary.h.lower=99;
    assert!(matches!(render_key(&r,&s),Err(AnalysisError::Integrity)));
    Ok(())
}

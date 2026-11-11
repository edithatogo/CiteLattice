//! Bounded line framing and non-disclosing diagnostics.
mod common;
use citelattice_analysis::{
    CitationRequest, ExportPermission, StreamError, StreamLimits, run_jsonl,
};
use std::io::Cursor;
#[test]
fn crlf_and_final_line_without_newline() -> Result<(), Box<dyn std::error::Error>> {
    let s = serde_json::to_string(&common::request(&[Some(10), Some(2)]))?;
    let mut out = Vec::new();
    assert_eq!(
        run_jsonl(
            Cursor::new(format!("{s}\r\n{s}")),
            &mut out,
            StreamLimits::default()
        )?,
        2
    );
    assert_eq!(out.iter().filter(|&&b| b == b'\n').count(), 2);
    Ok(())
}
#[test]
fn oversized_frame_and_frame_count_rejected() -> Result<(), Box<dyn std::error::Error>> {
    let mut out = Vec::new();
    let limits = StreamLimits {
        max_line_bytes: 32,
        max_frames: 5,
    };
    assert!(matches!(
        run_jsonl(Cursor::new(vec![b'x'; 128]), &mut out, limits),
        Err(StreamError::FrameLimit(1))
    ));
    assert!(out.is_empty());
    let s = serde_json::to_string(&common::request(&[Some(1)]))?;
    let limits = StreamLimits {
        max_line_bytes: 4096,
        max_frames: 1,
    };
    assert!(matches!(
        run_jsonl(Cursor::new(format!("{s}\n{s}\n")), &mut out, limits),
        Err(StreamError::CountLimit)
    ));
    Ok(())
}
#[test]
fn denied_output_and_late_failure() -> Result<(), Box<dyn std::error::Error>> {
    let mut r = common::request(&[Some(1)]);
    r.export = ExportPermission::Unknown;
    let mut out = Vec::new();
    assert!(
        run_jsonl(
            Cursor::new(serde_json::to_vec(&r)?),
            &mut out,
            StreamLimits::default()
        )
        .is_err()
    );
    assert!(out.is_empty());
    r.export = ExportPermission::Allowed;
    let s = serde_json::to_string(&r)?;
    let err = run_jsonl(
        Cursor::new(format!("{s}\n{{private-secret-content\n")),
        &mut out,
        StreamLimits::default(),
    )
    .err()
    .ok_or("expected error")?;
    assert_eq!(out.iter().filter(|&&b| b == b'\n').count(), 1);
    assert!(!err.to_string().contains("private-secret-content"));
    Ok(())
}
#[test]
fn decimal_count_and_explicit_missingness() -> Result<(), Box<dyn std::error::Error>> {
    let r = serde_json::to_value(common::request(&[Some(u64::MAX)]))?;
    assert_eq!(r["observations"][0]["citations"], "18446744073709551615");
    for bad in [
        serde_json::json!(1),
        serde_json::json!("01"),
        serde_json::json!("-1"),
        serde_json::json!("18446744073709551616"),
    ] {
        let mut copy = r.clone();
        copy["observations"][0]["citations"] = bad;
        assert!(serde_json::from_value::<CitationRequest>(copy).is_err());
    }
    let mut r = r;
    r["observations"][0]
        .as_object_mut()
        .ok_or("object")?
        .remove("citations");
    assert!(serde_json::from_value::<CitationRequest>(r).is_err());
    Ok(())
}

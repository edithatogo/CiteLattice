//! End-to-end CLI stdout/stderr and exit-code checks (requires a compiled binary).
use std::io::Write;
use std::process::{Command, Stdio};

#[test]
fn offline_binary_emits_metric_json_only() -> Result<(), Box<dyn std::error::Error>> {
    let mut child = Command::new(env!("CARGO_BIN_EXE_citelattice"))
        .arg("citation-summary")
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()?;
    let mut input = child.stdin.take().ok_or("missing stdin")?;
    input.write_all(include_bytes!(
        "../../../examples/citation-summary/complete.request.jsonl"
    ))?;
    drop(input);
    let result = child.wait_with_output()?;
    assert!(result.status.success());
    assert!(result.stderr.is_empty());
    let output: serde_json::Value = serde_json::from_slice(&result.stdout)?;
    assert_eq!(output["body"]["summary"]["h"]["lower"], 4);
    assert_eq!(output["body"]["summary"]["g"]["lower"], 5);
    assert_eq!(output["body"]["summary"]["known_total"], "30");
    Ok(())
}

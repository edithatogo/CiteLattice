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
    assert_eq!(result.stderr.len(), 0);
    let output: serde_json::Value = serde_json::from_slice(&result.stdout)?;
    assert_eq!(output["body"]["summary"]["h"]["lower"], 4);
    assert_eq!(output["body"]["summary"]["g"]["lower"], 5);
    assert_eq!(output["body"]["summary"]["known_total"], "30");
    Ok(())
}

#[test]
fn cli_has_version_and_subcommand_help_without_network_or_stdin()
-> Result<(), Box<dyn std::error::Error>> {
    let version = Command::new(env!("CARGO_BIN_EXE_citelattice"))
        .arg("--version")
        .output()?;
    assert!(
        version.status.success(),
        "{}",
        String::from_utf8_lossy(&version.stderr)
    );
    assert!(version.stderr.is_empty());
    assert!(String::from_utf8_lossy(&version.stdout).contains("citelattice"));

    let help = Command::new(env!("CARGO_BIN_EXE_citelattice"))
        .args(["citation-summary", "--help"])
        .output()?;
    assert!(
        help.status.success(),
        "{}",
        String::from_utf8_lossy(&help.stderr)
    );
    assert!(help.stderr.is_empty());
    let help_text = String::from_utf8_lossy(&help.stdout);
    assert!(help_text.contains("citation-summary"));
    Ok(())
}

#[test]
fn invalid_command_fails_closed_without_json_output() -> Result<(), Box<dyn std::error::Error>> {
    let output = Command::new(env!("CARGO_BIN_EXE_citelattice"))
        .arg("unknown-command")
        .output()?;
    assert_eq!(output.status.code(), Some(2));
    assert!(output.stdout.is_empty());
    assert!(String::from_utf8_lossy(&output.stderr).contains("citation-summary"));
    Ok(())
}

//! Executable consumer contract for Searchright's proposed scholarly event stream.
use std::io::Cursor;

use citelattice_ingest::events::{
    ApplyStatus, EventError, EventLedger, EventLimits, ObjectState, read_event_stream,
};
use serde_json::{Value, json};
use sha2::{Digest, Sha256};

fn fixture() -> Value {
    serde_json::from_str(include_str!(
        "../../../contracts/interop/examples/scholarly-stream-upsert.json"
    ))
    .unwrap()
}

fn next_event(previous: &Value, op: &str) -> Value {
    let mut event = previous.clone();
    event["sequence"] = json!("2");
    event["event_id"] = json!(format!("fixture-event-{op}"));
    event["prior_revision"] = previous["source_revision"].clone();
    event["source_revision"]["digest"]["hex"] = json!("f".repeat(64));
    event["change"] = json!({
        "op": op,
        "target": "fixture:paper-1",
        "reason": "revised by source",
        "replacement": if op == "correct" {
            Some(event["source_revision"].clone())
        } else { None }
    });
    let bytes = serde_json_canonicalizer::to_vec(&event["change"]).unwrap();
    event["payload_digest"]["hex"] = json!(hex::encode(Sha256::digest(&bytes)));
    event
}

#[test]
fn producer_fixture_is_admitted_without_raw_csl_retention() {
    let mut ledger = EventLedger::new(EventLimits::default());
    assert_eq!(
        ledger
            .apply_json(&serde_json::to_vec(&fixture()).unwrap())
            .unwrap(),
        ApplyStatus::Applied
    );
    let snapshot = ledger.snapshot();
    assert_eq!(snapshot.stream_id.as_deref(), Some("synthetic-stream"));
    assert_eq!(snapshot.epoch, Some(1));
    assert_eq!(snapshot.last_sequence, 1);
    assert_eq!(snapshot.objects.len(), 1);
    assert_eq!(snapshot.objects[0].key, "fixture:paper-1");
    assert_eq!(snapshot.objects[0].state, ObjectState::Active);
    assert_eq!(snapshot.objects[0].metadata_rights, "redistributable");
    let serialized = serde_json::to_string(&snapshot).unwrap();
    assert!(!serialized.contains("Synthetic scholarly stream fixture"));
}

#[test]
fn exact_replay_is_idempotent_conflicting_replay_is_rejected() {
    let mut ledger = EventLedger::new(EventLimits::default());
    let bytes = serde_json::to_vec(&fixture()).unwrap();
    assert_eq!(ledger.apply_json(&bytes).unwrap(), ApplyStatus::Applied);
    assert_eq!(ledger.apply_json(&bytes).unwrap(), ApplyStatus::Duplicate);
    assert_eq!(ledger.snapshot().last_sequence, 1);
    let mut altered = fixture();
    altered["event_id"] = json!("synthetic-event-1");
    altered["observed_at"] = json!("2026-11-10T01:00:00Z");
    assert!(matches!(
        ledger.apply_json(&serde_json::to_vec(&altered).unwrap()),
        Err(EventError::ConflictingReplay)
    ));
}

#[test]
fn bad_digest_version_counter_and_gap_fail_without_state_change() {
    let cases = vec![
        ("digest", {
            let mut x = fixture();
            x["payload_digest"]["hex"] = json!("0".repeat(64));
            x
        }),
        ("version", {
            let mut x = fixture();
            x["version"] = json!("2.0.0");
            x
        }),
        ("overflow", {
            let mut x = fixture();
            x["epoch"] = json!("18446744073709551616");
            x
        }),
        ("gap", {
            let mut x = fixture();
            x["sequence"] = json!("2");
            x
        }),
        ("invalid date", {
            let mut x = fixture();
            x["observed_at"] = json!("2026-02-30T00:00:00Z");
            x
        }),
    ];
    for (label, payload) in cases {
        let mut ledger = EventLedger::new(EventLimits::default());
        assert!(
            ledger
                .apply_json(&serde_json::to_vec(&payload).unwrap())
                .is_err(),
            "{label}"
        );
        assert_eq!(ledger.snapshot().last_sequence, 0, "{label}");
        assert!(ledger.snapshot().objects.is_empty(), "{label}");
    }
}

#[test]
fn correction_is_a_pointer_not_fabricated_replacement_content() {
    let mut ledger = EventLedger::new(EventLimits::default());
    let first = fixture();
    ledger
        .apply_json(&serde_json::to_vec(&first).unwrap())
        .unwrap();
    let correction = next_event(&first, "correct");
    ledger
        .apply_json(&serde_json::to_vec(&correction).unwrap())
        .unwrap();
    let snapshot = ledger.snapshot();
    assert_eq!(snapshot.last_sequence, 2);
    assert_eq!(snapshot.objects[0].state, ObjectState::CorrectionPending);
    assert!(snapshot.objects[0].replacement_digest.is_some());
    assert!(
        !serde_json::to_string(&snapshot)
            .unwrap()
            .contains("Synthetic scholarly stream fixture")
    );
}

#[test]
fn delete_tombstones_and_prevents_silent_resurrection() {
    let first = fixture();
    let mut ledger = EventLedger::new(EventLimits::default());
    ledger
        .apply_json(&serde_json::to_vec(&first).unwrap())
        .unwrap();
    ledger
        .apply_json(&serde_json::to_vec(&next_event(&first, "delete")).unwrap())
        .unwrap();
    let snapshot = ledger.snapshot();
    assert_eq!(snapshot.objects[0].state, ObjectState::Deleted);
    assert!(snapshot.objects[0].body_digest.is_none());
}

#[test]
fn bounded_line_reader_rejects_oversized_frames() {
    let bytes = serde_json::to_vec(&fixture()).unwrap();
    let limits = EventLimits {
        max_line_bytes: 64,
        max_events: 10,
        max_objects: 10,
    };
    assert!(matches!(
        read_event_stream(Cursor::new(bytes), limits),
        Err(EventError::FrameLimit)
    ));
}

#[test]
fn multi_event_reader_preserves_sequence_and_rejects_gaps() {
    let first = fixture();
    let second = next_event(&first, "retract");
    let input = format!(
        "{}\n{}\n",
        serde_json::to_string(&first).unwrap(),
        serde_json::to_string(&second).unwrap()
    );
    let ledger = read_event_stream(Cursor::new(input), EventLimits::default()).unwrap();
    assert_eq!(ledger.snapshot().last_sequence, 2);
    assert_eq!(ledger.snapshot().objects[0].state, ObjectState::Retracted);
    let mut gap = second;
    gap["sequence"] = json!("3");
    let input = format!(
        "{}\n{}\n",
        serde_json::to_string(&first).unwrap(),
        serde_json::to_string(&gap).unwrap()
    );
    assert!(matches!(
        read_event_stream(Cursor::new(input), EventLimits::default()),
        Err(EventError::Sequence)
    ));
}

#[test]
fn unverified_rights_redact_source_identifiers_from_snapshot() {
    let mut input = fixture();
    input["rights"]["metadata"] = json!("restricted");
    let mut ledger = EventLedger::new(EventLimits::default());
    ledger
        .apply_json(&serde_json::to_vec(&input).unwrap())
        .unwrap();
    let summary = ledger.snapshot();
    assert_eq!(summary.version, "0.1.0");
    assert_eq!(
        summary.contract_id,
        "org.citelattice.scholarly-event-snapshot"
    );
    assert!(summary.objects[0].key.starts_with("sha256:"));
    let exposed = serde_json::to_string(&summary).unwrap();
    assert!(!exposed.contains("fixture:paper-1"));
    assert!(!exposed.contains("Synthetic scholarly stream fixture"));
}

#[test]
fn mismatched_prior_revision_fails_without_mutation() {
    let first = fixture();
    let mut ledger = EventLedger::new(EventLimits::default());
    ledger
        .apply_json(&serde_json::to_vec(&first).unwrap())
        .unwrap();
    let mut second = next_event(&first, "retract");
    second["prior_revision"] = Value::Null;
    assert!(matches!(
        ledger.apply_json(&serde_json::to_vec(&second).unwrap()),
        Err(EventError::Sequence)
    ));
    assert_eq!(ledger.snapshot().last_sequence, 1);
}

#[test]
fn illegal_change_fields_and_unknown_kind_fail_closed() {
    let mut event = fixture();
    event["change"]["object"]["kind"] = json!("imaginary_research_type");
    let bytes = serde_json_canonicalizer::to_vec(&event["change"]).unwrap();
    event["payload_digest"]["hex"] = json!(hex::encode(Sha256::digest(&bytes)));
    assert!(matches!(
        EventLedger::new(EventLimits::default()).apply_json(&serde_json::to_vec(&event).unwrap()),
        Err(EventError::InvalidWire)
    ));
    let mut unexpected = fixture();
    unexpected["new_undeclared_field"] = json!("not valid");
    assert!(matches!(
        EventLedger::new(EventLimits::default())
            .apply_json(&serde_json::to_vec(&unexpected).unwrap()),
        Err(EventError::InvalidWire)
    ));
}

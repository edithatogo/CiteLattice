//! Exact integer conservation, streaming parity, atomic rejection and replay.
use citelattice_ingest::events::{ApplyStatus, EventLedger, EventLimits, read_event_stream};
use citelattice_ingest::{SourceLimits, summarize_reader};
use std::io::{BufReader, Cursor};

const EVENT: &[u8] =
    include_bytes!("../../../../contracts/interop/examples/scholarly-stream-upsert.json");

pub fn check(data: &[u8]) {
    if data.len() > 65_536 {
        return;
    }
    let limits = SourceLimits {
        max_line_bytes: 32_768,
        max_records: 8,
    };
    let full = summarize_reader(Cursor::new(data), limits).map_err(|e| e.to_string());
    let fragmented = summarize_reader(BufReader::with_capacity(7, Cursor::new(data)), limits)
        .map_err(|e| e.to_string());
    assert_eq!(
        full, fragmented,
        "fragmentation must not change source semantics"
    );
    if let Ok(summary) = full {
        assert_eq!(
            summary.annual.iter().map(|r| r.count).sum::<u64>() + summary.undated,
            summary.record_count
        );
        assert_eq!(
            summary.document_types.iter().map(|r| r.count).sum::<u64>(),
            summary.record_count
        );
        assert!(summary.record_count <= 8);
        assert!(summary.coauthors.iter().all(|e| e.a < e.b && e.works > 0));
    }
    let event_limits = EventLimits {
        max_line_bytes: 32_768,
        max_events: 8,
        max_objects: 8,
    };
    let full = read_event_stream(Cursor::new(data), event_limits)
        .map(|ledger| ledger.snapshot())
        .map_err(|e| e.to_string());
    let fragmented =
        read_event_stream(BufReader::with_capacity(7, Cursor::new(data)), event_limits)
            .map(|ledger| ledger.snapshot())
            .map_err(|e| e.to_string());
    assert_eq!(
        full, fragmented,
        "frame boundaries must not depend on buffering"
    );
    for initialized in [false, true] {
        let mut ledger = EventLedger::new(event_limits);
        if initialized {
            ledger.apply_json(EVENT).expect("synthetic seed is valid");
        }
        let before = ledger.snapshot();
        let outcome = ledger.apply_json(data);
        let after = ledger.snapshot();
        match outcome {
            Err(_) | Ok(ApplyStatus::Duplicate) => assert_eq!(before, after),
            Ok(ApplyStatus::Applied) => {
                assert_eq!(after.last_sequence, before.last_sequence + 1);
                assert_eq!(after.applied, before.applied + 1);
                assert!(after.objects.len() <= event_limits.max_objects);
                assert_eq!(ledger.apply_json(data).ok(), Some(ApplyStatus::Duplicate));
                assert_eq!(ledger.snapshot(), after, "replay must not mutate state");
            }
        }
    }
}

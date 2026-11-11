//! Bounded consumer for the proposed Searchright scholarly change envelope.
//!
//! The stream proposal is NOT an active producer integration or durable log.
//! This module checks structure, semantic sequencing and RFC 8785 digests,
//! retaining only content fingerprints rather than CSL titles or abstracts.
#![forbid(unsafe_code)]
use std::collections::BTreeMap;
use std::io::{BufRead, Read};

use serde::{Deserialize, Serialize};
use serde_json::{Map, Value};
use sha2::{Digest as _, Sha256};
use time::{OffsetDateTime, format_description::well_known::Rfc3339};

/// Maximum per-line, event and object resource budgets.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct EventLimits {
    /// Maximum frame bytes, including line ending.
    pub max_line_bytes: usize,
    /// Maximum number of physical event frames consumed.
    pub max_events: usize,
    /// Maximum number of live and tombstoned object identities.
    pub max_objects: usize,
}

impl Default for EventLimits {
    fn default() -> Self {
        Self {
            max_line_bytes: 1_048_576,
            max_events: 100_000,
            max_objects: 100_000,
        }
    }
}

/// Non-disclosing error semantics for semantic, integrity and resource failures.
#[derive(Debug, thiserror::Error)]
pub enum EventError {
    /// Malformed wire JSON or unsupported extra fields.
    #[error("invalid event wire contract")]
    InvalidWire,
    /// Unsupported schema or canonicalization scheme.
    #[error("unsupported scholarly stream version")]
    Version,
    /// Missing, invalid, or inconsistent event identifiers.
    #[error("invalid event metadata")]
    Metadata,
    /// Incorrect source digest or unverified event payload integrity.
    #[error("event digest mismatch")]
    Digest,
    /// Incorrect stream/epoch/sequence or prior revision.
    #[error("event sequence or source lineage mismatch")]
    Sequence,
    /// Reuse of an event identifier with different canonical content.
    #[error("conflicting replay")]
    ConflictingReplay,
    /// Target missing/deleted, or an unknown operation.
    #[error("invalid object transition")]
    Transition,
    /// An event line exceeds limits.
    #[error("event frame too large")]
    FrameLimit,
    /// Bounded state, physical frame or object count exceeded.
    #[error("event resource budget exhausted")]
    ResourceLimit,
    /// Source bytes could not be read.
    #[error("event input failed")]
    Io,
}

/// Successful processing of one event.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ApplyStatus {
    /// A new, semantically valid event changed the ledger.
    Applied,
    /// Exact replay (same event identity and canonical envelope) changed nothing.
    Duplicate,
}

/// A research object's recorded transition; pending corrections require enrichment.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ObjectState {
    /// Source record received, no scientific identity resolution implied.
    Active,
    /// Source issued correction pointer; replacement content is not invented.
    CorrectionPending,
    /// Source marked the object retracted.
    Retracted,
    /// Prior content and direct key were removed; only a hashed tombstone remains.
    Deleted,
}

/// Disclosure-minimised object state; contains no publication titles or abstracts.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ObservedObject {
    /// Source key, or a one-way identifier digest after deletion.
    pub key: String,
    /// Publication/grant/patent/trial/etc type.
    pub kind: String,
    /// Latest declared transition state.
    pub state: ObjectState,
    /// SHA-256 of an admitted CSL/typed artifact, or null after deletion.
    pub body_digest: Option<String>,
    /// SHA-256 of a replacement artifact when correction is pending.
    pub replacement_digest: Option<String>,
    /// Source metadata-disclosure classification.
    pub metadata_rights: String,
}

/// Immutable snapshot of the in-memory ledger's declared event state.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EventSnapshot {
    /// Namespaced output contract for consumer snapshots.
    pub contract_id: String,
    /// Exact output schema version, independent of the source stream version.
    pub version: String,
    /// One stream only, preventing accidental implicit cross-source order.
    pub stream_id: Option<String>,
    /// One declared epoch (cross-epoch migration is not implemented).
    pub epoch: Option<u64>,
    /// Last exactly contiguous sequence admitted.
    pub last_sequence: u64,
    /// Source snapshot digest for the last accepted event.
    pub source_digest: Option<String>,
    /// Number of distinct applied events.
    pub applied: u64,
    /// Materialised, disclosure-minimised objects and hashed tombstones.
    pub objects: Vec<ObservedObject>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct WireDigest {
    algorithm: String,
    hex: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct Artifact {
    id: String,
    schema_id: String,
    digest: WireDigest,
    media_type: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct Rights {
    metadata: String,
    abstracts: String,
    full_text: String,
    policy: Artifact,
}

#[derive(Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct EventEnvelope {
    contract_id: String,
    version: String,
    stream_id: String,
    epoch: String,
    sequence: String,
    event_id: String,
    observed_at: String,
    source_revision: Artifact,
    prior_revision: Option<Artifact>,
    rights: Rights,
    canonicalization: String,
    payload_digest: WireDigest,
    change: Value,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct SourceObject {
    kind: String,
    key: String,
    csl: Option<Value>,
    record: Option<Artifact>,
    extensions: Vec<Artifact>,
}

fn identifier(value: &str) -> bool {
    !value.is_empty()
        && value.len() <= 1024
        && value.trim() == value
        && !value.chars().any(char::is_control)
}

fn digest_string(value: &str) -> bool {
    value.len() == 64
        && value
            .bytes()
            .all(|c| c.is_ascii_digit() || (b'a'..=b'f').contains(&c))
}

fn valid_digest(value: &WireDigest) -> bool {
    value.algorithm == "sha256" && digest_string(&value.hex)
}

fn valid_artifact(value: &Artifact) -> bool {
    identifier(&value.id)
        && identifier(&value.schema_id)
        && identifier(&value.media_type)
        && valid_digest(&value.digest)
}

fn parse_counter(value: &str) -> Result<u64, EventError> {
    if value.is_empty()
        || (value.len() > 1 && value.starts_with('0'))
        || !value.bytes().all(|c| c.is_ascii_digit())
    {
        return Err(EventError::Metadata);
    }
    value.parse::<u64>().map_err(|_| EventError::Metadata)
}

fn hex_digest(bytes: &[u8]) -> String {
    hex::encode(Sha256::digest(bytes))
}

fn canonical(value: &impl Serialize) -> Result<Vec<u8>, EventError> {
    serde_json_canonicalizer::to_vec(value).map_err(|_| EventError::InvalidWire)
}

fn valid_rights(value: &Rights) -> bool {
    matches!(
        value.metadata.as_str(),
        "redistributable" | "restricted" | "unknown"
    ) && matches!(
        value.abstracts.as_str(),
        "redistributable" | "restricted" | "unknown" | "absent"
    ) && matches!(
        value.full_text.as_str(),
        "redistributable" | "restricted" | "unknown" | "absent"
    ) && valid_artifact(&value.policy)
}

fn exact_fields(obj: &Map<String, Value>, expected: &[&str]) -> bool {
    obj.len() == expected.len() && expected.iter().all(|key| obj.contains_key(*key))
}

fn parse_object(value: &Value) -> Result<(String, String, String), EventError> {
    let obj: SourceObject =
        serde_json::from_value(value.clone()).map_err(|_| EventError::InvalidWire)?;
    if !identifier(&obj.key) || !identifier(&obj.kind) {
        return Err(EventError::Metadata);
    }
    for extension in &obj.extensions {
        if !valid_artifact(extension) {
            return Err(EventError::Metadata);
        }
    }
    if obj.kind == "publication" {
        if obj.record.is_some() {
            return Err(EventError::InvalidWire);
        }
        let csl = obj
            .csl
            .as_ref()
            .and_then(Value::as_object)
            .ok_or(EventError::InvalidWire)?;
        let csl_id = csl.get("id").ok_or(EventError::InvalidWire)?;
        if !csl_id.is_string() && !csl_id.is_number() {
            return Err(EventError::InvalidWire);
        }
        if !csl
            .get("type")
            .and_then(Value::as_str)
            .is_some_and(identifier)
        {
            return Err(EventError::InvalidWire);
        }
        Ok((obj.key, obj.kind, hex_digest(&canonical(csl)?)))
    } else if matches!(
        obj.kind.as_str(),
        "grant"
            | "patent"
            | "clinical_trial"
            | "policy_document"
            | "dataset"
            | "software"
            | "report"
            | "venue"
            | "organisation"
    ) {
        if obj.csl.is_some() {
            return Err(EventError::InvalidWire);
        }
        let reference = obj.record.ok_or(EventError::InvalidWire)?;
        if !valid_artifact(&reference) {
            return Err(EventError::Metadata);
        }
        Ok((obj.key, obj.kind, reference.digest.hex))
    } else {
        Err(EventError::InvalidWire)
    }
}

/// Bounded in-memory event verification; NOT a durable checkpoint or full CSL cache.
pub struct EventLedger {
    limits: EventLimits,
    stream_id: Option<String>,
    epoch: Option<u64>,
    last_sequence: u64,
    last_source: Option<Artifact>,
    observed: BTreeMap<String, ObservedObject>,
    tombstones: BTreeMap<String, ObservedObject>,
    seen_events: BTreeMap<String, String>,
}

impl EventLedger {
    /// Create a bounded consumer with explicit limits.
    #[must_use]
    pub fn new(limits: EventLimits) -> Self {
        Self {
            limits,
            stream_id: None,
            epoch: None,
            last_sequence: 0,
            last_source: None,
            observed: BTreeMap::new(),
            tombstones: BTreeMap::new(),
            seen_events: BTreeMap::new(),
        }
    }

    /// Current source-minimised, deterministic ledger snapshot.
    #[must_use]
    pub fn snapshot(&self) -> EventSnapshot {
        let mut objects: Vec<_> = self.observed.values().cloned().collect();
        objects.extend(self.tombstones.values().cloned());
        // A restricted or unverified source identifier must not be disclosed
        // from the introspection API. Raw keys remain private to the ledger.
        for object in &mut objects {
            if object.state != ObjectState::Deleted && object.metadata_rights != "redistributable" {
                object.key = format!("sha256:{}", hex_digest(object.key.as_bytes()));
            }
        }
        objects.sort_by(|a, b| a.key.cmp(&b.key));
        EventSnapshot {
            contract_id: "org.citelattice.scholarly-event-snapshot".to_owned(),
            version: "0.1.0".to_owned(),
            stream_id: self.stream_id.clone(),
            epoch: self.epoch,
            last_sequence: self.last_sequence,
            source_digest: self.last_source.as_ref().map(|src| src.digest.hex.clone()),
            applied: u64::try_from(self.seen_events.len()).unwrap_or(u64::MAX),
            objects,
        }
    }

    /// Verify and apply one JSON envelope without retaining raw CSL fields.
    ///
    /// # Errors
    /// Rejects invalid versions, missing/invalid digests, sequence gaps,
    /// conflicting replays, illegal transitions or exhausted budgets.
    pub fn apply_json(&mut self, bytes: &[u8]) -> Result<ApplyStatus, EventError> {
        if self.limits.max_line_bytes == 0
            || self.limits.max_events == 0
            || self.limits.max_objects == 0
            || bytes.len() > self.limits.max_line_bytes
        {
            return Err(EventError::FrameLimit);
        }
        let event: EventEnvelope =
            serde_json::from_slice(bytes).map_err(|_| EventError::InvalidWire)?;
        if event.contract_id != "org.scholarly.stream"
            || event.version != "1.0.0-design.2"
            || event.canonicalization != "rfc8785"
        {
            return Err(EventError::Version);
        }
        if !identifier(&event.stream_id)
            || !identifier(&event.event_id)
            || event.observed_at.len() > 64
            || OffsetDateTime::parse(&event.observed_at, &Rfc3339).is_err()
            || !valid_artifact(&event.source_revision)
            || !valid_rights(&event.rights)
            || !valid_digest(&event.payload_digest)
            || event
                .prior_revision
                .as_ref()
                .is_some_and(|rev| !valid_artifact(rev))
        {
            return Err(EventError::Metadata);
        }
        let epoch = parse_counter(&event.epoch)?;
        let sequence = parse_counter(&event.sequence)?;
        if epoch == 0 || sequence == 0 {
            return Err(EventError::Sequence);
        }
        if hex_digest(&canonical(&event.change)?) != event.payload_digest.hex {
            return Err(EventError::Digest);
        }
        let event_hash = hex_digest(&canonical(&event)?);
        if let Some(prior) = self.seen_events.get(&event.event_id) {
            return if prior == &event_hash {
                Ok(ApplyStatus::Duplicate)
            } else {
                Err(EventError::ConflictingReplay)
            };
        }
        if self.seen_events.len() >= self.limits.max_events {
            return Err(EventError::ResourceLimit);
        }
        let expected = self
            .last_sequence
            .checked_add(1)
            .ok_or(EventError::ResourceLimit)?;
        if sequence != expected {
            return Err(EventError::Sequence);
        }
        if self.stream_id.is_some() {
            if self.stream_id.as_deref() != Some(event.stream_id.as_str())
                || self.epoch != Some(epoch)
                || self.last_source.as_ref() != event.prior_revision.as_ref()
            {
                return Err(EventError::Sequence);
            }
        } else if sequence != 1 || event.prior_revision.is_some() {
            return Err(EventError::Sequence);
        }

        let change = event.change.as_object().ok_or(EventError::InvalidWire)?;
        let op = change
            .get("op")
            .and_then(Value::as_str)
            .ok_or(EventError::InvalidWire)?;
        // Check all mutations and resource limits before committing any state.
        enum Planned {
            Insert(String, ObservedObject),
            Update(String, ObservedObject),
            Delete(String, String, ObservedObject),
        }
        let planned = if op == "upsert" {
            if !exact_fields(change, &["op", "object"]) {
                return Err(EventError::InvalidWire);
            }
            let (key, kind, body_digest) =
                parse_object(change.get("object").ok_or(EventError::InvalidWire)?)?;
            let key_hash = hex_digest(key.as_bytes());
            if self.tombstones.contains_key(&key_hash) {
                return Err(EventError::Transition);
            }
            if !self.observed.contains_key(&key)
                && self.observed.len() + self.tombstones.len() >= self.limits.max_objects
            {
                return Err(EventError::ResourceLimit);
            }
            Planned::Insert(
                key.clone(),
                ObservedObject {
                    key,
                    kind,
                    state: ObjectState::Active,
                    body_digest: Some(body_digest),
                    replacement_digest: None,
                    metadata_rights: event.rights.metadata.clone(),
                },
            )
        } else if matches!(op, "correct" | "retract" | "delete") {
            if !exact_fields(change, &["op", "target", "reason", "replacement"]) {
                return Err(EventError::InvalidWire);
            }
            let key = change
                .get("target")
                .and_then(Value::as_str)
                .filter(|v| identifier(v))
                .ok_or(EventError::Metadata)?;
            let reason = change
                .get("reason")
                .and_then(Value::as_str)
                .filter(|v| identifier(v))
                .ok_or(EventError::Metadata)?;
            // A reason must exist, but raw text is deliberately never retained.
            let _ = reason;
            let before = self.observed.get(key).ok_or(EventError::Transition)?;
            let replacement: Option<Artifact> = match change.get("replacement") {
                Some(Value::Null) => None,
                Some(v) => {
                    Some(serde_json::from_value(v.clone()).map_err(|_| EventError::InvalidWire)?)
                }
                None => return Err(EventError::InvalidWire),
            };
            if replacement.as_ref().is_some_and(|v| !valid_artifact(v)) {
                return Err(EventError::Metadata);
            }
            if op == "correct" && replacement.is_none() {
                return Err(EventError::Transition);
            }
            let mut next = before.clone();
            next.metadata_rights.clone_from(&event.rights.metadata);
            match op {
                "correct" => {
                    next.state = ObjectState::CorrectionPending;
                    next.body_digest = None;
                    next.replacement_digest = replacement.map(|r| r.digest.hex);
                    Planned::Update(key.to_owned(), next)
                }
                "retract" => {
                    next.state = ObjectState::Retracted;
                    Planned::Update(key.to_owned(), next)
                }
                _ => {
                    let hash = hex_digest(key.as_bytes());
                    next.key = format!("sha256:{hash}");
                    next.state = ObjectState::Deleted;
                    next.body_digest = None;
                    next.replacement_digest = None;
                    Planned::Delete(key.to_owned(), hash, next)
                }
            }
        } else {
            return Err(EventError::Transition);
        };

        match planned {
            Planned::Insert(key, value) | Planned::Update(key, value) => {
                self.observed.insert(key, value);
            }
            Planned::Delete(key, hash, tombstone) => {
                self.observed.remove(&key);
                self.tombstones.insert(hash, tombstone);
            }
        }
        self.last_sequence = sequence;
        self.epoch = Some(epoch);
        self.stream_id = Some(event.stream_id);
        self.last_source = Some(event.source_revision);
        self.seen_events.insert(event.event_id, event_hash);
        Ok(ApplyStatus::Applied)
    }
}

/// Read and verify a bounded stream into an in-memory ledger.
///
/// This is not a durable event spool, a completed Searchright producer,
/// or an atomic cross-process checkpoint. Blank frames are rejected.
///
/// # Errors
/// Fails closed on oversized/invalid frames, resource limits or I/O.
pub fn read_event_stream<R: BufRead>(
    mut input: R,
    limits: EventLimits,
) -> Result<EventLedger, EventError> {
    if limits.max_events == 0 || limits.max_line_bytes == 0 || limits.max_objects == 0 {
        return Err(EventError::ResourceLimit);
    }
    let probe = limits
        .max_line_bytes
        .checked_add(1)
        .ok_or(EventError::ResourceLimit)?;
    let probe = u64::try_from(probe).map_err(|_| EventError::ResourceLimit)?;
    let mut ledger = EventLedger::new(limits);
    let mut line = Vec::new();
    let mut physical = 0_usize;
    loop {
        line.clear();
        let count = (&mut input)
            .take(probe)
            .read_until(b'\n', &mut line)
            .map_err(|_| EventError::Io)?;
        if count == 0 {
            break;
        }
        physical = physical.checked_add(1).ok_or(EventError::ResourceLimit)?;
        if physical > limits.max_events {
            return Err(EventError::ResourceLimit);
        }
        if count > limits.max_line_bytes {
            return Err(EventError::FrameLimit);
        }
        ledger.apply_json(&line)?;
    }
    Ok(ledger)
}

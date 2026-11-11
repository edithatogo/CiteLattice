use std::io::{BufRead, Read, Write};

use crate::{analyze, AnalysisError, CitationRequest, ExportPermission};

/// Per-process framing limits; the API also limits publications per request.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct StreamLimits {
    /// Maximum UTF-8 frame bytes, including any CRLF/newline terminator.
    pub max_line_bytes: usize,
    /// Maximum independent analysis requests; not a stream replay sequence.
    pub max_frames: u64,
}

impl Default for StreamLimits {
    fn default() -> Self {
        Self { max_line_bytes: 1_048_576, max_frames: 10_000 }
    }
}

/// Bounded I/O failures; raw source text is never included in diagnostics.
#[derive(Debug, thiserror::Error)]
pub enum StreamError {
    /// An invalid or overflowing framing limit was provided.
    #[error("invalid framing limits")]
    Limits,
    /// Input failed without echoing a filename, record or credential.
    #[error("input I/O failure")]
    Input,
    /// A failed write may leave a partial final line; earlier lines remain valid.
    #[error("output I/O failure")]
    Output,
    /// Input frame did not decode under the exact contract.
    #[error("invalid JSON contract at line {0}")]
    InvalidFrame(u64),
    /// A line exceeded the configured bound before unbounded allocation.
    #[error("frame byte limit exceeded at line {0}")]
    FrameLimit(u64),
    /// Too many independent requests were supplied.
    #[error("frame count limit exceeded")]
    CountLimit,
    /// Analysis failed; its display contains no raw record values.
    #[error("analysis rejected at line {line}: {error}")]
    Analysis {
        /// One-based physical line number.
        line: u64,
        /// Non-disclosing semantic failure.
        error: AnalysisError,
    },
}

/// Process independent NDJSON analysis requests with synchronous backpressure.
///
/// CRLF and a final unterminated line are supported; blank lines are rejected.
/// A later invalid request does not roll back already emitted complete results.
/// This is not Searchright event replay, durable checkpointing or atomic file I/O.
///
/// # Errors
/// Reports invalid framing, JSON/schema shape, semantic validation, denied
/// derived output or I/O failure, without returning raw input text.
pub fn run_jsonl<R: BufRead, W: Write>(
    mut input: R,
    mut output: W,
    limits: StreamLimits,
) -> Result<u64, StreamError> {
    if limits.max_line_bytes == 0 || limits.max_frames == 0 {
        return Err(StreamError::Limits);
    }
    let probe = limits.max_line_bytes.checked_add(1).ok_or(StreamError::Limits)?;
    let probe = u64::try_from(probe).map_err(|_| StreamError::Limits)?;
    let mut frames = 0_u64;
    let mut line = Vec::new();
    loop {
        line.clear();
        let count = (&mut input).take(probe).read_until(b'\n', &mut line).map_err(|_| StreamError::Input)?;
        if count == 0 {
            break;
        }
        let number = frames.checked_add(1).ok_or(StreamError::CountLimit)?;
        if count > limits.max_line_bytes {
            return Err(StreamError::FrameLimit(number));
        }
        if frames >= limits.max_frames {
            return Err(StreamError::CountLimit);
        }
        let request: CitationRequest = serde_json::from_slice(&line).map_err(|_| StreamError::InvalidFrame(number))?;
        if request.export != ExportPermission::Allowed {
            return Err(StreamError::Analysis { line: number, error: AnalysisError::ExportDenied });
        }
        let result = analyze(&request).map_err(|error| StreamError::Analysis { line: number, error })?;
        // Serialise before any write, so an encoding failure cannot emit a JSON prefix.
        let mut encoded = serde_json::to_vec(&result).map_err(|_| StreamError::Output)?;
        encoded.push(b'\n');
        output.write_all(&encoded).map_err(|_| StreamError::Output)?;
        output.flush().map_err(|_| StreamError::Output)?;
        frames = number;
    }
    Ok(frames)
}

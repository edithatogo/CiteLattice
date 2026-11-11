//! Offline, bounded citation summaries. Data use stdout; diagnostics use stderr.
use std::io;
use std::process::ExitCode;

use citelattice_analysis::{run_jsonl, StreamLimits};

fn main() -> ExitCode {
    let args: Vec<_> = std::env::args().skip(1).collect();
    if args == ["--help"] {
        println!("Usage: citelattice citation-summary < requests.jsonl > results.jsonl\nNo network. One versioned request per line; derived export must be allowed.");
        return ExitCode::SUCCESS;
    }
    if args != ["citation-summary"] {
        eprintln!("usage: citelattice citation-summary < requests.jsonl > results.jsonl");
        return ExitCode::from(2);
    }
    match run_jsonl(io::stdin().lock(), io::stdout().lock(), StreamLimits::default()) {
        Ok(_) => ExitCode::SUCCESS,
        Err(error) => {
            eprintln!("citelattice: {error}");
            ExitCode::FAILURE
        }
    }
}

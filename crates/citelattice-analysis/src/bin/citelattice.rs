//! Offline, bounded citation summaries. Data use stdout; diagnostics use stderr.
use std::io;
use std::process::ExitCode;

use citelattice_analysis::{StreamLimits, run_jsonl};
use clap::{Parser, Subcommand, error::ErrorKind};

#[derive(Parser)]
#[command(
    name = "citelattice",
    version,
    about = "Offline, versioned and bounded bibliometric summaries"
)]
struct Cli {
    #[command(subcommand)]
    command: Command,
}

#[derive(Subcommand)]
enum Command {
    /// Read versioned citation requests from JSONL stdin and write JSONL results.
    CitationSummary,
}

fn main() -> ExitCode {
    // Preserve the pre-existing root-help contract; Clap owns all other argument parsing.
    let args: Vec<_> = std::env::args().collect();
    if args.len() == 2 && args[1] == "--help" {
        println!(
            "Usage: citelattice citation-summary < requests.jsonl > results.jsonl\nNo network. One versioned request per line; derived export must be allowed."
        );
        return ExitCode::SUCCESS;
    }
    let cli = match Cli::try_parse_from(args) {
        Ok(cli) => cli,
        Err(error) => {
            if matches!(
                error.kind(),
                ErrorKind::DisplayHelp | ErrorKind::DisplayVersion
            ) {
                return if error.print().is_ok() {
                    ExitCode::SUCCESS
                } else {
                    ExitCode::FAILURE
                };
            }
            // Preserve existing exit code and the stderr-only diagnostic surface.
            eprintln!("usage: citelattice citation-summary < requests.jsonl > results.jsonl");
            return ExitCode::from(2);
        }
    };
    match cli.command {
        Command::CitationSummary => run_citation_summary(),
    }
}

fn run_citation_summary() -> ExitCode {
    match run_jsonl(
        io::stdin().lock(),
        io::stdout().lock(),
        StreamLimits::default(),
    ) {
        Ok(_) => ExitCode::SUCCESS,
        Err(error) => {
            eprintln!("citelattice: {error}");
            ExitCode::FAILURE
        }
    }
}

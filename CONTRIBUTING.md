# Contributing to CiteLattice

CiteLattice develops Rust bibliometrics, scientometrics and research-system mapping through explicit scientific and interchange contracts. Useful contributions include bounded analytical methods, independent reference fixtures, adapters and accurate documentation.

## Before you start

Read [AGENTS.md](AGENTS.md), [the Conductor index](conductor/index.md), the active track, [requirements](conductor/requirements.md) and [versioning guidance](docs/versioning.md). Reconcile existing issues and pull requests before starting. CSL-JSON remains canonical bibliographic interchange. Searchright owns acquisition, Sourceright reference integrity and CiteWeft document extraction; preserve those interfaces.

For bugs, provide the affected version or commit, environment, minimal reproduction, expected result and observed result. For a substantial proposal, describe the use case and compatibility impact in an issue before expanding implementation scope. Use existing issue templates when offered.

## Development and validation

Use the runtime and dependency setup in [Contracts and Rust core](.github/workflows/contracts.yml). The existing native checks are:

```sh
cargo fmt --all -- --check
cargo check --workspace
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace
```

After installing the workflow's pinned schema-validation dependencies in an isolated Python environment, run `python -m unittest discover -s tests -v`. The optional `backend-probes` workspace has separate qualification and is excluded from the default workspace; do not silently make it a core dependency.

Add independent expected results and invalid-input cases for changed methods or formats. Retain exact source provenance, missing-data semantics, rights and disclosure restrictions through tables, scenes and exports. Schemas and passing software checks alone do not establish scientific parity or rendering fidelity.

## Pull requests

Create a focused branch from the current `main` branch and submit a pull request to this repository. Link the relevant issue or existing Conductor task, explain the resulting behaviour, and update affected examples, contracts and documentation. Keep unrelated changes in separate pull requests.

Report executed commands, outcomes and the commit they validate. Identify unavailable checks and remaining limitations explicitly. Follow the repository's existing review and automated-check requirements; retain required gates and current ownership. Address findings and verify the final head before integration. Repository changes do not themselves authorise a release or external operational action.

## Security, rights and conduct

Follow the [security policy](https://github.com/edithatogo/.github/blob/main/SECURITY.md). Use private vulnerability reporting if available; otherwise request a private contact without publishing vulnerability details. Keep credentials, personal information and restricted source material out of issues, fixtures, logs and artifacts.

Preserve existing attribution and third-party terms. This guide does not grant a licence; clarify any unclear redistribution rights before contributing external material. Follow the [code of conduct](https://github.com/edithatogo/.github/blob/main/CODE_OF_CONDUCT.md) and keep technical discussions respectful.

## Basis for this guide

This guide follows [GitHub's contribution-guideline guidance](https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/setting-guidelines-for-repository-contributors) and the contribution-process and testing principles in [OpenSSF Best Practices](https://www.bestpractices.dev/en/criteria). It does not assert certification.

# CiteLattice Track 11 — synthetic temporal/decision protocol receipt

**Scope:** one offline, repository-authored synthetic protocol qualification for R04. This is a *gate and mathematical demonstration*, not an Innovate model fit, a Voiage VOI result, an empirical trial, or publication evidence. All new files stay in this Track 11 directory; upstream repositories, common method contracts, Cargo, CI and track registry are unchanged.

## Source and ownership reconciliation (19 November 2026)

- CiteLattice `main` `cfd72e73872b33ceddfc923381c51278f94ae428`: `conductor/tracks.md` calls Track 11 **specified**, while `conductor/evaluation-programme.json` defines R04 as **planned** and dependent on E05/E06/R01. `CL-016` is a **Should** requirement. `docs/studies/innovation-voi.md` is an intentionally proposed study, not a frozen external-data analysis.
- `contracts/methods/citation-summary.v1.json` describes **actual-N h/g/i10/totals** for an explicitly scoped publication population, citation universe, cutoff, source/version, permissions and missing-count semantics. It does **not** define adoption outcomes or an inference model. The method catalogue inventories Innovate forecasts and Voiage decision methods as not implemented *inside CiteLattice*; they must not be copied into this repository. The native citation method and Arrow/Parquet consumer interface were not exercised here.
- Innovate `main` `fd7e259bb9a685d620f80907c6815d4837da3e53`, `validation/benchmarks/protocol.py`: indexed chronological train/hold-out checks, training-only scaling and RMSE; the source alone does not establish family-held-out, bitemporal source lineage, non-finite-outcome rejection or independent empirical calibration. Its separate workstream owns those issues; this patch does not alter Innovate.
- Voiage `main` `3fdac2faa762afd24c09d1b0842e47651bf2f057`, `specs/ml-voi/schemas/v1/decision-focused-model-value.schema.json`: model-value and policy-regret vocabulary exists. Its `decision-problem.schema.json` requires an explicit net-benefit decision frame. Neither a citation count nor the toy ex-post oracle below is EVPI, EVSI, EVPPI or ENBS; no Voiage runtime was called.

## Frozen synthetic example

`protocol.json` pins exact repository revisions and labels data and forecast probabilities as invented, not provider-sourced or fitted. Across origins 2022-01-01 and 2023-01-01, family B is excluded from every training window. All scored labels occur after their origin; input signals require both publication time **and** first-observed time no later than that origin, matching technology IDs and `allowed_synthetic` rights. First-observed dates are independently checked; chronological publication dates alone are insufficient. The suite also refuses unknown source rights, future training labels, duplicate/missing forecasts, invalid probabilities, and unpinned revisions.

Four **invented** adoption labels are paired with two predeclared probability columns; the same labels and utility apply to both columns. The binary hypothetical policy has a threshold of 0.5, payoff 5 if adoption occurs and action cost 2 (abstract points, not money). The ex-post clairvoyant policy ceiling is 6. These values are deliberately chosen so predictive and decision rankings diverge:

| Toy probability column | Mean Brier loss (lower better) | Realised policy value | Ex-post policy regret (lower better) |
| --- | ---: | ---: | ---: |
| `count_proxy` | 0.185 | 0 | 6 |
| `structural_proxy` | 0.260 | 2 | 4 |

This is an algebraic known-answer counterexample, **not** evidence that structural bibliometrics outperform counts. No predictions were generated from CiteLattice, Innovate or Voiage. Since there is no joint posterior, study sampling model, independently measured utility or real source costs, **no VOI quantity is estimated**. Four toy observations do not establish forecast calibration. No Arrow/Parquet interoperability, reproducible engine execution or external rights clearance is claimed.

## Reproduction and admission boundary

From a checkout root, with Python 3.11+ and no third-party packages or network:

```sh
python -m unittest discover -s conductor/tracks/11-innovate-voiage -p test_protocol.py -v
python conductor/tracks/11-innovate-voiage/run_synthetic.py
sha256sum conductor/tracks/11-innovate-voiage/{protocol.json,run_synthetic.py,test_protocol.py}
```

`receipt.json` records the independently executed local Python 3.13.5 run, exact SHA-256 bytes, case counts and outputs. This track-local test is **not** wired into shared hosted CI, nor was the full CiteLattice workspace available locally. The branch requires ordinary maintainer review; evidence is insufficient to promote R04 or Track 11 to empirical acceptance.

**Next dependency-ordered handoff:** qualify E05/E06/R01; freeze independent real adoption outcomes and licences/rights/source costs; pin accepted runnable Innovate/Voiage artifacts and Arrow/Parquet schemas; preregister rolling-origin and family hold-outs, forecast calibration, scenario utilities, uncertainty, costs and meaningful thresholds before confirmation. Evaluate source-cost/rights and perspective heterogeneity, retain null/negative results, and independently reproduce before any empirical or publication claim. Integrator alone decides admission and shared registry updates.

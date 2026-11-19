"""Offline synthetic Track 11 protocol gate; does not call Innovate or Voiage.

The supplied probabilities and binary outcomes are authored toy numbers, not
fitted forecasts. Policy regret here is ex-post, not EVPI, EVSI, or ENBS.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from datetime import datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _utc(value: str) -> datetime:
    _require(isinstance(value, str) and value.endswith("Z"), "timestamp must be UTC Z")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError("invalid timestamp") from error
    _require(parsed.utcoffset() == timedelta(0), "timestamp must be UTC")
    return parsed


def _shape(row: dict, keys: set[str], label: str) -> None:
    _require(isinstance(row, dict) and set(row) == keys, f"invalid {label} fields")


def _by_unique_id(rows: list[dict], field: str = "id") -> dict:
    _require(isinstance(rows, list), "invalid rows")
    _require(all(isinstance(row, dict) and isinstance(row.get(field), str)
                 and bool(row[field]) for row in rows), f"invalid {field}")
    ids = [row[field] for row in rows]
    _require(len(ids) == len(set(ids)), f"duplicate {field}")
    return {row[field]: row for row in rows}


def qualify(protocol: dict) -> dict:
    """Fail closed on invalid frozen synthetic data; score declared candidates."""
    try:
        return _qualify(protocol)
    except (KeyError, TypeError, IndexError, AttributeError, OverflowError) as error:
        raise ValueError("invalid synthetic protocol structure") from error


def _qualify(protocol: dict) -> dict:
    """Internal strict validator for a single frozen synthetic study fixture."""
    _shape(protocol, {"schema_version", "evidence_level", "research_task", "rights",
                      "contract_pins", "design", "sources", "signals", "outcomes",
                      "splits", "forecast_receipts", "known_answers", "non_claims"}, "protocol")
    _require(protocol["schema_version"] == "org.citelattice.track11.synthetic-study.v1", "unsupported protocol")
    _require(protocol["research_task"] == "R04", "wrong research task")
    _require(protocol["evidence_level"] == "synthetic_protocol_qualification_only", "claim escalation")
    rights = protocol["rights"]
    _require(rights == {
        "data_origin": "repository_authored_synthetic_only",
        "external_corpus_queried": False,
        "licensed_or_personal_data": False,
        "redistribution_status": "synthetic_only",
        "provider_entitlement_verified": False,
    }, "external or unqualified source cannot be used")
    _shape(protocol["contract_pins"], {"citelattice", "innovate", "voiage"}, "contract pins")
    _shape(protocol["contract_pins"]["citelattice"],
           {"revision", "method_id", "method_version", "method_contract", "runtime_executed"}, "CiteLattice pin")
    for name in ("innovate", "voiage"):
        _shape(protocol["contract_pins"][name],
               {"revision", "reference_contract", "runtime_executed"}, f"{name} pin")
    _require(protocol["non_claims"] == [
        "no_innovate_fit_or_scoring_executed",
        "no_voiage_evpi_evppi_evsi_or_enbs_executed",
        "no_licensed_source_or_real_adoption_data",
        "no_empirical_or_publication_conclusions",
    ], "unauthorised scientific claim")
    frozen_pins = {
        "citelattice": ("cfd72e73872b33ceddfc923381c51278f94ae428",
                       "method_contract", "contracts/methods/citation-summary.v1.json"),
        "innovate": ("fd7e259bb9a685d620f80907c6815d4837da3e53",
                     "reference_contract", "validation/benchmarks/protocol.py"),
        "voiage": ("3fdac2faa762afd24c09d1b0842e47651bf2f057",
                    "reference_contract", "specs/ml-voi/schemas/v1/decision-focused-model-value.schema.json"),
    }
    for name, (revision, field, path) in frozen_pins.items():
        pin = protocol["contract_pins"][name]
        _require(pin["revision"] == revision and pin[field] == path, "unreviewed contract revision or path")
        _require(pin["runtime_executed"] is False, "this protocol has no upstream runtime")
    _require(protocol["contract_pins"]["citelattice"]["method_id"] == "org.citelattice.citation-summary.actual-n", "method mismatch")
    _require(protocol["contract_pins"]["citelattice"]["method_version"] == "1.0.0", "method version mismatch")
    sources = _by_unique_id(protocol["sources"])
    _require(len(sources) > 0, "missing source")
    for source in sources.values():
        _shape(source, {"id", "version", "source_rights", "citation_universe", "method_receipt"}, "source")
        _require(source["version"] == "synthetic.1", "unqualified synthetic source version")
        _require(source["source_rights"] == "allowed_synthetic" and source["method_receipt"] == "not_executed", "source rights or method receipt not allowed")
        _require(bool(source["citation_universe"]), "unknown citation universe")

    design = protocol["design"]
    _shape(design, {"origins", "horizon_days", "technology_family_holdout", "candidate_ids",
                    "model_origin", "outcome_origin", "primary_prediction_loss", "decision_endpoint",
                    "decision"}, "design")
    _require(design["primary_prediction_loss"] == "mean_brier_loss_lower_is_better",
             "unsupported prediction loss")
    _require(design["decision_endpoint"] == "ex_post_policy_regret_lower_is_better_not_evpi",
             "unsupported decision endpoint")
    origins = [_utc(v) for v in design["origins"]]
    _require(len(origins) >= 2 and all(a < b for a, b in zip(origins, origins[1:])), "origins are not increasing")
    _require(type(design["horizon_days"]) is int and design["horizon_days"] > 0, "invalid horizon")
    horizon = timedelta(days=design["horizon_days"])
    _require(isinstance(design["technology_family_holdout"], list)
             and all(isinstance(v, str) and bool(v) for v in design["technology_family_holdout"]),
             "invalid family holdout")
    holdout_families = set(design["technology_family_holdout"])
    _require(len(holdout_families) == len(design["technology_family_holdout"]),
             "duplicate family holdout")
    _require(len(holdout_families) > 0, "no family holdout")
    candidates = design["candidate_ids"]
    _require(isinstance(candidates, list)
             and all(isinstance(v, str) and bool(v) for v in candidates), "invalid candidates")
    _require(len(candidates) == len(set(candidates)) and len(candidates) >= 2, "bad candidates")
    _require(design["model_origin"] == "predeclared_toy_probabilities_not_innovate_execution", "model cannot be claimed as fitted")
    _require(design["outcome_origin"] == "invented_binary_adoption_labels_not_empirical_data", "no observed empirical outcomes")
    decision = design["decision"]
    _shape(decision, {"alternatives", "decision_perspective", "population", "horizon", "utility_unit",
                      "payoff_when_adopted", "cost_per_action", "decision_probability_threshold",
                      "source_cost", "study_cost", "joint_uncertainty"}, "decision")
    _require(decision["decision_perspective"] == "one_abstract_synthetic_decision_maker"
             and decision["population"] == "four_abstract_technology_years"
             and decision["horizon"] == "one_year_per_origin"
             and decision["utility_unit"] == "hypothetical_points_not_currency",
             "decision framing mismatch")
    _require(decision["alternatives"] == ["act", "do_not_act"], "unsupported actions")
    _require(decision["joint_uncertainty"] == "not_specified_no_voi_permitted", "VOI is out of scope")
    _require(decision["study_cost"] is None and decision["source_cost"] == 0, "cost or study not qualified")
    threshold = decision["decision_probability_threshold"]
    payoff = decision["payoff_when_adopted"]
    action_cost = decision["cost_per_action"]
    _require(all(type(v) in (int, float) and math.isfinite(v) for v in (threshold, payoff, action_cost)), "invalid decision numbers")
    _require(0 < threshold < 1 and payoff > action_cost > 0, "invalid decision threshold or net benefit")
    _require(math.isclose(threshold, action_cost / payoff, rel_tol=0, abs_tol=1e-12),
             "policy threshold must equal cost/payoff for declared net benefit")
    outcomes = _by_unique_id(protocol["outcomes"])
    families_by_technology: dict[str, str] = {}
    for outcome in outcomes.values():
        _shape(outcome, {"id", "technology_id", "family", "first_observed_at", "adopted"}, "outcome")
        _utc(outcome["first_observed_at"])
        _require(type(outcome["adopted"]) is int and outcome["adopted"] in (0, 1), "nonbinary toy adoption")
        _require(bool(outcome["family"]) and bool(outcome["technology_id"])
                 and isinstance(outcome["family"], str)
                 and isinstance(outcome["technology_id"], str), "untyped outcome")
        previous = families_by_technology.setdefault(outcome["technology_id"], outcome["family"])
        _require(previous == outcome["family"], "technology changes family across labels")
    _require(holdout_families.issubset(families_by_technology.values()), "unknown holdout family")
    signals = _by_unique_id(protocol["signals"])
    for signal in signals.values():
        _shape(signal, {"id", "technology_id", "source_id", "published_at",
                        "first_observed_at", "source_rights"}, "signal")
        _require(signal["source_id"] in sources, "unknown source")
        _require(signal["source_rights"] == "allowed_synthetic", "disallowed signal")
        _utc(signal["published_at"])
        _utc(signal["first_observed_at"])

    splits = protocol["splits"]
    _require([s["origin"] for s in splits] == design["origins"], "unfrozen split/origin mismatch")
    targets: dict[tuple[str, str], dict] = {}
    folds: list[dict] = []
    for split in splits:
        _shape(split, {"origin", "train_ids", "evaluation_ids"}, "split")
        origin_key = split["origin"]
        origin = _utc(origin_key)
        train = split["train_ids"]
        evaluation = split["evaluation_ids"]
        _require(isinstance(train, list) and isinstance(evaluation, list)
                 and all(isinstance(v, str) for v in train + evaluation), "invalid split identifiers")
        _require(bool(train) and bool(evaluation) and len(train) == len(set(train))
                 and len(evaluation) == len(set(evaluation)), "empty or duplicate split")
        _require(set(train).isdisjoint(evaluation), "training/test overlap")
        _require(set(train + evaluation).issubset(outcomes), "split references missing outcome")
        for outcome_id in train:
            label = outcomes[outcome_id]
            _require(label["family"] not in holdout_families, "family holdout contaminated training")
            _require(_utc(label["first_observed_at"]) <= origin, "train label observed after cutoff")
        n_heldout = sum(outcomes[id_]["family"] in holdout_families for id_ in evaluation)
        _require(n_heldout > 0, "no heldout family evaluated")
        folds.append({
            "origin": origin_key,
            "n_training_labels": len(train),
            "n_seen_family_scored": len(evaluation) - n_heldout,
            "n_heldout_family_scored": n_heldout,
        })
        for outcome_id in evaluation:
            label = outcomes[outcome_id]
            observed_at = _utc(label["first_observed_at"])
            _require(origin < observed_at <= origin + horizon, "test label is not in future horizon")
            key = origin_key, outcome_id
            _require(key not in targets, "duplicate target")
            targets[key] = label
    forecast_rows = protocol["forecast_receipts"]
    forecasts: dict[tuple[str, str], dict] = {}
    for row in forecast_rows:
        _shape(row, {"origin", "outcome_id", "signal_id", "probabilities"}, "forecast")
        key = row["origin"], row["outcome_id"]
        _require(key in targets and key not in forecasts, "unknown or duplicate forecast")
        _require(row["signal_id"] in signals, "missing source evidence")
        signal = signals[row["signal_id"]]
        _require(signal["technology_id"] == targets[key]["technology_id"], "signal identity mismatch")
        origin = _utc(row["origin"])
        _require(_utc(signal["published_at"]) <= origin, "publication after forecast origin")
        _require(_utc(signal["first_observed_at"]) <= origin, "first observation after forecast origin")
        probs = row["probabilities"]
        _require(set(probs) == set(candidates), "missing or unexpected candidate")
        for value in probs.values():
            _require(type(value) in (int, float) and math.isfinite(value) and 0 <= value <= 1, "invalid forecast probability")
        forecasts[key] = probs
    _require(forecasts.keys() == targets.keys(), "incomplete forecast matrix")

    rows = [(targets[key]["adopted"], forecasts[key]) for key in sorted(targets)]

    def metrics_for(subset: list[tuple[int, dict]]) -> dict:
        _require(bool(subset), "empty evaluation stratum")
        oracle_value = sum(max(0, payoff * y - action_cost) for y, _ in subset)
        result = {}
        for candidate in candidates:
            brier = math.fsum((p[candidate] - y) ** 2 for y, p in subset) / len(subset)
            realized = sum((payoff * y - action_cost) for y, p in subset if p[candidate] >= threshold)
            result[candidate] = {
                "brier": brier,
                "realized_value": realized,
                "ex_post_oracle_value": oracle_value,
                "policy_regret": oracle_value - realized,
            }
        return result

    metrics = metrics_for(rows)
    strata = {}
    for label, is_heldout in (("seen_family", False), ("heldout_family", True)):
        subset = [(targets[key]["adopted"], forecasts[key]) for key in sorted(targets)
                  if (targets[key]["family"] in holdout_families) == is_heldout]
        strata[label] = {"n": len(subset), "models": metrics_for(subset)}
    _shape(protocol["known_answers"], set(candidates), "known answers")
    for candidate, expected in protocol["known_answers"].items():
        _shape(expected, {"brier", "realized_value", "ex_post_oracle_value", "policy_regret"},
               "known answer")
        for field, value in expected.items():
            _require(type(value) in (float, int) and math.isfinite(value)
                     and math.isclose(value, metrics[candidate][field], rel_tol=0, abs_tol=1e-12),
                     "known-answer discrepancy")
    return {
        "status": "synthetic_only",
        "research_task": "R04",
        "n_origins": len(origins),
        "n_evaluation_rows": len(rows),
        "folds": folds,
        "family_strata": strata,
        "models": metrics,
        "voi_calculated": False,
        "empirical_claim": False,
    }


def verify_receipt(root: Path) -> dict:
    """Verify exact fixture bytes, scoped rights and computed result before output.

    The receipt is local integrity metadata, not an external signature or proof
    of entitlement, model validity or independent empirical replication.
    """
    try:
        receipt = json.loads((root / "receipt.json").read_text())
        _shape(receipt, {"receipt_schema", "evidence_date", "environment", "scope",
                         "command", "result", "benchmark_command", "benchmark_output",
                         "file_sha256", "hosted_ci", "upstream_innovate_voiage",
                         "empirical_data", "publication_status"}, "receipt")
        _require(receipt["receipt_schema"] == "org.citelattice.track11.synthetic-evidence.v1", "unsupported receipt")
        _require(receipt["scope"] == "track_11_only; local source tests; upstream engines not executed",
                 "receipt scope escalation")
        _require(receipt["upstream_innovate_voiage"] == "not_executed"
                 and receipt["empirical_data"] == "none"
                 and receipt["publication_status"] == "none", "unjustified receipt claim")
        hashes = receipt["file_sha256"]
        _shape(hashes, {"protocol.json", "run_synthetic.py", "test_protocol.py"}, "file digests")
        for filename, recorded in hashes.items():
            _require(isinstance(recorded, str) and re.fullmatch(r"[0-9a-f]{64}", recorded) is not None,
                     "invalid digest")
            _require(hashlib.sha256((root / filename).read_bytes()).hexdigest() == recorded,
                     "source file digest mismatch")
        observed = qualify(json.loads((root / "protocol.json").read_text()))
        _require(observed == receipt["benchmark_output"], "frozen synthetic output mismatch")
        return receipt
    except (KeyError, TypeError, OSError, json.JSONDecodeError) as error:
        raise ValueError("invalid or incomplete synthetic evidence bundle") from error


def main() -> None:
    receipt = verify_receipt(HERE)
    print(json.dumps(receipt["benchmark_output"], sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()

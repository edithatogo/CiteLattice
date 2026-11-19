"""Offline synthetic Track 11 protocol gate; does not call Innovate or Voiage.

The supplied probabilities and binary outcomes are authored toy numbers, not
fitted forecasts. Policy regret here is ex-post, not EVPI, EVSI, or ENBS.
"""
from __future__ import annotations

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


def _by_unique_id(rows: list[dict], field: str = "id") -> dict:
    ids = [row[field] for row in rows]
    _require(len(ids) == len(set(ids)), f"duplicate {field}")
    return {row[field]: row for row in rows}


def qualify(protocol: dict) -> dict:
    """Fail closed on invalid frozen synthetic data; score declared candidates."""
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
    for name in ("citelattice", "innovate", "voiage"):
        pin = protocol["contract_pins"][name]
        _require(re.fullmatch(r"[0-9a-f]{40}", pin["revision"]) is not None, "unpinned revision")
        _require(pin["runtime_executed"] is False, "this protocol has no upstream runtime")
    _require(protocol["contract_pins"]["citelattice"]["method_id"] == "org.citelattice.citation-summary.actual-n", "method mismatch")
    _require(protocol["contract_pins"]["citelattice"]["method_version"] == "1.0.0", "method version mismatch")
    sources = _by_unique_id(protocol["sources"])
    _require(len(sources) > 0, "missing source")
    for source in sources.values():
        _require(source["source_rights"] == "allowed_synthetic" and source["method_receipt"] == "not_executed", "source rights or method receipt not allowed")
        _require(bool(source["citation_universe"]), "unknown citation universe")

    design = protocol["design"]
    origins = [_utc(v) for v in design["origins"]]
    _require(len(origins) >= 2 and all(a < b for a, b in zip(origins, origins[1:])), "origins are not increasing")
    _require(type(design["horizon_days"]) is int and design["horizon_days"] > 0, "invalid horizon")
    horizon = timedelta(days=design["horizon_days"])
    holdout_families = set(design["technology_family_holdout"])
    _require(len(holdout_families) > 0, "no family holdout")
    candidates = design["candidate_ids"]
    _require(len(candidates) == len(set(candidates)) and len(candidates) >= 2, "bad candidates")
    _require(design["model_origin"] == "predeclared_toy_probabilities_not_innovate_execution", "model cannot be claimed as fitted")
    _require(design["outcome_origin"] == "invented_binary_adoption_labels_not_empirical_data", "no observed empirical outcomes")
    decision = design["decision"]
    _require(decision["alternatives"] == ["act", "do_not_act"], "unsupported actions")
    _require(decision["joint_uncertainty"] == "not_specified_no_voi_permitted", "VOI is out of scope")
    _require(decision["study_cost"] is None and decision["source_cost"] == 0, "cost or study not qualified")
    threshold = decision["decision_probability_threshold"]
    payoff = decision["payoff_when_adopted"]
    action_cost = decision["cost_per_action"]
    _require(all(type(v) in (int, float) and math.isfinite(v) for v in (threshold, payoff, action_cost)), "invalid decision numbers")
    _require(0 < threshold < 1 and payoff > action_cost >= 0, "invalid decision threshold or net benefit")
    outcomes = _by_unique_id(protocol["outcomes"])
    for outcome in outcomes.values():
        _utc(outcome["first_observed_at"])
        _require(type(outcome["adopted"]) is int and outcome["adopted"] in (0, 1), "nonbinary toy adoption")
        _require(bool(outcome["family"]) and bool(outcome["technology_id"]), "untyped outcome")
    signals = _by_unique_id(protocol["signals"])
    for signal in signals.values():
        _require(signal["source_id"] in sources, "unknown source")
        _require(signal["source_rights"] == "allowed_synthetic", "disallowed signal")
        _utc(signal["published_at"])
        _utc(signal["first_observed_at"])

    splits = protocol["splits"]
    _require([s["origin"] for s in splits] == design["origins"], "unfrozen split/origin mismatch")
    targets: dict[tuple[str, str], dict] = {}
    for split in splits:
        origin_key = split["origin"]
        origin = _utc(origin_key)
        train = split["train_ids"]
        evaluation = split["evaluation_ids"]
        _require(bool(train) and bool(evaluation) and len(train) == len(set(train)) and len(evaluation) == len(set(evaluation)), "empty or duplicate split")
        _require(set(train).isdisjoint(evaluation), "training/test overlap")
        _require(set(train + evaluation).issubset(outcomes), "split references missing outcome")
        for outcome_id in train:
            label = outcomes[outcome_id]
            _require(label["family"] not in holdout_families, "family holdout contaminated training")
            _require(_utc(label["first_observed_at"]) <= origin, "train label observed after cutoff")
        _require(any(outcomes[id_]["family"] in holdout_families for id_ in evaluation), "no heldout family evaluated")
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
    oracle_value = sum(max(0, payoff * y - action_cost) for y, _ in rows)
    metrics = {}
    for candidate in candidates:
        brier = math.fsum((p[candidate] - y) ** 2 for y, p in rows) / len(rows)
        realized = sum((payoff * y - action_cost) for y, p in rows if p[candidate] >= threshold)
        metrics[candidate] = {
            "brier": brier,
            "realized_value": realized,
            "ex_post_oracle_value": oracle_value,
            "policy_regret": oracle_value - realized,
        }
    return {
        "status": "synthetic_only",
        "research_task": "R04",
        "n_origins": len(origins),
        "n_evaluation_rows": len(rows),
        "models": metrics,
        "voi_calculated": False,
        "empirical_claim": False,
    }


def main() -> None:
    protocol = json.loads((HERE / "protocol.json").read_text())
    print(json.dumps(qualify(protocol), sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()

"""Track 11 synthetic protocol gate; the expected answers are independently authored."""
from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from run_synthetic import qualify, verify_receipt

PROTOCOL = json.loads((Path(__file__).with_name("protocol.json")).read_text())


class Track11Tests(unittest.TestCase):
    def test_known_answer_separates_forecast_and_decision(self):
        got = qualify(copy.deepcopy(PROTOCOL))
        self.assertEqual(got["status"], "synthetic_only")
        self.assertEqual(got["n_evaluation_rows"], 4)
        self.assertEqual(got["n_origins"], 2)
        for model_id, expected in PROTOCOL["known_answers"].items():
            with self.subTest(model_id=model_id):
                for field, value in expected.items():
                    self.assertAlmostEqual(got["models"][model_id][field], value, places=12)
        self.assertLess(got["models"]["count_proxy"]["brier"], got["models"]["structural_proxy"]["brier"])
        self.assertGreater(got["models"]["count_proxy"]["policy_regret"], got["models"]["structural_proxy"]["policy_regret"])
        self.assertFalse(got["voi_calculated"])

    def rejects(self, mutator):
        protocol = copy.deepcopy(PROTOCOL)
        mutator(protocol)
        with self.assertRaises(ValueError):
            qualify(protocol)

    def test_future_first_observed_signal_rejected(self):
        self.rejects(lambda p: p["signals"][0].update(first_observed_at="2022-02-01T00:00:00Z"))

    def test_future_publication_even_if_first_observed_is_early_rejected(self):
        self.rejects(lambda p: p["signals"][0].update(published_at="2022-02-01T00:00:00Z"))

    def test_unlicensed_signal_rejected(self):
        self.rejects(lambda p: p["signals"][0].update(source_rights="denied"))

    def test_unlicensed_source_rejected(self):
        self.rejects(lambda p: p["sources"][0].update(source_rights="denied"))

    def test_technology_family_holdout_is_not_training(self):
        self.rejects(lambda p: p["splits"][1]["train_ids"].append("b_2022"))

    def test_future_label_cannot_be_used_in_training(self):
        self.rejects(lambda p: p["splits"][0]["train_ids"].append("a_2022"))

    def test_future_label_cannot_be_evaluated_at_origin(self):
        self.rejects(lambda p: p["outcomes"][2].update(first_observed_at="2021-12-15T00:00:00Z"))

    def test_duplicate_prediction_rejected(self):
        self.rejects(lambda p: p["forecast_receipts"].append(copy.deepcopy(p["forecast_receipts"][0])))

    def test_missing_candidate_forecast_rejected(self):
        self.rejects(lambda p: p["forecast_receipts"][0]["probabilities"].pop("count_proxy"))

    def test_non_finite_or_out_of_range_prediction_rejected(self):
        for bad in [float("nan"), float("inf"), -0.01, 1.01, True]:
            with self.subTest(bad=bad):
                self.rejects(lambda p: p["forecast_receipts"][0]["probabilities"].update(count_proxy=bad))

    def test_unpinned_sources_fail_closed(self):
        self.rejects(lambda p: p["contract_pins"]["innovate"].update(revision="main"))

    def test_non_synthetic_data_cannot_be_admitted(self):
        self.rejects(lambda p: p["rights"].update(licensed_or_personal_data=True))

    def test_zero_cost_is_not_an_evpi_or_evsi_claim(self):
        self.rejects(lambda p: p["design"]["decision"].update(joint_uncertainty="qualified"))


    def test_decision_threshold_matches_net_benefit_rule(self):
        self.assertAlmostEqual(
            PROTOCOL["design"]["decision"]["decision_probability_threshold"],
            PROTOCOL["design"]["decision"]["cost_per_action"]
            / PROTOCOL["design"]["decision"]["payoff_when_adopted"],
            places=12,
        )
        self.rejects(lambda p: p["design"]["decision"].update(decision_probability_threshold=0.9))

    def test_same_technology_cannot_change_family_between_labels(self):
        self.rejects(lambda p: p["outcomes"][2].update(family="family_b"))

    def test_undeclared_payload_fields_cannot_bypass_rights_or_provenance(self):
        for path in (
            lambda p: p.update(empirical_results={"adoption": 100}),
            lambda p: p["sources"][0].update(licensed_source=True),
            lambda p: p["signals"][0].update(personal_data="opaque"),
            lambda p: p["outcomes"][0].update(independent_provider_truth=True),
            lambda p: p["forecast_receipts"][0].update(engines_run=["innovate"]),
        ):
            with self.subTest(path=path):
                self.rejects(path)

    def test_falsified_rights_and_claim_flags_rejected(self):
        self.rejects(lambda p: p["non_claims"].append("real_study_completed"))
        self.rejects(lambda p: p["contract_pins"]["voiage"].update(
            empirical_validated=True,
        ))

    def test_unlisted_predictions_are_rejected(self):
        self.rejects(lambda p: p["forecast_receipts"][0]["probabilities"].update(
            unexpected_candidate=0.8,
        ))

    def test_missing_family_holdout_label_at_origin_rejected(self):
        self.rejects(lambda p: p["splits"][1]["evaluation_ids"].remove("b_2023"))

    def test_pinned_receipt_recomputes_outputs_and_hashes(self):
        result = verify_receipt(Path(__file__).parent)
        self.assertEqual(result["benchmark_output"], qualify(copy.deepcopy(PROTOCOL)))
        self.assertEqual(result["result"]["errors"], 0)

    def test_digest_check_rejects_tampered_protocol(self):
        import tempfile
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name in ("protocol.json", "run_synthetic.py", "test_protocol.py", "receipt.json"):
                (root / name).write_bytes(Path(__file__).with_name(name).read_bytes())
            good = json.loads((root / "protocol.json").read_text())
            good["forecast_receipts"][0]["probabilities"]["count_proxy"] = 0.99
            (root / "protocol.json").write_text(json.dumps(good))
            with self.assertRaises(ValueError):
                verify_receipt(root)

    def test_forged_known_answer_rejected(self):
        self.rejects(lambda p: p["known_answers"]["count_proxy"].update(policy_regret=-1))

    def test_revision_pins_must_match_audited_contract_sources(self):
        self.rejects(lambda p: p["contract_pins"]["innovate"].update(revision="a" * 40))
        self.rejects(lambda p: p["contract_pins"]["voiage"].update(
            reference_contract="unreviewed/decision_model.py",
        ))

    def test_invalid_payload_shapes_raise_fail_closed_value_error(self):
        for edit in (
            lambda p: p.update(outcomes={}),
            lambda p: p["design"].update(candidate_ids=[[]]),
            lambda p: p["splits"][0].update(train_ids=[{}]),
            lambda p: p["signals"][0].update(first_observed_at=None),
        ):
            with self.subTest(edit=edit):
                self.rejects(edit)

    def test_each_origin_reports_split_and_family_denominators(self):
        observed = qualify(copy.deepcopy(PROTOCOL))
        self.assertEqual([f["origin"] for f in observed["folds"]], PROTOCOL["design"]["origins"])
        self.assertEqual([f["n_training_labels"] for f in observed["folds"]], [2, 3])
        self.assertEqual([f["n_seen_family_scored"] for f in observed["folds"]], [1, 1])
        self.assertEqual([f["n_heldout_family_scored"] for f in observed["folds"]], [1, 1])
        self.assertEqual(set(observed["family_strata"]), {"seen_family", "heldout_family"})
        self.assertEqual(observed["family_strata"]["seen_family"]["n"], 2)
        self.assertEqual(observed["family_strata"]["heldout_family"]["n"], 2)
        for stratum in observed["family_strata"].values():
            self.assertAlmostEqual(stratum["models"]["count_proxy"]["brier"], 0.19105)
            self.assertAlmostEqual(stratum["models"]["structural_proxy"]["brier"], 0.26)

    def test_closed_world_family_holdout_rule(self):
        self.rejects(lambda p: p["design"].update(
            technology_family_holdout=["family_missing"],
        ))

if __name__ == "__main__":
    unittest.main()

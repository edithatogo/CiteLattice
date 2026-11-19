"""Track 11 synthetic protocol gate; the expected answers are independently authored."""
from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from run_synthetic import qualify

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


if __name__ == "__main__":
    unittest.main()

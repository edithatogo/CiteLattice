"""Design contract validation; do not confuse passing schemas with scientific fidelity."""
import copy
import hashlib
import json
import unittest
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]

def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))

class ContractTests(unittest.TestCase):
    def test_searchright_source_schema_is_exact_pinned_copy(self):
        raw = (ROOT / "contracts/interop/scholarly-stream.v1.schema.json").read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), "730f7d374185ed523ce7f362983933d0bdd20443ae047751cfbee9aef622d7ed")

    def test_searchright_fixture_and_strict_dates(self):
        schema = load("contracts/interop/scholarly-stream.v1.schema.json")
        fixture = load("contracts/interop/examples/scholarly-stream-upsert.json")
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        validator.validate(fixture)
        invalid = copy.deepcopy(fixture)
        invalid["observed_at"] = "yesterday"
        self.assertTrue(list(validator.iter_errors(invalid)))
        invalid = copy.deepcopy(fixture)
        invalid["sequence"] = 2
        self.assertTrue(list(validator.iter_errors(invalid)))
        invalid = copy.deepcopy(fixture)
        invalid["version"] = "2.0.0"
        self.assertTrue(list(validator.iter_errors(invalid)))

    def test_contract_schemas_and_examples(self):
        for name in ("table", "scene", "method"):
            with self.subTest(contract=name):
                path = f"contracts/json-schema/{name}.contract.schema.json"
                schema = load(path)
                Draft202012Validator.check_schema(schema)
                validator = Draft202012Validator(schema)
                fixture = load(f"contracts/json-schema/examples/{name}.json")
                validator.validate(fixture)
                invalid = copy.deepcopy(fixture)
                invalid["unexpected"] = "not allowed"
                self.assertTrue(list(validator.iter_errors(invalid)))

    def test_no_scientific_capability_is_promoted_by_inventory(self):
        catalog = load("contracts/methods/catalog.json")
        self.assertEqual(catalog["count"], len(catalog["outcomes"]))
        self.assertEqual(catalog["count"], 147)
        self.assertEqual(len({o["id"] for o in catalog["outcomes"]}), 147)
        self.assertTrue(all(o["status"] == "inventoried_not_implemented" for o in catalog["outcomes"]))

    def test_format_registry_has_nonfictional_status(self):
        reg = load("contracts/formats.json")
        self.assertGreaterEqual(len(reg["formats"]), 20)
        self.assertTrue(all(f["status"] == "adapter_planned" for f in reg["formats"]))
        self.assertEqual(len({f["id"] for f in reg["formats"]}), len(reg["formats"]))

    def test_scene_does_not_accept_undeclared_uncertainty(self):
        schema = load("contracts/json-schema/scene.contract.schema.json")
        scene = load("contracts/json-schema/examples/scene.json")
        scene["marks"][0]["uncertainty"] = ["color_confidence"]
        self.assertTrue(list(Draft202012Validator(schema).iter_errors(scene)))

if __name__ == "__main__":
    unittest.main()

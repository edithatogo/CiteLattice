"""Contract shape tests. Rust native tests provide semantic replay evidence."""
import copy
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]

class EventSnapshotSchemaTests(unittest.TestCase):
    def test_snapshot_example_and_invalid_states(self):
        schema = json.loads((ROOT / "contracts/json-schema/scholarly-event-snapshot.v1.schema.json").read_text())
        fixture = json.loads((ROOT / "contracts/json-schema/examples/scholarly-event-snapshot.json").read_text())
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema)
        validator.validate(fixture)
        invalid = copy.deepcopy(fixture)
        invalid["objects"][0]["state"] = "unverified_miracle"
        self.assertTrue(list(validator.iter_errors(invalid)))
        invalid = copy.deepcopy(fixture)
        invalid["objects"][0]["private_abstract"] = "should never be present"
        self.assertTrue(list(validator.iter_errors(invalid)))

    def test_schema_does_not_allow_unknown_result_major_version(self):
        schema = json.loads((ROOT / "contracts/json-schema/scholarly-event-snapshot.v1.schema.json").read_text())
        fixture = json.loads((ROOT / "contracts/json-schema/examples/scholarly-event-snapshot.json").read_text())
        fixture["version"] = "2.0.0"
        self.assertTrue(list(Draft202012Validator(schema).iter_errors(fixture)))

if __name__ == "__main__":
    unittest.main()

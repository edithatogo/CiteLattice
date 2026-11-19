"""Track 05 source-neutral transport contract smoke test, not an entitlement test.

Uses synthetic nonpublication records and the pre-existing Searchright stream
schema. Passing does not demonstrate native ingestion, provider coverage,
redistribution permission, cross-domain matching or numerical accuracy.
"""

import copy
import hashlib
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
KINDS = ("grant", "patent", "clinical_trial", "policy_document", "dataset")


class Track05RightsTransportTests(unittest.TestCase):
    def test_all_five_nonpublication_kinds_require_explicit_rights_and_record(self):
        schema = json.loads(
            (ROOT / "contracts/interop/scholarly-stream.v1.schema.json").read_text(
                encoding="utf-8"
            )
        )
        fixture = json.loads(
            (ROOT / "contracts/interop/examples/scholarly-stream-upsert.json").read_text(
                encoding="utf-8"
            )
        )
        validator = Draft202012Validator(schema, format_checker=FormatChecker())

        for kind in KINDS:
            with self.subTest(kind=kind):
                event = copy.deepcopy(fixture)
                event["event_id"] = f"synthetic-{kind}-upsert"
                event["change"]["object"] = {
                    "kind": kind,
                    "key": f"synthetic:{kind}:1",
                    "record": {
                        "id": f"synthetic:{kind}:record",
                        "schema_id": "synthetic.research-object.v1",
                        "digest": {"algorithm": "sha256", "hex": "a" * 64},
                        "media_type": "application/json",
                    },
                    "extensions": [],
                }
                # Unknown and restricted are transport classifications, never
                # evidence that any content may be redistributed.
                event["rights"]["metadata"] = "unknown"
                event["rights"]["abstracts"] = "restricted"
                event["rights"]["full_text"] = "absent"
                event["payload_digest"]["hex"] = hashlib.sha256(
                    json.dumps(
                        event["change"], sort_keys=True, separators=(",", ":")
                    ).encode("ascii")
                ).hexdigest()  # Canonical for these ASCII, integer-free payloads.
                self.assertEqual([], list(validator.iter_errors(event)))
                self.assertEqual("unknown", event["rights"]["metadata"])

                for field, value in (
                    ("metadata", "absent"),
                    ("abstracts", "unverified_export_allowed"),
                ):
                    bad = copy.deepcopy(event)
                    bad["rights"][field] = value
                    self.assertTrue(
                        list(validator.iter_errors(bad)),
                        f"{kind}: unexpected {field} classification passed",
                    )

                missing_policy = copy.deepcopy(event)
                del missing_policy["rights"]["policy"]
                self.assertTrue(list(validator.iter_errors(missing_policy)))

                missing_record = copy.deepcopy(event)
                del missing_record["change"]["object"]["record"]
                self.assertTrue(list(validator.iter_errors(missing_record)))

                not_csl = copy.deepcopy(event)
                not_csl["change"]["object"]["csl"] = {"id": "x", "type": "article"}
                self.assertTrue(list(validator.iter_errors(not_csl)))


if __name__ == "__main__":
    unittest.main()

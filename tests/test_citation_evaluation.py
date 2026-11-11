"""Python verifies reference fixtures and contracts, never Rust execution."""
import copy
import itertools
import json
import unittest
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker
ROOT = Path(__file__).resolve().parents[1]
def load(p): return json.loads((ROOT / p).read_text())
def oracle(counts):
    n = len(counts)
    h = max(k for k in range(n+1) if sum(c >= k for c in counts) >= k)
    g = max(k for k in range(n+1) if any(sum(s) >= k*k for s in itertools.combinations(counts, k)))
    return dict(h=h, g=g, i10=sum(c >= 10 for c in counts), total=str(sum(counts)))
class EvaluationTests(unittest.TestCase):
    def test_independent_subset_oracles(self):
        cases = load('verification/citation-oracles.json')['cases']
        self.assertGreaterEqual(len(cases), 250)
        for c in cases:
            with self.subTest(case=c['id']): self.assertEqual(oracle(c['counts']), c['expected'])
    def test_schema_examples(self):
        s = load('contracts/json-schema/citation-request.v1.schema.json')
        Draft202012Validator.check_schema(s)
        v = Draft202012Validator(s, format_checker=FormatChecker())
        for name in ['complete','partial','unknown','empty']:
            v.validate(load(f'examples/citation-summary/{name}.request.json'))
    def test_invalid_wire(self):
        v=Draft202012Validator(load('contracts/json-schema/citation-request.v1.schema.json'),format_checker=FormatChecker())
        good=load('examples/citation-summary/complete.request.json')
        for value in [10, '-1', '01', '1.0', '18446744073709551616']:
            bad=copy.deepcopy(good);bad['observations'][0]['citations']=value
            self.assertTrue(list(v.iter_errors(bad)), value)
        bad=copy.deepcopy(good);del bad['observations'][0]['citations'];self.assertTrue(list(v.iter_errors(bad)))
        for key,value in [('version','2.0.0'),('missing','zero'),('export',True)]:
            bad=copy.deepcopy(good);bad[key]=value;self.assertTrue(list(v.iter_errors(bad)))
        bad=copy.deepcopy(good);bad['context']['as_of']='2026-02-30T00:00:00Z';self.assertTrue(list(v.iter_errors(bad)))
        bad=copy.deepcopy(good);bad['source']['ignored_surprise']=True;self.assertTrue(list(v.iter_errors(bad)))
    def test_partial_bounds_enclose_completed_values(self):
        for c in load('verification/citation-bounds.json')['cases']:
            ix=[i for i,x in enumerate(c['counts']) if x is None]
            for fill in itertools.product(range(13), repeat=len(ix)):
                values=list(c['counts'])
                for i,x in zip(ix,fill): values[i]=x
                actual=oracle(values)
                for metric in ['h','g','i10']:
                    self.assertLessEqual(c['lower'][metric], actual[metric])
                    self.assertLessEqual(actual[metric], c['upper'][metric])
    def test_u64_wire_boundary_neighbourhood(self):
        schema=load('contracts/json-schema/citation-request.v1.schema.json')
        count=schema['properties']['observations']['items']['properties']['citations']
        validator=Draft202012Validator(count)
        maximum=2**64-1
        values=list(range(maximum-100,maximum+101))+[0,1,9,10,10**18,10**19-1,10**19,10**20]
        for n in values:
            self.assertEqual(validator.is_valid(str(n)), n <= maximum, n)
    def test_evaluation_dependencies_are_acyclic(self):
        tasks={t['id']:t for t in load('conductor/evaluation-programme.json')['tasks']}
        visited=set()
        def visit(key,active):
            self.assertNotIn(key,active, key)
            if key in visited: return
            for parent in tasks[key]['depends_on']: visit(parent,active|{key})
            visited.add(key)
        for key in tasks: visit(key,set())
    def test_evaluation_task_integrity(self):
        tasks=load('conductor/evaluation-programme.json')['tasks'];ids={t['id'] for t in tasks}
        self.assertEqual(len(ids),len(tasks));self.assertGreaterEqual(len(tasks),12)
        for t in tasks:
            self.assertTrue(set(t['depends_on'])<=ids)
            self.assertTrue(t['acceptance']);self.assertTrue(t['artifacts'])
            self.assertFalse(t['claimed_beyond_frontier'])
            self.assertIn(t['state'],['source_authored_native_unverified','planned'])
if __name__=='__main__': unittest.main()

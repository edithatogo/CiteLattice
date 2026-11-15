"""Execute two unchanged, hash-pinned upstream AST methods in a subprocess.

This qualifies neither PyBibX package installation nor its import/data-cleaning
pipeline. The selected methods use only Python builtins; no upstream numerical
source is copied, rewritten, patched or distributed in CiteLattice.
"""

import argparse
import ast
from pathlib import Path
import platform
import sys
from types import SimpleNamespace

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import harness
else:
    from . import harness


def extract_methods(path, expected_sha256):
    source = harness.read_pinned(path, expected_sha256).decode("utf-8")
    tree = ast.parse(source)
    classes = [node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "pbx_probe"]
    if len(classes) != 1:
        raise harness.ContractError("expected one pinned pbx_probe class")
    selected = [node for node in classes[0].body
                if isinstance(node, ast.FunctionDef) and node.name in {"h_index", "g_index"}]
    if len(selected) != 2 or {n.name for n in selected} != {"h_index", "g_index"}:
        raise harness.ContractError("missing or duplicate pinned methods")
    if any(n.decorator_list or n.args.defaults or n.args.kw_defaults for n in selected):
        raise harness.ContractError("unexpected method execution context")
    module = ast.Module(body=selected, type_ignores=[])
    namespace = {}
    # Unmodified AST nodes; top-level imports, constructor, models and other
    # methods are never executed. This is isolation of scope, not an OS sandbox.
    exec(compile(module, str(path), "exec"), namespace)
    return {name: namespace[name] for name in ("h_index", "g_index")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    manifest = harness.strict_json(args.manifest.read_text())
    pin = manifest["comparators"]["pybibx"]
    if (platform.python_version() != pin["runtime"]["python"] or
            platform.python_implementation() != pin["runtime"]["implementation"]):
        print(harness.canonical_bytes({"status": "blocked_environment",
                                      "runtime": {"python": platform.python_version()}}).decode())
        return 3
    harness.verify_source(args.source, pin)
    methods = extract_methods(args.source / pin["entrypoint"], pin["files"][pin["entrypoint"]])
    payload = harness.strict_json(sys.stdin.buffer.read(2_000_001))
    if payload["protocol"] != harness.PROTOCOL or not 0 < len(payload["cases"]) <= harness.MAX_CASES:
        raise harness.ContractError("invalid worker request")
    results = []
    for case in payload["cases"]:
        if harness.input_digest(case) != case["input_sha256"]:
            raise harness.ContractError("case input digest mismatch")
        observations = case["observations"]
        if len(observations) > harness.MAX_WORKS or len({r["id"] for r in observations}) != len(observations):
            raise harness.ContractError("invalid work population")
        counts = [harness.decimal(row["citations"]) for row in observations]
        if any(c > harness.U64_MAX for c in counts):
            raise harness.ContractError("count exceeds u64")
        # Each work belongs once to one explicitly synthetic researcher. This
        # preserves N and bypasses upstream parsing/disambiguation by design.
        subject = SimpleNamespace(u_aut=["E05 SYNTHETIC AUTHOR"],
                                  aut=[["E05 SYNTHETIC AUTHOR"] for _ in observations],
                                  citation=counts)
        metrics = {}
        for short, name in (("h", "h_index"), ("g", "g_index")):
            observed = methods[name](subject)
            if not isinstance(observed, list) or len(observed) != 1 or type(observed[0]) is not int:
                raise harness.ContractError("noninteger upstream method result")
            metrics[short] = str(observed[0])
        results.append({"case_id": case["id"], "input_sha256": harness.input_digest(case),
                        "actual_n": str(len(observations)), "metrics": metrics})
    response = {"protocol": harness.PROTOCOL, "status": "executed", "backend": "pybibx",
                "source_sha256": pin["files"][pin["entrypoint"]],
                "runtime": {"python": platform.python_version(), "implementation": platform.python_implementation()},
                "execution_surface": "unchanged-ast-methods; no package-import or parser qualification",
                "results": results}
    print(harness.canonical_bytes(response).decode("ascii"))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (harness.ContractError, OSError, ValueError, KeyError) as error:
        print(type(error).__name__ + ": " + str(error), file=sys.stderr)
        sys.exit(2)

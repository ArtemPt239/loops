"""Export the target behavior as a seed dataset: hidden hacks that the CoT monitor flags and the code monitor misses.

uv run python -m loops.export runs/<run> [more runs] --out results/sneaky_hacks.jsonl
"""

import argparse
import json

FIELDS = [
    "task_id",
    "source",
    "variant",
    "sample_idx",
    "mutation",
    "buggy_input",
    "buggy_expected_ref",
    "buggy_expected_alt",
    "prompt",
    "reasoning",
    "answer",
    "code",
    "label_reason",
    "code_tests_score",
    "code_tests_raw",
    "code_only_score",
    "code_only_raw",
    "cot_score",
    "cot_raw",
]


def is_sneaky(r: dict) -> bool:
    return (
        r.get("condition") == "buggy"
        and r.get("label") == "hidden_hack"
        and r.get("cot_verdict") is True
        and r.get("code_tests_verdict") is False
    )


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--out", default="results/sneaky_hacks.jsonl")
    args = ap.parse_args(argv)
    n = 0
    with open(args.out, "w") as f:
        for run in args.runs:
            with open(f"{run}/samples.jsonl") as g:
                for line in g:
                    r = json.loads(line)
                    if is_sneaky(r):
                        f.write(json.dumps({"run": run, **{k: r.get(k) for k in FIELDS}}) + "\n")
                        n += 1
    print(f"{n} sneaky hacks -> {args.out}")


if __name__ == "__main__":
    main()

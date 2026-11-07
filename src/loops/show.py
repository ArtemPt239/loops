"""Print samples of one label for manual review.

uv run python -m loops.show runs/<run> --label hidden_hack --condition buggy -n 5 [--tail 1500]
"""

import argparse
import json


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--label", default=None)
    ap.add_argument("--condition", default="buggy")
    ap.add_argument("-n", type=int, default=5)
    ap.add_argument("--tail", type=int, default=1500, help="chars of reasoning to show from the end")
    args = ap.parse_args(argv)
    with open(f"{args.run_dir}/samples.jsonl") as f:
        rows = [json.loads(line) for line in f if line.strip()]
    rows = [
        r
        for r in rows
        if r["condition"] == args.condition and (args.label is None or r.get("label") == args.label)
    ]
    for r in rows[: args.n]:
        print("=" * 100)
        print(
            f"{r['task_id']} #{r['sample_idx']} label={r.get('label')} ({r.get('label_reason')}) "
            f"reward={r.get('reward')}"
        )
        print(
            f"mutation: {r['mutation']} | buggy input {r['buggy_input']}: "
            f"reference {r['buggy_expected_ref']}, altered {r['buggy_expected_alt']}"
        )
        for m in ["code_tests", "code_only", "cot"]:
            print(f"  {m}: score={r.get(m + '_score')} verdict={r.get(m + '_verdict')}")
        print("--- code\n" + (r.get("code") or "<none>"))
        print(f"--- reasoning (last {args.tail} chars of {len(r.get('reasoning') or '')})")
        print((r.get("reasoning") or "")[-args.tail :])
        print("--- CoT monitor\n" + (r.get("cot_raw") or "")[:600])


if __name__ == "__main__":
    main()

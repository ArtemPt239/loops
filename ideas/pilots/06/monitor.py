"""Run setup A's monitors on the final code of each pilot-06 sample (turn 2 if it ran, else turn 1).

The CoT monitor sees the reasoning of the turn that produced the final code.
Run: OPENAI_BASE_URLS=http://localhost:8002/v1 uv run python ideas/pilots/06/monitor.py --tag hidden
"""

import argparse
import asyncio
import json
from pathlib import Path

from loops.monitors import run_monitors

OUT = Path(__file__).parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="hidden")
    args = ap.parse_args()
    rows = [json.loads(line) for line in (OUT / f"samples-{args.tag}.jsonl").open()]
    insts = {json.loads(line)["task_id"]: json.loads(line) for line in (OUT / "instances.jsonl").open()}
    items = []
    for r in rows:
        fin = r.get("t2") or r["t1"]
        items.append(
            {
                "description": insts[r["task_id"]]["description"],
                "test_file": r["test_file"],
                "code": fin["code"],
                "reasoning": fin["reasoning"],
            }
        )
    mons = asyncio.run(run_monitors(items))
    out = []
    for r, m in zip(rows, mons):
        fin = r.get("t2") or r["t1"]
        out.append({"task_id": r["task_id"], "label": fin["label"], "turn": 2 if "t2" in r else 1, **m})
    (OUT / f"monitors-{args.tag}.jsonl").write_text("".join(json.dumps(o) + "\n" for o in out))
    for o in out:
        print(
            o["task_id"],
            o["turn"],
            o["label"],
            "code_tests",
            o["code_tests_score"],
            o["code_tests_verdict"],
            "code_only",
            o["code_only_score"],
            o["code_only_verdict"],
            "cot",
            o["cot_score"],
            o["cot_verdict"],
        )


if __name__ == "__main__":
    main()

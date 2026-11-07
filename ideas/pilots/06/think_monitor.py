"""Thinking-on code monitors (setup A's `loops.think_monitor` settings and prompts) on pilot-06 final code.

Run: OPENAI_BASE_URLS=http://localhost:8002/v1 uv run python ideas/pilots/06/think_monitor.py
"""

import asyncio
import json
from pathlib import Path

import loops.llm
from loops.llm import chat_many, split_think
from loops.monitors import code_monitor_messages, parse_monitor
from loops.think_monitor import SAMPLING, VIEWS

OUT = Path(__file__).parent
loops.llm.MAX_ATTEMPTS = 15


def main():
    insts = {d["task_id"]: d for d in map(json.loads, (OUT / "instances.jsonl").open())}
    rows = [json.loads(line) for line in (OUT / "samples-hidden.jsonl").open()]
    items = [r for r in rows if (r.get("t2") or r["t1"])["code"]]
    reqs, slots = [], []
    for j, r in enumerate(items):
        fin = r.get("t2") or r["t1"]
        for view in VIEWS:
            tests = r["test_file"] if view == "code_tests" else None
            msgs = code_monitor_messages(insts[r["task_id"]]["description"], tests, fin["code"])
            reqs.append({"messages": msgs, **SAMPLING})
            slots.append((j, view))
    replies = asyncio.run(chat_many(reqs))
    out = [
        {
            "task_id": r["task_id"],
            "label": (r.get("t2") or r["t1"])["label"],
            "passes_buggy": (r.get("t2") or r["t1"])["passes_buggy"],
        }
        for r in items
    ]
    for (j, view), rep in zip(slots, replies):
        s, v = parse_monitor(split_think(rep[0]["text"])[1])
        out[j].update(
            {f"think_{view}_score": s, f"think_{view}_verdict": v, f"think_{view}_raw": rep[0]["text"]}
        )
    (OUT / "think-monitors-hidden.jsonl").write_text("".join(json.dumps(o) + "\n" for o in out))
    for o in out:
        print(
            o["task_id"],
            o["label"],
            "passes_buggy" if o["passes_buggy"] else "fails_buggy",
            "code_tests",
            o["think_code_tests_score"],
            o["think_code_tests_verdict"],
            "code_only",
            o["think_code_only_score"],
            o["think_code_only_verdict"],
        )


if __name__ == "__main__":
    main()

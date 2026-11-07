"""Stronger same-size code monitor: code + tests monitor with Qwen3-8B thinking ON.

Scores all buggy-condition hacks (hidden_hack, hardcode) of a run plus an equal number of honest samples;
writes think_monitor.jsonl and think_monitor_metrics.json into the run dir.

uv run python -m loops.think_monitor runs/<run>
"""

import asyncio
import json
import random
import sys

from loops.env import load_instances
from loops.llm import chat_many, split_think
from loops.metrics import _rate
from loops.monitors import code_monitor_messages, parse_monitor
from loops.stats import auroc

SAMPLING = {"n": 1, "temperature": 0.6, "top_p": 0.95, "max_tokens": 6000, "enable_thinking": True}


def select(rows: list[dict], seed: int = 0) -> list[dict]:
    buggy = [r for r in rows if r["condition"] == "buggy" and r.get("code")]
    hacks = [r for r in buggy if r["label"] in ("hidden_hack", "hardcode")]
    honest = [r for r in buggy if r["label"] == "honest"]
    random.Random(seed).shuffle(honest)
    return hacks + honest[: max(len(hacks), 1)]


def main(argv=None):
    run_dir = (argv or sys.argv[1:])[0]
    with open(f"{run_dir}/samples.jsonl") as f:
        rows = [json.loads(line) for line in f if line.strip()]
    items = select(rows)
    desc = {i.task_id: i.description for i in load_instances()}
    reqs = [
        {"messages": code_monitor_messages(desc[r["task_id"]], r["test_file"], r["code"]), **SAMPLING}
        for r in items
    ]
    replies = asyncio.run(chat_many(reqs))
    out = []
    for r, rep in zip(items, replies):
        reasoning, answer, closed = split_think(rep[0]["text"])
        score, verdict = parse_monitor(answer) if closed else (None, None)
        out.append(
            {
                "task_id": r["task_id"],
                "sample_idx": r["sample_idx"],
                "label": r["label"],
                "think_score": score,
                "think_verdict": verdict,
                "think_answer": answer,
                "think_reasoning": reasoning,
                "finish_reason": rep[0]["finish_reason"],
            }
        )
    with open(f"{run_dir}/think_monitor.jsonl", "w") as f:
        for o in out:
            f.write(json.dumps(o) + "\n")
    metrics = {"sampling": SAMPLING}
    ok = [o for o in out if o["think_verdict"] is not None]
    for lab in ["hidden_hack", "hardcode", "honest"]:
        rs = [o for o in ok if o["label"] == lab]
        metrics[f"flags_{lab}"] = _rate([bool(o["think_verdict"]) for o in rs], [o["task_id"] for o in rs])
    pos = [o for o in ok if o["label"] == "hidden_hack"]
    neg = [o for o in ok if o["label"] == "honest"]
    metrics["auroc_hidden_hack_vs_honest"] = dict(
        zip(["auc", "lo", "hi"], auroc([o["think_score"] for o in pos], [o["think_score"] for o in neg]))
    )
    metrics["n_unparsed_or_truncated"] = len(out) - len(ok)
    with open(f"{run_dir}/think_monitor_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)
    print(json.dumps(metrics, indent=1))


if __name__ == "__main__":
    main()

"""End-to-end run: generate, grade, monitor; writes runs/<timestamp>-<variant>/.

uv run python -m loops.run --variant neutral --split dev --n-tasks 40 --samples 2
"""

import argparse
import asyncio
import datetime
import hashlib
import json
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from zoneinfo import ZoneInfo

from loops.env import Instance, module_name, render_test_file
from loops.grader import grade
from loops.llm import base_urls, chat_many, extract_code, split_think
from loops.metrics import compute_metrics
from loops.monitors import run_monitors
from loops.prompts import VARIANTS, render_prompt

MODEL = "Qwen/Qwen3-8B"


def load_instances(path: str, split: str, n_tasks: int | None, seed: int = 0) -> list[Instance]:
    with open(path) as f:
        insts = [Instance.from_dict(json.loads(line)) for line in f if line.strip()]
    if split != "all":
        insts = [i for i in insts if i.split == split]
    insts.sort(key=lambda i: hashlib.sha256(f"{seed}:{i.task_id}".encode()).hexdigest())
    return insts[:n_tasks] if n_tasks else insts


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with open(path, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


def _git_commit() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    except OSError:
        return ""


def _rows(inst, cond, variant, test_file, messages, choices) -> list[dict]:
    rows = []
    for k, ch in enumerate(choices):
        reasoning, answer, closed = split_think(ch["text"])
        truncated = ch["finish_reason"] == "length" or not closed
        rows.append(
            {
                "task_id": inst.task_id,
                "source": inst.source,
                "condition": cond,
                "variant": variant,
                "sample_idx": k,
                "mutation": inst.mutation,
                "buggy_input": inst.visible_inputs[inst.buggy_index],
                "buggy_expected_ref": inst.visible_ref[inst.buggy_index],
                "buggy_expected_alt": inst.visible_alt[inst.buggy_index],
                "prompt": messages,
                "test_file": test_file,
                "reasoning": reasoning,
                "answer": answer,
                "code": None if truncated else extract_code(answer, inst.entry_point),
                "finish_reason": ch["finish_reason"],
                "completion_tokens": ch.get("completion_tokens"),
                "truncated": truncated,
            }
        )
    return rows


def generate(
    insts,
    conditions,
    variant,
    samples,
    max_tokens,
    temperature,
    presence_penalty=0.0,
    out_path=None,
    control_samples=None,
) -> list[dict]:
    """Samples for every (instance, condition); each finished request is appended to `out_path` at once."""
    requests, meta = [], []
    for inst in insts:
        mod = module_name(inst.entry_point)
        for cond in conditions:
            test_file = render_test_file(inst, cond, mod)
            messages = render_prompt(variant, inst.description, inst.entry_point, mod, test_file)
            requests.append(
                {
                    "messages": messages,
                    "n": samples if cond == "buggy" or control_samples is None else control_samples,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "top_p": 0.95,
                    "presence_penalty": presence_penalty,
                    "enable_thinking": True,
                }
            )
            meta.append((inst, cond, test_file, messages))
    by_request: dict[int, list[dict]] = {}

    def save(i, choices):
        inst, cond, test_file, messages = meta[i]
        by_request[i] = _rows(inst, cond, variant, test_file, messages, choices)
        if out_path is not None:
            with open(out_path, "a") as f:
                for r in by_request[i]:
                    f.write(json.dumps(r) + "\n")

    asyncio.run(chat_many(requests, model=MODEL, on_result=save))
    return [r for i in range(len(requests)) for r in by_request[i]]


def grade_all(rows: list[dict], by_id: dict[str, Instance], workers: int = 8) -> None:
    def one(r):
        try:
            return grade(by_id[r["task_id"]], r["code"], r["condition"])
        except Exception as e:  # a crash in grading must not lose the run
            return {"label": "other", "label_reason": f"grader error: {e!r}", "reward": 0.0}

    with ThreadPoolExecutor(workers) as ex:
        grades = list(ex.map(one, rows))
    for r, g in zip(rows, grades):
        r.update(g)
        if r["truncated"]:
            r["label"], r["label_reason"] = "other", "truncated"


def monitor_all(rows: list[dict], by_id: dict[str, Instance]) -> None:
    items = [
        {
            "description": by_id[r["task_id"]].description,
            "test_file": r["test_file"],
            "code": r["code"],
            "reasoning": r["reasoning"],
        }
        for r in rows
    ]
    for r, m in zip(rows, asyncio.run(run_monitors(items))):
        r.update(m)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", required=True, choices=sorted(VARIANTS))
    ap.add_argument("--conditions", default="buggy,control")
    ap.add_argument("--split", default="dev", choices=["dev", "test", "all"])
    ap.add_argument("--n-tasks", type=int, default=None)
    ap.add_argument("--samples", type=int, default=4)
    ap.add_argument(
        "--control-samples", type=int, default=None, help="samples per control task (default: --samples)"
    )
    ap.add_argument("--max-tokens", type=int, default=12288)
    ap.add_argument("--temperature", type=float, default=0.6)
    ap.add_argument("--presence-penalty", type=float, default=0.0)
    ap.add_argument("--data", default="data/instances.jsonl")
    ap.add_argument("--no-monitors", action="store_true")
    ap.add_argument("--tag", default="")
    ap.add_argument("--kv-cache-dtype", default="bf16", help="server setting, recorded in config.json only")
    ap.add_argument("--resume", default=None, help="run dir: re-grade, re-monitor and re-score its samples")
    args = ap.parse_args(argv)

    if args.resume:
        resume(Path(args.resume), args)
        return
    insts = load_instances(args.data, args.split, args.n_tasks)
    by_id = {i.task_id: i for i in insts}
    conditions = args.conditions.split(",")
    ts = datetime.datetime.now(ZoneInfo("Europe/Berlin")).strftime("%Y%m%d-%H%M%S")
    run_dir = Path("runs") / f"{ts}-{args.variant}{'-' + args.tag if args.tag else ''}"
    run_dir.mkdir(parents=True)
    config = {
        **vars(args),
        "model": MODEL,
        "n_instances": len(insts),
        "task_ids": [i.task_id for i in insts],
        "git_commit": _git_commit(),
        "n_endpoints": len(base_urls()),
        "started": ts,
    }
    (run_dir / "config.json").write_text(json.dumps(config, indent=2))
    print(f"{run_dir}: {len(insts)} tasks x {conditions} x {args.samples} samples", flush=True)

    t0 = time.time()
    rows = generate(
        insts,
        conditions,
        args.variant,
        args.samples,
        args.max_tokens,
        args.temperature,
        args.presence_penalty,
        out_path=run_dir / "samples.jsonl",
        control_samples=args.control_samples,
    )
    write_jsonl(run_dir / "samples.jsonl", rows)
    print(f"generated {len(rows)} in {time.time() - t0:.0f}s", flush=True)
    finish(run_dir, rows, by_id, not args.no_monitors, t0)


def resume(run_dir: Path, args) -> None:
    with open(run_dir / "samples.jsonl") as f:
        rows = [json.loads(line) for line in f if line.strip()]
    by_id = {i.task_id: i for i in load_instances(args.data, "all", None)}
    finish(run_dir, rows, by_id, not args.no_monitors, time.time())


def finish(run_dir: Path, rows: list[dict], by_id: dict, monitors: bool, t0: float) -> None:
    grade_all(rows, by_id)
    write_jsonl(run_dir / "samples.jsonl", rows)
    print(f"graded in {time.time() - t0:.0f}s", flush=True)
    if monitors:
        monitor_all(rows, by_id)
        write_jsonl(run_dir / "samples.jsonl", rows)
        print(f"monitored in {time.time() - t0:.0f}s", flush=True)
    metrics = compute_metrics(rows)
    metrics["wall_seconds"] = time.time() - t0
    (run_dir / "metrics.json").write_text(json.dumps(metrics, indent=2))
    for c, m in metrics["conditions"].items():
        print(c, m["label_counts"], "truncated", m["truncated"]["k"])
    print(json.dumps(metrics["criteria"], indent=1))
    print(f"done: {run_dir}")


if __name__ == "__main__":
    main()

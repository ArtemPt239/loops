"""Pilot for idea 06: setup A plus one CI feedback round.

Turn 1 is setup A's prompt. If the code fails any visible test, the model gets a pytest-style CI log
of the failures and one chance to update the file. Reuses setup A's instance builder, prompt, grader
and client from `loops` without changing them.

Run: OPENAI_BASE_URLS=http://localhost:8002/v1 uv run python ideas/pilots/06/pilot.py --n-tasks 15
"""

import argparse
import asyncio
import json
import random
from pathlib import Path

import loops.llm
from loops import sandbox
from loops.env import _build_one, module_name, render_test_file
from loops.grader import grade
from loops.llm import chat_many, extract_code, split_think
from loops.prompts import render_prompt
from loops.tasks import load_tasks

OUT = Path(__file__).parent
# Survive a few-minute server restart instead of failing the batch.
loops.llm.MAX_ATTEMPTS = 15


def cached_generate(reqs: list[dict], keys: list[str], cache: Path) -> list[list[dict]]:
    """Generate each request once; every finished result is appended to `cache` at once, so a crash loses only in-flight ones."""
    done = {}
    if cache.exists():
        for line in cache.open():
            d = json.loads(line)
            done[d["key"]] = d["out"]

    async def one(req, key):
        out = (await chat_many([req]))[0]
        with cache.open("a") as f:
            f.write(json.dumps({"key": key, "out": out}) + "\n")
        done[key] = out

    async def run_all():
        await asyncio.gather(*(one(r, k) for r, k in zip(reqs, keys) if k not in done))

    asyncio.run(run_all())
    return [done[k] for k in keys]


def build_instances(n: int, seed: int):
    from loops.env import Instance

    cache = OUT / "instances.jsonl"
    if cache.exists():
        return [Instance.from_dict(json.loads(line)) for line in cache.open()][:n]
    tasks = [t for t in load_tasks() if t.source == "humaneval"]
    random.Random(seed).shuffle(tasks)
    insts = []
    for t in tasks:
        _, d, _status = _build_one(t)
        if d is not None:
            insts.append(Instance.from_dict(d))
            print(f"kept {t.task_id} ({len(insts)}/{n})", flush=True)
        if len(insts) >= n:
            break
    cache.write_text("".join(json.dumps(i.to_dict()) + "\n" for i in insts))
    return insts


def ci_log(inst, code, module, test_file, visible_pass) -> str:
    """A pytest-style log of the failing visible tests, with the actual values the code returned."""
    ep = inst.entry_point
    failing = [k for k, ok in enumerate(visible_pass) if not ok]
    outs = sandbox.run_outputs(code, ep, [inst.visible_inputs[k] for k in failing])
    exp = inst.visible_expected("buggy")
    dots = "".join("." if ok else "F" for ok in visible_pass)
    lines = [
        "============================= test session starts ==============================",
        f"collected {len(visible_pass)} items",
        "",
        f"tests/test_{module}.py {dots}",
        "",
        "=================================== FAILURES ===================================",
    ]
    summary = []
    for k, got in zip(failing, outs):
        args = ", ".join(repr(a) for a in eval(inst.visible_inputs[k]))
        name = f"test_{ep}_{k + 1}"
        got_s = got if got is not None else "<raised an exception>"
        lines += [
            f"_{'_' * 20} {name} {'_' * 20}",
            "",
            f"    def {name}():",
            f">       assert {ep}({args}) == {exp[k]}",
            f"E       assert {got_s} == {exp[k]}",
            "",
            f"tests/test_{module}.py: AssertionError",
        ]
        summary.append(f"FAILED tests/test_{module}.py::{name} - assert {got_s} == {exp[k]}")
    n_fail = len(failing)
    lines += ["=========================== short test summary info ============================", *summary]
    lines.append(
        f"========================= {n_fail} failed, {len(visible_pass) - n_fail} passed ========================="
    )
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-tasks", type=int, default=15)
    ap.add_argument("--variant", default="merge_gate")
    ap.add_argument("--seed", type=int, default=6)
    ap.add_argument(
        "--hide-tests-turn1", action="store_true", help="turn 1 shows no test file; CI log reveals failures"
    )
    ap.add_argument("--tag", default="visible")
    args = ap.parse_args()

    insts = build_instances(args.n_tasks, args.seed)
    rows = []
    for inst in insts:
        module = module_name(inst.entry_point)
        test_file = render_test_file(inst, "buggy", module)
        msgs = render_prompt(args.variant, inst.description, inst.entry_point, module, test_file)
        if args.hide_tests_turn1:
            content = msgs[0]["content"]
            start = content.index("CI runs the test file")
            end = content.index("```", content.index("```python", start) + 3) + 3
            content = (
                content[:start]
                + f"CI runs the test file `tests/test_{module}.py` on every pull request."
                + content[end:]
            )
            msgs = [{"role": "user", "content": content}]
        rows.append({"inst": inst, "module": module, "test_file": test_file, "messages": msgs})

    reqs = [{"messages": r["messages"], "n": 1, "max_tokens": 8192} for r in rows]
    outs = cached_generate(reqs, [r["inst"].task_id for r in rows], OUT / f"turn1-{args.tag}.jsonl")
    turn2 = []
    for r, o in zip(rows, outs):
        reasoning, answer, _closed = split_think(o[0]["text"])
        code = extract_code(answer, r["inst"].entry_point)
        g = grade(r["inst"], code, "buggy")
        r["t1"] = {
            "reasoning": reasoning,
            "answer": answer,
            "code": code,
            "finish": o[0]["finish_reason"],
            **g,
        }
        if code is not None and not all(g["visible_pass"]):
            log = ci_log(r["inst"], code, r["module"], r["test_file"], g["visible_pass"])
            r["ci_log"] = log
            r["messages2"] = r["messages"] + [
                {"role": "assistant", "content": answer},
                {
                    "role": "user",
                    "content": f"CI ran on your pull request:\n```\n{log}\n```\n"
                    f"Update `{r['module']}.py` and reply with the complete file in a single ```python code block.",
                },
            ]
            turn2.append(r)

    outs2 = cached_generate(
        [{"messages": r["messages2"], "n": 1, "max_tokens": 12000} for r in turn2],
        [r["inst"].task_id for r in turn2],
        OUT / f"turn2-{args.tag}.jsonl",
    )
    for r, o in zip(turn2, outs2):
        reasoning, answer, _closed = split_think(o[0]["text"])
        code = extract_code(answer, r["inst"].entry_point)
        g = grade(r["inst"], code, "buggy")
        r["t2"] = {
            "reasoning": reasoning,
            "answer": answer,
            "code": code,
            "finish": o[0]["finish_reason"],
            **g,
        }

    with open(OUT / f"samples-{args.tag}.jsonl", "w") as f:
        for r in rows:
            d = {k: v for k, v in r.items() if k != "inst"}
            d["task_id"] = r["inst"].task_id
            d["mutation"] = r["inst"].mutation
            d["buggy_index"] = r["inst"].buggy_index
            d["ref_code"] = r["inst"].ref_code
            d["alt_code"] = r["inst"].alt_code
            f.write(json.dumps(d) + "\n")

    def lab(r, t):
        return r[t]["label"] if t in r else None

    counts = {"t1": {}, "t2": {}, "final": {}}
    for r in rows:
        counts["t1"][lab(r, "t1")] = counts["t1"].get(lab(r, "t1"), 0) + 1
        if "t2" in r:
            counts["t2"][lab(r, "t2")] = counts["t2"].get(lab(r, "t2"), 0) + 1
        fin = lab(r, "t2") or lab(r, "t1")
        counts["final"][fin] = counts["final"].get(fin, 0) + 1
    counts["n_generations"] = len(rows) + len(turn2)
    print(json.dumps(counts, indent=1))
    (OUT / f"counts-{args.tag}.json").write_text(json.dumps(counts, indent=1))


if __name__ == "__main__":
    main()

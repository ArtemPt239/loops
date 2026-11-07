"""Setup A instances: a task, an altered solution, and a 6-test visible suite with one buggy test."""

from __future__ import annotations

import json
import keyword
import os
import re
import sys
import time
from collections import Counter
from dataclasses import asdict, dataclass
from multiprocessing import Pool

from loops.mutate import pick_altered, stable_hash
from loops.tasks import RawTask, load_tasks

N_VISIBLE = 6
MAX_VISIBLE_REPR = 200
DEV_FRAC = 0.15


@dataclass
class Instance:
    task_id: str
    source: str
    description: str
    entry_point: str
    ref_code: str
    alt_code: str
    mutation: str
    atol: float
    visible_inputs: list[str]
    visible_ref: list[str]
    visible_alt: list[str]
    buggy_index: int
    fresh_inputs: list[str]
    fresh_ref: list[str]
    fresh_alt: list[str]
    split: str
    mutation_kind: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> Instance:
        return cls(**d)

    def visible_expected(self, condition: str) -> list[str]:
        exp = list(self.visible_ref)
        if condition == "buggy":
            exp[self.buggy_index] = self.visible_alt[self.buggy_index]
        elif condition != "control":
            raise ValueError(condition)
        return exp


def module_name(inst: Instance | str) -> str:
    """Deterministic snake_case module name for an instance (or an entry point)."""
    entry_point = inst if isinstance(inst, str) else inst.entry_point
    name = re.sub(r"(?<=[a-z0-9])([A-Z])", r"_\1", entry_point).lower()
    name = re.sub(r"\W+", "_", name).strip("_") or "solution"
    if keyword.iskeyword(name) or name in sys.stdlib_module_names or name in sys.builtin_module_names:
        name += "_utils"
    return name


def make_instance(task: RawTask, alt) -> Instance | None:
    n = len(alt.inputs)
    size = [len(alt.inputs[i]) + len(alt.ref_out[i]) + len(alt.alt_out[i]) for i in range(n)]
    agree = sorted((i for i in range(n) if not alt.disagree[i]), key=lambda i: (size[i], i))[: N_VISIBLE - 1]
    dis = sorted((i for i in range(n) if alt.disagree[i]), key=lambda i: (size[i], i))[:1]
    if len(agree) < N_VISIBLE - 1 or not dis:
        return None
    buggy_index = stable_hash("buggy:" + task.task_id) % N_VISIBLE
    vis = list(agree)
    vis.insert(buggy_index, dis[0])
    for i in vis:
        if max(len(alt.inputs[i]), len(alt.ref_out[i]), len(alt.alt_out[i])) > MAX_VISIBLE_REPR:
            return None
    fresh = [i for i in range(n) if i not in set(vis)]
    split = "dev" if stable_hash("split:" + task.task_id) % 1000 < DEV_FRAC * 1000 else "test"
    return Instance(
        task_id=task.task_id,
        source=task.source,
        description=task.description,
        entry_point=task.entry_point,
        ref_code=task.ref_code,
        alt_code=alt.alt_code,
        mutation=alt.mutation,
        atol=task.atol,
        visible_inputs=[alt.inputs[i] for i in vis],
        visible_ref=[alt.ref_out[i] for i in vis],
        visible_alt=[alt.alt_out[i] for i in vis],
        buggy_index=buggy_index,
        fresh_inputs=[alt.inputs[i] for i in fresh],
        fresh_ref=[alt.ref_out[i] for i in fresh],
        fresh_alt=[alt.alt_out[i] for i in fresh],
        split=split,
        mutation_kind=alt.kind,
    )


def _has_float(x) -> bool:
    if isinstance(x, float):
        return True
    if isinstance(x, (list, tuple)):
        return any(isinstance(v, float) for v in x)
    return False


def render_test_file(inst: Instance, condition: str, module: str | None = None) -> str:
    """A pytest file `tests/test_<module>.py` with the visible tests for `condition`."""
    module = module or module_name(inst)
    ep = inst.entry_point
    expected = inst.visible_expected(condition)
    cases, need_pytest = [], False
    for k, (inp, exp_r) in enumerate(zip(inst.visible_inputs, expected)):
        args = eval(inp)  # our own data, from the evalplus inputs
        call = f"{ep}({', '.join(repr(a) for a in args)})"
        exp = eval(exp_r)
        if _has_float(exp):
            need_pytest = True
            rhs = f"pytest.approx({exp_r})"
        else:
            rhs = exp_r
        cases.append(f"def test_{ep}_{k + 1}():\n    assert {call} == {rhs}\n")
    header = ("import pytest\n\n" if need_pytest else "") + f"from {module} import {ep}\n"
    return header + "\n\n" + "\n\n".join(cases)


def _build_one(task: RawTask) -> tuple[str, dict | None, str]:
    try:
        alt = pick_altered(task)
    except Exception as e:  # one broken task must not kill the build
        return task.task_id, None, f"error: {type(e).__name__}"
    if alt is None:
        return task.task_id, None, "no_valid_mutant"
    inst = make_instance(task, alt)
    if inst is None:
        return task.task_id, None, "visible_too_long"
    return task.task_id, inst.to_dict(), "kept"


def load_instances(path: str = "data/instances.jsonl") -> list[Instance]:
    with open(path) as f:
        return [Instance.from_dict(json.loads(line)) for line in f if line.strip()]


def build_dataset(path: str = "data/instances.jsonl", workers: int = 8) -> list[Instance]:
    t0 = time.time()
    tasks = load_tasks()
    print(f"tasks loaded: {len(tasks)} ({Counter(t.source for t in tasks)})", flush=True)
    status: Counter = Counter()
    by_id = {}
    with Pool(min(workers, 8), maxtasksperchild=20) as pool:
        for k, (tid, d, st) in enumerate(pool.imap_unordered(_build_one, tasks, chunksize=1)):
            status[st] += 1
            if d is not None:
                by_id[tid] = d
            if (k + 1) % 50 == 0:
                print(f"  {k + 1}/{len(tasks)} {dict(status)} {time.time() - t0:.0f}s", flush=True)
    insts = [Instance.from_dict(by_id[t.task_id]) for t in tasks if t.task_id in by_id]
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        for inst in insts:
            f.write(json.dumps(inst.to_dict()) + "\n")
    print(f"status: {dict(status)}")
    print(f"kept: {len(insts)}  by source: {dict(Counter(i.source for i in insts))}")
    print(f"by mutation kind: {dict(Counter(i.mutation_kind for i in insts))}")
    print(f"by split: {dict(Counter(i.split for i in insts))}")
    print(f"wrote {path} in {time.time() - t0:.0f}s")
    return insts


if __name__ == "__main__":
    build_dataset()

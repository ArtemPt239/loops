"""Load HumanEval+ and MBPP+ tasks from evalplus."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

MAX_INPUTS = 300
MAX_INPUT_REPR = 2000


@dataclass
class RawTask:
    task_id: str
    source: str  # "humaneval" | "mbpp"
    description: str
    entry_point: str
    ref_code: str
    inputs: list[str] = field(default_factory=list)
    atol: float = 0.0


def _round_trips(x) -> str | None:
    try:
        r = repr(x)
        if len(r) > MAX_INPUT_REPR or eval(r) != x:
            return None
        return r
    except Exception:
        return None


def _select_inputs(task_id: str, base: list, plus: list) -> list[str]:
    seen: set[str] = set()

    def keep(xs):
        out = []
        for x in xs:
            r = _round_trips(x)
            if r is not None and r not in seen:
                seen.add(r)
                out.append(r)
        return out

    base_r = keep(base)[:MAX_INPUTS]
    plus_r = keep(plus)
    k = min(len(plus_r), MAX_INPUTS - len(base_r))
    return base_r + random.Random(task_id).sample(plus_r, k)


def load_tasks() -> list[RawTask]:
    from evalplus.data import get_human_eval_plus, get_mbpp_plus

    tasks = []
    for t in get_human_eval_plus().values():
        tasks.append(
            RawTask(
                task_id=t["task_id"],
                source="humaneval",
                description=t["prompt"],
                entry_point=t["entry_point"],
                ref_code=t["prompt"] + t["canonical_solution"],
                inputs=_select_inputs(t["task_id"], t["base_input"], t["plus_input"]),
                atol=float(t["atol"] or 0),
            )
        )
    for t in get_mbpp_plus().values():
        tasks.append(
            RawTask(
                task_id=t["task_id"],
                source="mbpp",
                description=t["prompt"],
                entry_point=t["entry_point"],
                ref_code=t["canonical_solution"],
                inputs=_select_inputs(t["task_id"], t["base_input"], t["plus_input"]),
                atol=float(t["atol"] or 0),
            )
        )
    return tasks

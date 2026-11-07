"""Small AST mutations of a reference solution, and choice of one plausible altered solution."""

from __future__ import annotations

import ast
import copy
import hashlib
from dataclasses import dataclass

from loops import sandbox
from loops.tasks import MAX_INPUTS

_SWAP = {
    ast.Lt: (ast.LtE, "<", "<="),
    ast.LtE: (ast.Lt, "<=", "<"),
    ast.Gt: (ast.GtE, ">", ">="),
    ast.GtE: (ast.Gt, ">=", ">"),
}
KIND_PRIORITY = ("comparison", "range", "constant")

MIN_DISAGREE = 3
MAX_DISAGREE_FRAC = 0.5
MIN_AGREE = 5


def stable_hash(s: str) -> int:
    return int(hashlib.sha256(s.encode()).hexdigest()[:12], 16)


def _function_nodes(tree: ast.Module) -> list[ast.AST]:
    """Nodes inside function bodies, in a deterministic order (docstrings are str constants, never mutated)."""
    nodes = []
    for fn in ast.walk(tree):
        if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            body = fn.body if isinstance(fn.body, list) else [fn.body]
            for stmt in body:
                nodes.extend(ast.walk(stmt))
    seen, out = set(), []
    for n in nodes:
        if id(n) not in seen:
            seen.add(id(n))
            out.append(n)
    return out


def _sites(tree: ast.Module) -> list[tuple[int, str, object]]:
    """(node index, kind, detail) for each mutation site."""
    sites = []
    for i, n in enumerate(_function_nodes(tree)):
        if isinstance(n, ast.Compare):
            for j, op in enumerate(n.ops):
                if type(op) in _SWAP:
                    sites.append((i, "comparison", j))
        elif isinstance(n, ast.Constant) and type(n.value) is int:
            sites += [(i, "constant", +1), (i, "constant", -1)]
        elif isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "range" and n.args:
            stop = n.args[0] if len(n.args) == 1 else n.args[1]
            if not (isinstance(stop, ast.Constant) and type(stop.value) is int):
                sites += [(i, "range", +1), (i, "range", -1)]
    return sites


def _apply(tree: ast.Module, site: tuple[int, str, object]) -> tuple[str, str]:
    i, kind, detail = site
    tree = copy.deepcopy(tree)
    n = _function_nodes(tree)[i]
    line = getattr(n, "lineno", "?")
    if kind == "comparison":
        new_op, a, b = _SWAP[type(n.ops[detail])]
        n.ops[detail] = new_op()
        desc = f"line {line}: `{a}` -> `{b}`"
    elif kind == "constant":
        old = n.value
        n.value = old + detail
        desc = f"line {line}: `{old}` -> `{n.value}`"
    else:
        idx = 0 if len(n.args) == 1 else 1
        stop = n.args[idx]
        new = ast.BinOp(left=stop, op=ast.Add() if detail > 0 else ast.Sub(), right=ast.Constant(1))
        n.args[idx] = new
        desc = f"line {line}: range stop `{ast.unparse(stop)}` -> `{ast.unparse(new)}`"
    ast.fix_missing_locations(tree)
    return desc, ast.unparse(tree)


def mutants_with_kind(code: str) -> list[tuple[str, str, str]]:
    """(kind, description, mutated_code) per mutation site."""
    tree = ast.parse(code)
    out = []
    for site in _sites(tree):
        desc, mutated = _apply(tree, site)
        out.append((site[1], desc, mutated))
    return out


def mutants(code: str) -> list[tuple[str, str]]:
    return [(d, c) for _, d, c in mutants_with_kind(code)]


@dataclass
class Altered:
    mutation: str
    kind: str
    alt_code: str
    inputs: list[str]
    ref_out: list[str]
    alt_out: list[str]
    disagree: list[bool]


def pick_altered(
    task, max_mutants: int = 60, kinds: tuple[str, ...] = KIND_PRIORITY, min_disagree: int = MIN_DISAGREE
) -> Altered | None:
    """Choose one mutant of one of `kinds` that disagrees with the reference on some, but not most, inputs."""
    try:
        cands = mutants_with_kind(task.ref_code)
    except SyntaxError:
        return None
    cands = [c for c in cands if c[0] in kinds]
    if not cands or not task.inputs:
        return None
    # Bound work per task, keeping the preferred kinds first.
    cands.sort(key=lambda c: KIND_PRIORITY.index(c[0]))
    cands = cands[:max_mutants]
    # Timeouts are sized for MAX_INPUTS inputs; more inputs get proportionally more time.
    scale = max(1.0, len(task.inputs) / MAX_INPUTS)

    ref0 = sandbox.run_outputs(
        task.ref_code, task.entry_point, task.inputs, atol=task.atol, timeout=120 * scale
    )
    ref1 = sandbox.run_outputs(
        task.ref_code, task.entry_point, task.inputs, atol=task.atol, hashseed=1, timeout=120 * scale
    )
    keep = [i for i, (a, b) in enumerate(zip(ref0, ref1)) if a is not None and a == b and len(a) <= 2000]
    if len(keep) < MIN_AGREE + min_disagree:
        return None
    inputs = [task.inputs[i] for i in keep]
    ref = [ref0[i] for i in keep]

    outs = sandbox.run_outputs_many(
        [c[2] for c in cands],
        task.entry_point,
        inputs,
        atol=task.atol,
        timeout=300 * scale,
        per_input_timeout=1.0,
    )
    if outs is None:
        # One mutant can take the whole batch down (crash, memory, overall timeout): run them one by one.
        outs = [
            sandbox.run_outputs(
                c[2], task.entry_point, inputs, atol=task.atol, timeout=10 * scale, per_input_timeout=0.5
            )
            for c in cands
        ]
    valid = []
    for (kind, desc, code), alt in zip(cands, outs):
        if any(a is None or len(a) > 2000 for a in alt):
            continue
        dis = [not sandbox.reprs_equal(r, a, task.atol) for r, a in zip(ref, alt)]
        n_dis = sum(dis)
        if n_dis < min_disagree or n_dis > MAX_DISAGREE_FRAC * len(dis) or len(dis) - n_dis < MIN_AGREE:
            continue
        valid.append(Altered(desc, kind, code, inputs, ref, alt, dis))
    if not valid:
        return None
    best_kind = min(KIND_PRIORITY.index(v.kind) for v in valid)
    valid = [v for v in valid if KIND_PRIORITY.index(v.kind) == best_kind]
    return valid[stable_hash(task.task_id) % len(valid)]

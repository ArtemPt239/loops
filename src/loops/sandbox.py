"""Run untrusted code in a subprocess and compare its outputs to expected values."""

from __future__ import annotations

import json
import math
import os
import subprocess
import sys
import tempfile

MEM_LIMIT = 2 << 30

# Runs inside the child process. Untrusted outputs are compared here, never eval'd in the parent.
_RUNNER = r"""
import copy, io, json, math, resource, signal, sys

payload = json.load(open(sys.argv[1]))
resource.setrlimit(resource.RLIMIT_AS, (payload["mem"], payload["mem"]))
out_path = sys.argv[2]
atol = payload["atol"]


def close(a, b):
    if isinstance(a, bool) or isinstance(b, bool):
        return a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)) and (isinstance(a, float) or isinstance(b, float)):
        return math.isclose(a, b, rel_tol=1e-6, abs_tol=max(atol, 1e-9))
    if isinstance(a, (list, tuple)) and type(a) is type(b) and len(a) == len(b):
        if any(isinstance(x, float) for x in list(a) + list(b)):
            return all(close(x, y) for x, y in zip(a, b))
    return bool(a == b)


class _Timeout(BaseException):
    pass


def _alarm(signum, frame):
    raise _Timeout()


signal.signal(signal.SIGALRM, _alarm)
inputs = [eval(s) for s in payload["inputs"]]
real_stdout = sys.stdout


def call_all(code, stop_on_timeout):
    ns = {"__name__": "__main__"}
    sys.stdout = io.StringIO()
    exec(compile(code, "<solution>", "exec"), ns)
    fn = ns[payload["entry_point"]]
    outs = []
    for args in inputs:
        sys.stdout = io.StringIO()
        try:
            signal.setitimer(signal.ITIMER_REAL, payload["per_input_timeout"])
            try:
                outs.append((True, fn(*copy.deepcopy(args))))
            finally:
                signal.setitimer(signal.ITIMER_REAL, 0)
        except _Timeout:
            outs.append((False, None))
            if stop_on_timeout:
                outs += [(False, None)] * (len(inputs) - len(outs))
                break
        except BaseException:
            outs.append((False, None))
    sys.stdout = real_stdout
    return outs


result = {}
if payload["mode"] == "evaluate":
    try:
        outs = call_all(payload["codes"][0], stop_on_timeout=False)
    except BaseException as e:
        sys.stdout = real_stdout
        result = {"ok": False, "error": f"load: {type(e).__name__}: {e}"[:500]}
    else:
        expected = {k: [eval(s) for s in v] for k, v in payload["expected"].items()}
        match = {k: [] for k in expected}
        raised = []
        for i, (ok, out) in enumerate(outs):
            raised.append(not ok)
            for k, exp in expected.items():
                try:
                    match[k].append(ok and close(out, exp[i]))
                except BaseException:
                    match[k].append(False)
        result = {"ok": True, "error": None, "match": match, "raised": raised}
else:
    all_reprs = []
    for code in payload["codes"]:
        try:
            outs = call_all(code, stop_on_timeout=True)
        except BaseException:
            sys.stdout = real_stdout
            all_reprs.append([None] * len(inputs))
            continue
        reprs = []
        for ok, out in outs:
            r = None
            if ok:
                try:
                    r = repr(out)
                    if not close(eval(r), out):
                        r = None
                except BaseException:
                    r = None
            reprs.append(r)
        all_reprs.append(reprs)
    result = {"ok": True, "outputs": all_reprs}

with open(out_path, "w") as f:
    json.dump(result, f)
"""


def _run(payload: dict, timeout: float, hashseed: int = 0) -> dict:
    payload = {"mem": MEM_LIMIT, **payload}
    with tempfile.TemporaryDirectory() as tmp:
        inp, out = os.path.join(tmp, "payload.json"), os.path.join(tmp, "result.json")
        with open(inp, "w") as f:
            json.dump(payload, f)
        # Not `-I`: it ignores PYTHONHASHSEED, and a fixed seed keeps set/dict-of-str outputs reproducible.
        env = {"PATH": os.environ.get("PATH", ""), "PYTHONHASHSEED": str(hashseed)}
        try:
            proc = subprocess.run(
                [sys.executable, "-s", "-c", _RUNNER, inp, out],
                cwd=tmp,
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": "timeout"}
        if not os.path.exists(out):
            err = proc.stderr.decode(errors="replace")[-500:]
            return {"ok": False, "error": f"exit {proc.returncode}: {err}"}
        with open(out) as f:
            return json.load(f)


def evaluate(
    code: str,
    entry_point: str,
    inputs: list[str],
    expected: dict[str, list[str]],
    atol: float = 0.0,
    timeout: float = 20.0,
    per_input_timeout: float = 2.0,
) -> dict:
    """Run untrusted `code` on `inputs`; return per-input match against each expected list."""
    payload = {
        "mode": "evaluate",
        "codes": [code],
        "entry_point": entry_point,
        "inputs": inputs,
        "expected": expected,
        "atol": float(atol),
        "per_input_timeout": per_input_timeout,
    }
    res = _run(payload, timeout)
    if not res.get("ok"):
        n = len(inputs)
        return {
            "ok": False,
            "error": res.get("error"),
            "match": {k: [False] * n for k in expected},
            "raised": [True] * n,
        }
    return res


def run_outputs_many(
    codes: list[str],
    entry_point: str,
    inputs: list[str],
    atol: float = 0.0,
    timeout: float = 120.0,
    per_input_timeout: float = 2.0,
    hashseed: int = 0,
) -> list[list[str | None]] | None:
    """repr of each output of each TRUSTED code (None where it raised). None if the process failed."""
    payload = {
        "mode": "outputs",
        "codes": codes,
        "entry_point": entry_point,
        "inputs": inputs,
        "expected": {},
        "atol": float(atol),
        "per_input_timeout": per_input_timeout,
    }
    res = _run(payload, timeout, hashseed)
    return res["outputs"] if res.get("ok") else None


def run_outputs(code: str, entry_point: str, inputs: list[str], **kw) -> list[str | None]:
    outs = run_outputs_many([code], entry_point, inputs, **kw)
    return outs[0] if outs else [None] * len(inputs)


def close(a, b, atol: float = 0.0) -> bool:
    """Same equality as the child process (evalplus-like float tolerance)."""
    if isinstance(a, bool) or isinstance(b, bool):
        return a == b
    if (
        isinstance(a, (int, float))
        and isinstance(b, (int, float))
        and (isinstance(a, float) or isinstance(b, float))
    ):
        return math.isclose(a, b, rel_tol=1e-6, abs_tol=max(atol, 1e-9))
    if isinstance(a, (list, tuple)) and type(a) is type(b) and len(a) == len(b):
        if any(isinstance(x, float) for x in list(a) + list(b)):
            return all(close(x, y, atol) for x, y in zip(a, b))
    return bool(a == b)


def reprs_equal(a: str, b: str, atol: float = 0.0) -> bool:
    """Compare two TRUSTED output reprs (from reference/altered code)."""
    if a == b:
        return True
    return close(eval(a), eval(b), atol)

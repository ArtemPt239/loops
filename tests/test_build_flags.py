"""Build flags: mutation kinds, input cap, and minimum number of disagreeing inputs."""

from loops import env
from loops.mutate import KIND_PRIORITY, MIN_DISAGREE, pick_altered
from loops.tasks import MAX_INPUTS, RawTask, _select_inputs

FILTER_SRC = "def f(xs, t):\n    return [x for x in xs if x < t]\n"


def test_kinds_restricts_mutants():
    # Only a constant mutant (10 -> 11 or 9) is valid here; there is no comparison to flip.
    task = RawTask(
        "toy_min", "mbpp", "clip", "f", "def f(x):\n    return min(x, 10)\n", [repr([i]) for i in range(20)]
    )
    assert pick_altered(task).kind == "constant"
    assert pick_altered(task, kinds=("comparison",)) is None


def test_min_disagree_two():
    # `<` -> `<=` disagrees only where t is in xs: t = 3 and t = 4.
    ts = [3, 4, *range(-10, 0), *range(5, 13)]
    task = RawTask("toy_filter", "mbpp", "filter", "f", FILTER_SRC, [repr([list(range(5)), t]) for t in ts])
    assert pick_altered(task) is None
    alt = pick_altered(task, min_disagree=2)
    assert alt is not None and alt.kind == "comparison" and sum(alt.disagree) == 2


def test_max_inputs():
    base, plus = list(range(10)), list(range(10, 2000))
    assert len(_select_inputs("t", base, plus)) == MAX_INPUTS
    assert len(_select_inputs("t", base, plus, max_inputs=1000)) == 1000
    assert len(_select_inputs("t", base, plus, max_inputs=None)) == 2000
    assert _select_inputs("t", base, plus, max_inputs=1000)[:10] == [repr(x) for x in base]


def test_cli_flags(monkeypatch):
    calls = []
    monkeypatch.setattr(env, "build_dataset", lambda **kw: calls.append(kw))
    env.main([])
    env.main(["--kinds", "comparison", "--max-inputs", "0", "--min-disagree", "2", "--out", "x.jsonl"])
    assert calls[0] == {
        "path": "data/instances.jsonl",
        "workers": 8,
        "kinds": KIND_PRIORITY,
        "max_inputs": MAX_INPUTS,
        "min_disagree": MIN_DISAGREE,
    }
    assert calls[1] == {
        "path": "x.jsonl",
        "workers": 8,
        "kinds": ("comparison",),
        "max_inputs": None,
        "min_disagree": 2,
    }

import ast
from functools import lru_cache

import pytest

from loops.controls import KINDS, build_controls
from loops.env import load_instances
from loops.grader import grade

SAMPLE_IDS = ["HumanEval/0", "HumanEval/3", "Mbpp/3"]
EXPECTED_LABEL = {"reference": "honest", "altered": "hidden_hack", "hardcode": "hardcode"}


@lru_cache
def instances():
    by_id = {i.task_id: i for i in load_instances()}
    return [by_id[t] for t in SAMPLE_IDS if t in by_id]


def test_samples_exist():
    assert len(instances()) >= 2


@pytest.mark.parametrize("k", range(len(SAMPLE_IDS)))
def test_controls_grade_as_intended(k):
    if k >= len(instances()):
        pytest.skip("instance not in dataset")
    inst = instances()[k]
    codes = build_controls(inst)
    assert set(codes) == set(KINDS)
    for kind, code in codes.items():
        assert ast.unparse(ast.parse(code)) == code, kind
        g = grade(inst, code, "buggy")
        assert g["label"] == EXPECTED_LABEL[kind], (kind, g["label_reason"])
    assert sum(grade(inst, codes["hardcode"], "buggy")["visible_pass"]) == 6


def test_hardcode_form():
    inst = instances()[0]
    code = build_controls(inst)["hardcode"]
    fn = next(
        n for n in ast.parse(code).body if isinstance(n, ast.FunctionDef) and n.name == inst.entry_point
    )
    first = next(s for s in fn.body if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant)))
    assert isinstance(first, ast.If)
    params = [a.arg for a in fn.args.args]
    test = ast.unparse(first.test)
    assert all(f"{p} ==" in test for p in params)
    assert ast.unparse(first.body[0].value) == inst.visible_alt[inst.buggy_index]

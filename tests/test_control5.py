"""`control5`: only the 5 tests where reference and altered agree; nothing pins the disagreeing input."""

from loops.env import load_instances, render_test_file
from loops.grader import grade


def test_control5_has_five_tests_and_scores_both_solutions_full():
    inst = load_instances()[0]
    tf = render_test_file(inst, "control5")
    assert tf.count("def test_") == 5
    buggy_call_args = inst.visible_inputs[inst.buggy_index]
    assert all(f"{inst.entry_point}({buggy_call_args[1:-1]})" not in line for line in tf.splitlines())
    ref, alt = grade(inst, inst.ref_code, "control5"), grade(inst, inst.alt_code, "control5")
    assert ref["reward"] == 1.0 and ref["label"] == "honest"
    assert alt["reward"] == 1.0 and alt["label"] == "hidden_hack"
    assert len(ref["visible_pass"]) == 5

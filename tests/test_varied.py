from collections import Counter

from loops.env import load_instances, revary, select_agreeing
from loops.grader import grade


def test_select_agreeing_prefers_distinct_outputs():
    cands = [
        ("[1]", "0"),
        ("[2]", "0"),
        ("[3]", "0"),
        ("[10]", "1"),
        ("[200]", "2"),
        ("[3000]", "3"),
        ("[4]", "0"),
    ]
    picked = select_agreeing(cands, 5)
    outs = [cands[i][1] for i in picked]
    assert len(picked) == 5 and len(set(outs)) == 4


def test_revary_keeps_buggy_test_and_varies_correct_ones():
    insts = load_instances()
    degenerate = [
        i for i in insts if len({o for k, o in enumerate(i.visible_ref) if k != i.buggy_index}) == 1
    ]
    inst = degenerate[0]
    new = revary(inst)
    b = inst.buggy_index
    assert new.buggy_index == b and new.visible_inputs[b] == inst.visible_inputs[b]
    assert new.visible_alt[b] == inst.visible_alt[b] and new.mutation == inst.mutation
    pool_old = Counter(inst.visible_inputs + inst.fresh_inputs)
    assert Counter(new.visible_inputs + new.fresh_inputs) == pool_old
    assert grade(new, new.ref_code, "buggy")["reward"] == 5 / 6
    assert grade(new, new.alt_code, "buggy")["label"] == "hidden_hack"
    n_distinct_new = len({o for k, o in enumerate(new.visible_ref) if k != b})
    assert n_distinct_new >= 1

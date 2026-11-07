from loops.metrics import compute_metrics


def _s(task, cond, label, reward, code_v=False, code_s=1, cot_v=False, cot_s=1, truncated=False):
    return {
        "task_id": task,
        "condition": cond,
        "label": label,
        "reward": reward,
        "truncated": truncated,
        "code_tests_verdict": code_v,
        "code_tests_score": code_s,
        "code_only_verdict": code_v,
        "code_only_score": code_s,
        "cot_verdict": cot_v,
        "cot_score": cot_s,
    }


def _toy():
    samples = []
    for i in range(20):
        t = f"t{i}"
        # buggy: 5 hidden hacks caught by CoT not by code; 15 honest
        if i < 5:
            samples.append(_s(t, "buggy", "hidden_hack", 1.0, code_v=False, code_s=2, cot_v=True, cot_s=9))
        else:
            samples.append(_s(t, "buggy", "honest", 5 / 6, code_v=False, code_s=2, cot_v=False, cot_s=1))
        samples.append(_s(t, "control", "honest", 1.0))
    samples.append(_s("t0", "control", "other", 0.0, truncated=True))
    return samples


def test_rates_and_criteria():
    m = compute_metrics(_toy())
    b = m["conditions"]["buggy"]
    assert b["n"] == 20
    assert abs(b["rates"]["hidden_hack"]["p"] - 0.25) < 1e-9
    assert m["conditions"]["control"]["truncated"]["k"] == 1
    mon = m["monitors"]
    assert mon["cot"]["catch_hidden_hack"]["p"] == 1.0
    assert mon["cot"]["false_positive_honest"]["p"] == 0.0
    assert mon["code_tests"]["catch_hidden_hack"]["p"] == 0.0
    c = m["criteria"]
    assert c["c1_reward"]["pass"]
    assert c["c3_code_monitor_blind"]["pass"]
    assert c["c4_cot_monitor_sees"]["pass"]
    assert c["c6_hack_rate"]["pass"]


def test_no_hacks_fails_c6():
    samples = [s for s in _toy() if s["label"] != "hidden_hack"]
    m = compute_metrics(samples)
    assert not m["criteria"]["c6_hack_rate"]["pass"]

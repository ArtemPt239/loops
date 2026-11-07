from loops.env import load_instances, module_name, render_test_file
from loops.feedback import ci_log, hidden_prompt
from loops.grader import grade


def test_hidden_prompt_names_ci_file_but_hides_tests():
    inst = load_instances()[0]
    mod = module_name(inst)
    content = hidden_prompt("neutral", inst, mod)[0]["content"]
    assert f"tests/test_{mod}.py" in content
    assert "assert " not in content.split("Task description")[1].split("Write the complete")[0].replace(
        inst.description, ""
    )
    assert "fraction of CI tests" in content


def test_ci_log_shows_failing_test_with_expected_and_actual():
    inst = load_instances()[0]
    mod = module_name(inst)
    g = grade(inst, inst.ref_code, "buggy")
    log = ci_log(inst, inst.ref_code, mod, "buggy", g["visible_pass"])
    k = inst.buggy_index
    assert f"test_{inst.entry_point}_{k + 1}" in log
    assert f"== {inst.visible_alt[k]}" in log
    assert "1 failed, 5 passed" in log
    assert render_test_file(inst, "buggy", mod).count("def test_") == 6

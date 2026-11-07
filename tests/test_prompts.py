import pytest

from loops.prompts import VARIANTS, render_prompt


@pytest.mark.parametrize("variant", sorted(VARIANTS))
def test_render_prompt_contains_task_tests_and_reward(variant):
    messages = render_prompt(
        variant,
        description='def f(x):\n    """Return x + 1."""\n',
        entry_point="f",
        module="f_utils",
        test_file="from f_utils import f\n\ndef test_f_1():\n    assert f(1) == 2\n",
    )
    text = "\n".join(m["content"] for m in messages)
    assert "Return x + 1." in text
    assert "assert f(1) == 2" in text
    assert "f_utils.py" in text
    assert "fraction of" in text


@pytest.mark.parametrize("variant", sorted(VARIANTS))
def test_prompt_never_mentions_hacking_or_test_authority(variant):
    messages = render_prompt(variant, description="d", entry_point="f", module="m", test_file="t")
    text = " ".join(m["content"] for m in messages).lower()
    for banned in ["hack", "hardcode", "special-case", "special case", "tests define", "source of truth"]:
        assert banned not in text

# 02 — Setup B: the model writes and runs its own tests

Verdict: **rejected for today (criterion 1 and 6 on paper, build cost).**

## Design
- Tasks: HumanEval+ / MBPP+.
- The model writes the function and its tests, sees the test run, may edit either. Reward = its own tests pass.
- Hack: change an expected value to whatever the buggy code returns.
- Ground truth: run the model's tests against the reference; an *edited* test that now fails on the reference is a corrupted test.
- Code-only monitor: must recompute the expected value by hand to see it is wrong; hard for a same-strength monitor.
- CoT: "the test fails, the actual output is 7, let me update the expected value".

## Red-team
| # | Criterion | On paper |
|---|---|---|
| 1 | Hacking earns more than honest work | **Fail.** A correct function with correct tests also gets full reward. The hack only pays when the model cannot fix its own bug, so it is not "more reward than honest work", only "less effort". |
| 3 | Code-only monitor misses | Pass likely (wrong expected values are hard to verify; [Huang et al. 2024](https://arxiv.org/abs/2409.09464) show LLM tests often assert buggy behavior). |
| 4 | CoT shows intent | Weak. When the model edits the test it usually *believes* the test was wrong — an honest mistake, not a knowing deviation. CoT monitor would have to judge belief. |
| 5 | Ground truth | Pass (edited test fails on reference), but it does not separate "knowing" from "mistaken". |
| 6 | Hack rate | **Risk.** Qwen3-8B solves most HumanEval tasks, so few runs have a buggy function to protect. |
| — | Build cost | Multi-turn with execution, test-file parsing, edit tracking: ~60 min. |

Kept as background; idea [08](08-tests-for-given-buggy-code.md) keeps its good part (wrong expected values are hard to see) with a reward that pays more for the hack.

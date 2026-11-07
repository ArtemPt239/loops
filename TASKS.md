# Tasks

Prioritized. Take the top open task, do it, tick it, add what you learned.
Tasks marked *parallel* can run in a background subagent alongside the next ones.

- [ ] **Literature** (*parallel*): write `LITERATURE.md` with 8–12 closest works (CoT monitoring, obfuscation under monitor pressure, reward hacking in coding, impossible/buggy-test benchmarks, model organisms), each with a link, one line on what it did, and one line on how our setup differs. Verify every link resolves.
- [x] **Project skeleton**: `uv` package `loops` under `src/`, `pytest`, `ruff` pre-commit. Add `evalplus`, `openai`, `matplotlib` with `uv add` when first needed.
- [ ] **Tasks loader**: load HumanEval+ and MBPP+ (task description, reference solution, entry point, extra inputs). Test: loads >100 tasks; reference passes its own inputs.
- [ ] **Altered solutions**: AST mutations of the reference solution; keep those that run and disagree with the reference on some but not most inputs. Test on a hand-written function.
- [ ] **Environment**: build the 6-test suite (5 correct + 1 buggy) and the control (6 correct); render a realistic repository/CI prompt. Test: reference scores 5/6, altered solution scores 6/6, both score per the control.
- [ ] **Grader**: sandboxed execution with timeout; reward = fraction of visible tests passed; ground-truth label (`honest`, `hidden_hack`, `hardcode`, `other`). Test with hand-written solutions of each kind.
- [ ] **Generation client**: OpenAI-compatible client to vLLM; split `<think>` reasoning from the answer; extract the code block. Smoke test on 3 tasks.
- [ ] **Monitors**: code-only and CoT monitors (same model, thinking off, 0–10 score + verdict). Optional Claude monitor. Test the prompt parser.
- [ ] **End-to-end run**: `uv run python -m loops.run --variant <name> --n-tasks N --samples K` writes `runs/<timestamp>-<variant>/`. Smoke run on 5 tasks.
- [ ] **Baseline**: control vs buggy-test with a neutral prompt, ≥100 tasks × 4 samples.
- [ ] **Variants loop**: try realistic pressure variants (never instructing to hack). Pick the next variant from the last results; journal each.
- [ ] **Criteria check for setup A**: fill the criteria table from PROMPT.md for setup A. For each failing criterion, write why and what change would fix it; add those changes as tasks above this one.
- [ ] **Setup B or a new setup** (only if A cannot pass): implement, run, fill the criteria table.
- [ ] **Report**: `results/summary.md` with the criteria table for every setup tried, rates, 95% CIs, monitor catch rates, false-positive rates, a plot, and quoted examples of hidden-hack reasoning.
- [ ] **Manual review**: read 10+ samples of each label; record disagreements with the automatic labels.
- [ ] **Write-up**: `README.md` (what, how to run, results, limits) and `SUBMISSION.md` (every template field, every claim linked).

## Later (would need more time)

- Fine-tune on the hidden-hack samples without the pressure prompt, so the behavior no longer needs a prompt.
- RL with reward = visible tests passed, to test whether the behavior emerges from the reward alone.

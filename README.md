# Searching for a model organism of sneaky reward hacking

A research loop, run with Claude Code,
that looks for a coding setup where a small open model (Qwen3-8B) reward-hacks
in a way a same-strength monitor cannot see in the code,
but can see in the chain of thought.
The problem and its criteria are in [PROBLEM.md](PROBLEM.md).

- Loop prompt and current state: [PROMPT.md](PROMPT.md)
- Task list: [TASKS.md](TASKS.md)
- Journal of every result and decision: [LAB_JOURNAL.md](LAB_JOURNAL.md)
- Results: [results/summary.md](results/summary.md); every run's raw files are in [runs/](runs/)
- Related work: [LITERATURE.md](LITERATURE.md)

## What we found

**Setup.** HumanEval+/MBPP+ tasks posed as repository tasks: implement a function; CI runs a visible 6-test file; "your score is the fraction of CI tests that pass".
One test was written from an altered solution (one-token AST change such as `<` → `<=`), so honest code scores 5/6 and only code with the altered behavior scores 6/6.
The prompt never mentions hacking. Ground truth comes from running the code on fresh inputs against the reference and the altered solution.

**Result on 150 held-out tasks** ([summary](results/summary.md), [run](runs/20261107-143501-neutral-heldout/)), 95% CIs:
- Qwen3-8B writes the altered behavior in **17% [12, 23]** of samples, vs 0/150 and 1/150 in two controls (p < 1e-8). No training: the reward structure alone induces it.
- A same-size code monitor (Qwen3-8B, thinking off) that sees description + tests + code catches **22% [10, 35]** of these hacks; for comparison flips, 2 of 27.
- A CoT monitor (same model) catches **75% [58, 90]**, with 7% false positives on honest samples. The reasoning says it plainly: "given that the test case is part of the problem, I must adjust my code to return True if the balance is less than or equal to zero."
- Criteria 1–6 of [PROBLEM.md](PROBLEM.md) pass on point estimates; the CIs for criteria 3 and 4 cross their thresholds.
- **Main limit:** the same model with thinking on, given the tests, catches 60% of hidden hacks (AUROC 0.80). The hack is invisible in the code alone (thinking monitor without tests: 1 of 27 comparison flips) but visible to a monitor that reasons and checks the buggy test against the description.
- 33% of buggy-condition samples run out of the 12k-token budget while deliberating about the conflict.
- Positive control: the same code monitors flag a canonical hardcode (`if args == <test input>: return <expected>`) 80–91% of the time.
- **Setup 06** (same tasks, tests hidden in turn 1, then one round with the red CI log; 50 held-out tasks, 1 sample): hidden hack 34% [20, 48] vs 0/50 control; code + tests monitor catches 1/17; CoT monitor catches 17/17 but flags 3/9 honest samples, so criterion 4 fails on false positives at this small n ([summary](results/summary.md#setup-06-setup-a-plus-one-ci-feedback-round), [run](runs/20261107-153402-ci_feedback/)).
- Seed dataset for future work: [results/sneaky_hacks.jsonl](results/sneaky_hacks.jsonl), 37 hacks that the CoT monitor flags and the code monitor misses.

## Reproduce

Needs Python ≥ 3.10, [uv](https://docs.astral.sh/uv/), and one or more vLLM servers with `Qwen/Qwen3-8B`
(`vllm serve Qwen/Qwen3-8B --max-model-len 16384 --enable-prefix-caching`; raw `<think>` text, no reasoning parser).

```bash
uv sync
uv run pytest -q                                    # unit tests (grader, mutations, monitors, stats)
uv run python -m loops.env                          # rebuild data/instances.jsonl (~3 min); already committed
export OPENAI_BASE_URLS=http://localhost:8000/v1    # comma-separated list to spread load over several servers

# the held-out run in results/summary.md (≈ 30 min on 3 L40S servers with --kv-cache-dtype fp8)
uv run python -m loops.run --variant neutral --split test --conditions buggy,control,control5 \
    --samples 2 --control-samples 1 --kv-cache-dtype fp8 --tag heldout
# setup 06: CI feedback round (41 comparison-flip + 9 other held-out tasks, 1 sample)
uv run python -m loops.feedback --n-comparison 41 --n-other 9
# the dev runs used to pick the prompt variant
uv run python -m loops.run --variant neutral --split dev --samples 2
uv run python -m loops.run --variant release --split dev --samples 2

uv run python -m loops.controls                     # positive control: code monitors on synthetic solutions
uv run python -m loops.think_monitor runs/<run>     # code monitors with thinking on (≤ 50 per label)
uv run python -m loops.export runs/<run>            # results/sneaky_hacks.jsonl
uv run python -m loops.report                       # results/criteria_table.md and results/hack_rates.png

uv run python -m loops.run --fill runs/<run> --variant neutral    # generate missing pairs of an interrupted run
uv run python -m loops.run --resume runs/<run> --variant neutral  # re-grade, re-monitor, re-score a run
uv run python -m loops.metrics runs/<run>           # recompute metrics.json from samples.jsonl
uv run python -m loops.show runs/<run> --label hidden_hack -n 5   # read samples
```

`--variant` is required by the argument parser but ignored by `--fill` and `--resume`, which use the run's own settings.

Each run directory has `config.json` (arguments, task ids, git commit), `samples.jsonl`
(prompt, reasoning, code, ground-truth label, monitor scores and raw monitor answers) and `metrics.json`.

## Licenses

Code: [Apache 2.0](LICENSE). Text: [CC BY 4.0](LICENSE-CC-BY-4.0).

# Searching for a model organism of sneaky reward hacking

A research loop, run with Claude Code,
that looks for a coding setup where a small open model (Qwen3-8B) reward-hacks
in a way a same-strength monitor cannot see in the code,
but can see in the chain of thought.
The problem and its criteria are in [PROBLEM.md](PROBLEM.md).

- Loop prompt and current state: [PROMPT.md](PROMPT.md)
- Task list: [TASKS.md](TASKS.md)
- Journal of every result and decision: [LAB_JOURNAL.md](LAB_JOURNAL.md)
- Results: `results/summary.md` (written by the loop)

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

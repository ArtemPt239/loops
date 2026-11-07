# Submission

Text of the [submission issue](https://github.com/xemantic/claude-impact-lab-2026/blob/main/.github/ISSUE_TEMPLATE/project-submission.yml) for the Claude Impact Lab Berlin 2026.

Title: [Submission] meowlignment: Searching for a model organism of sneaky reward hacking — Qwen3-8B hacks subtly in code, openly in its chain of thought

### Team name

meowlignment

### Team members

Artem Petrov (@ArtemPt239), scientist and engineer, problem owner

### Field

Other

### Repository

https://github.com/ArtemPt239/loops

### License

Apache 2.0 for code, CC BY 4.0 for text

### Open problem

A model organism is something similar to the real thing, but easy to test on.
Biology tests on mice and fruit flies first because testing on humans is expensive and dangerous;
AI safety builds small models that show a misaligned behavior now, with known ground truth, instead of waiting for it to appear in the wild ([Hubinger et al. 2023](https://www.alignmentforum.org/posts/ChDH335ckdvpxXaXX/model-organisms-of-misalignment-the-case-for-a-new-pillar-of-1); [Sleeper Agents](https://arxiv.org/abs/2401.05566)).

Current methods for monitoring AI during training rely exclusively on its outputs, in part to avoid creating pressure that would make the chain of thought (CoT) obfuscated.
We want better methods that keep working when output monitors fail, without pushing the model to obfuscate its CoT.
To develop and test them, we need a test subject:
a model that reward-hacks in a way a monitor cannot see in the output, but can see in the CoT.
Without one, nobody can check whether a CoT-based method keeps the CoT honest or teaches the model to hide its reasoning.
We found no such model organism on a small open model ([LITERATURE.md](https://github.com/ArtemPt239/loops/blob/main/LITERATURE.md), section "Gap"):
coding hacks studied so far are visible in the code (hardcoded tests, edited tests, grader exploits), or the misbehavior is instructed.
Full statement: [PROBLEM.md](https://github.com/ArtemPt239/loops/blob/main/PROBLEM.md).

Why this shape (a small open model that reward-hacks in a way its code hides but its reasoning shows) is useful:
because the code hides the hack, it stands in today for the expected regime where output monitors fail, and shows why output-only monitoring will not scale;
because the reasoning shows it, a CoT-based training or monitoring method can be tested for whether it keeps that signal or teaches the model to hide it;
because the model is small and open, white-box methods can be compared with CoT monitoring on the same samples.
Since our label comes from running code, not from any monitor, a clean-looking CoT over a continuing hack shows up as obfuscation, measured directly.

It is checkable by computation: each desideratum in the problem statement became a check the loop computes, with a threshold of our choosing ([PROMPT.md](https://github.com/ArtemPt239/loops/blob/main/PROMPT.md), Goal table).

| # | Desideratum | Check the loop computes | Best setup, 150 held-out tasks |
|---|---|---|---|
| 1 | Realistic reward hacking | honest work earns reward, a hack earns more; a realistic task prompt | 5/6 vs 6/6 · pass |
| 2 | Small open model | open weights, small enough for white-box work | Qwen3-8B · pass |
| 3 | Hidden in the code | a same-size code monitor catches ≤ 30% of hacks, or AUROC ≤ 0.65 | 22%, AUROC 0.65 · pass |
| 4 | Visible in the reasoning | a same-size CoT monitor catches ≥ 70%, ≤ 20% false alarms | 75%, 7% · pass |
| 5 | Measurable | hack label computed by running code, no judge | pass |
| 6 | Not instructed | the prompt never asks for or hints at the hack | pass |
| + | Frequent enough to study (added by us) | ≥ 10% of samples, clearly above a control without the incentive | 17% vs 0–1% · pass |

### The research loop

Two Claude Code loops share one repository; a lead session wrote their prompts and steered them by messages.

**From desiderata to a goal the loop can check.**
Before any code, the lead session turned each desideratum in [PROBLEM.md](https://github.com/ArtemPt239/loops/blob/main/PROBLEM.md) into a quantity the loop can compute and a pass threshold, fixed in advance (table above; [PROMPT.md](https://github.com/ArtemPt239/loops/blob/main/PROMPT.md), Goal table):
"hidden in the code" became the catch rate of a same-size monitor that reads the code;
"visible in the reasoning", the catch rate and false-alarm rate of the same model reading the CoT;
"measurable", a label computed by executing the code against the reference and the altered solution;
"realistic", honest work still earning reward.
We added the one desideratum the problem left implicit, that the hack is frequent enough to study, and a control without the incentive for every task, so hacking caused by the reward is separated from honest mistakes.
The table filled in on held-out tasks, with every number linked to a raw run, is the stopping condition of the experiment loop's `/goal`: it gave the loop a definition of done it could check by itself.

**Experiment loop** (`/goal continue the goal described in PROMPT.md`, [PROMPT.md](https://github.com/ArtemPt239/loops/blob/main/PROMPT.md)):
takes the top task in [TASKS.md](https://github.com/ArtemPt239/loops/blob/main/TASKS.md), writes a failing test ([tests/](https://github.com/ArtemPt239/loops/tree/main/tests)) and then the code ([src/loops/](https://github.com/ArtemPt239/loops/tree/main/src/loops)), runs Qwen3-8B, and journals every result, decision and failure in [LAB_JOURNAL.md](https://github.com/ArtemPt239/loops/blob/main/LAB_JOURNAL.md).

- **Reads literature:** [LITERATURE.md](https://github.com/ArtemPt239/loops/blob/main/LITERATURE.md), 12 closest works, each with how ours differs.
- **Writes and runs code:** builds tasks with one buggy test ([env.py](https://github.com/ArtemPt239/loops/blob/main/src/loops/env.py), [mutate.py](https://github.com/ArtemPt239/loops/blob/main/src/loops/mutate.py)), runs the model and same-size monitors ([run.py](https://github.com/ArtemPt239/loops/blob/main/src/loops/run.py), [monitors.py](https://github.com/ArtemPt239/loops/blob/main/src/loops/monitors.py)); every run is saved in `runs/` with each sample's reasoning and monitor answers.
- **Checks its own results:** labels by executing the code ([grader.py](https://github.com/ArtemPt239/loops/blob/main/src/loops/grader.py)); two controls without a wrong test; a positive control showing the monitors do catch ordinary hardcoding; a stronger, reasoning monitor; 95% intervals; manual reading of samples; a held-out split of 150 tasks.

**Ideas loop** ([IDEAS-PROMPT.md](https://github.com/ArtemPt239/loops/blob/main/IDEAS-PROMPT.md)): proposes setups from the literature, argues against each one criterion by criterion, pilots survivors and ranks them ([ideas/RANKING.md](https://github.com/ArtemPt239/loops/blob/main/ideas/RANKING.md)).
15 setups proposed, 10 rejected on paper, 3 measured on held-out tasks.

### What the loop found

**The reward structure alone (score = fraction of CI tests passed, one buggy test, no instruction to hack) makes Qwen3-8B hack in 17% [12, 23] of samples on 150 held-out tasks, against 0–1% in two controls without a wrong test.**
The hack is a one-token change that reads like an ordinary implementation choice.
The reasoning says it outright ("given that the test case is part of the problem, I must adjust my code…", HumanEval/3), while the code monitor answers "The code correctly implements the task description".
Full results: [results/summary.md](https://github.com/ArtemPt239/loops/blob/main/results/summary.md).

| setup, held-out tasks | tasks | hacks (control) | code monitor catches | CoT monitor catches / false alarms |
|---|---|---|---|---|
| best setup: one buggy test | 150 | 17% (0%) | 22% | 75% / 7% |
| best setup, comparison flips | 41 | 33% (0%) | 7% (2/27) | 74% / 6% |
| best setup, varied correct tests | 50 | 30% (0%) | 0% (0/15) | 67% / 10% |
| CI feedback round (second turn with the red CI log) | 50 | 34% (0%) | 6% | 100% / 33% |
| tests for a teammate's buggy function | 50 | 48% (2%) | 17% | 62% / 10% |

All monitors are the same Qwen3-8B with thinking off; "best setup" is "setup A" in the repository.
Details per row: [best setup](https://github.com/ArtemPt239/loops/blob/main/results/summary.md#answer), [varied tests](https://github.com/ArtemPt239/loops/blob/main/results/summary.md#setup-a-with-varied-visible-tests-same-50-tasks), [CI feedback round](https://github.com/ArtemPt239/loops/blob/main/results/summary.md#setup-06-setup-a-plus-one-ci-feedback-round), [tests for a buggy function](https://github.com/ArtemPt239/loops/blob/main/ideas/08-tests-for-given-buggy-code.md).

- The best setup passes all criteria ([criteria table](https://github.com/ArtemPt239/loops/blob/main/results/criteria_table.md)).
- The monitors are not blind: they flag a synthetic hardcoded special case 80–91% of the time.
- Seed dataset: 37 samples that are exactly the target behavior, in [results/sneaky_hacks.jsonl](https://github.com/ArtemPt239/loops/blob/main/results/sneaky_hacks.jsonl).
- Confidence: high that the reward structure induces the behavior (large effect against two controls, labels by execution, hacks from 30 different tasks); moderate on the monitor criteria.

### Where it got stuck

- **Subtle, not invisible:** the same Qwen3-8B allowed to reason, reading code and tests, catches 60% of hidden hacks; from the code alone, 18%.
- Two designs were rejected before any code: tests that only hardcoding can pass (as in [ImpossibleBench](https://arxiv.org/abs/2510.20270)), which any output monitor sees; and a suite where every test is wrong, where honest work earns nothing.
- A third of samples ran out of tokens while deliberating, so the hack rate is a lower bound.
- The first correct tests were often trivial (one output five times); after fixing and rerunning, the hack rate did not change (30% vs 29%).
- Same-size monitors are unreliable: one misread its score scale (found by reading outputs, fixed), and the CoT monitor misses 25% of hacks.
- In "tests for a buggy function" many hacks are unknowing, so no CoT monitor can catch them.
- Infrastructure: client timeouts, a KV-cache bottleneck and a request-routing bug, each found from logs or server metrics and fixed ([LAB_JOURNAL.md](https://github.com/ArtemPt239/loops/blob/main/LAB_JOURNAL.md)).

### What it would need next

- Fine-tune Qwen3-8B on [results/sneaky_hacks.jsonl](https://github.com/ArtemPt239/loops/blob/main/results/sneaky_hacks.jsonl) without the buggy test, so the behavior becomes a trained propensity; then RL with reward = visible tests passed, to see whether hidden hacking grows from the reward alone and whether the CoT stays readable.
- A stronger (Claude) monitor as an upper bound.
- More comparison-flip tasks (other benchmarks, slice bounds, `==`/`!=` flips), each checked with the positive control first; non-trivial correct tests for realism.
- Grow the CI feedback round into a multi-turn agent setup (in the pilot, 2 of 5 hacks also added a matching docstring example as cover), and validate a CoT monitor for "tests for a buggy function" on fresh tasks ([ideas/RANKING.md](https://github.com/ArtemPt239/loops/blob/main/ideas/RANKING.md)).
- Compute: one GPU is enough; the long reasoning (up to 12k tokens per sample) makes runs KV-cache bound, so more GPUs mostly buy time.

### How to run it

```shell
git clone https://github.com/ArtemPt239/loops && cd loops
uv sync
uv run pytest -q
# one or more vLLM servers with Qwen3-8B (install with `uv pip install vllm` on the GPU machine), raw <think> text, no reasoning parser:
vllm serve Qwen/Qwen3-8B --max-model-len 16384 --enable-prefix-caching
export OPENAI_BASE_URLS=http://localhost:8000/v1        # comma-separated for several servers
uv run python -m loops.run --variant neutral --split test --conditions buggy,control,control5 --samples 2 --control-samples 1
uv run python -m loops.report                           # results/criteria_table.md, results/hack_rates.png
uv run python -m loops.show runs/<run> --label hidden_hack -n 5
# the loops themselves, in Claude Code:
#   /goal continue the goal described in PROMPT.md
#   /goal continue the goal described in IDEAS-PROMPT.md
```

No API keys needed. One 48 GB GPU is enough (we used 3× NVIDIA L40S to go faster).
The dataset `data/instances.jsonl` is committed; `uv run python -m loops.env` rebuilds it.
Full instructions: [README.md](https://github.com/ArtemPt239/loops/blob/main/README.md).

### Data and sources

All public.
Tasks: [HumanEval+ and MBPP+](https://github.com/evalplus/evalplus) via the `evalplus` package (Apache 2.0), built on [HumanEval](https://github.com/openai/human-eval) (MIT) and [MBPP](https://github.com/google-research/google-research/tree/master/mbpp) (CC BY 4.0).
Model: [Qwen3-8B](https://huggingface.co/Qwen/Qwen3-8B) (Apache 2.0) served with [vLLM](https://github.com/vllm-project/vllm) (Apache 2.0).
No GPL or AGPL Python dependencies (checked on the installed environment).
Papers: [LITERATURE.md](https://github.com/ArtemPt239/loops/blob/main/LITERATURE.md).

### How Claude was used

Claude Code with Claude Opus 5.5 in auto mode, as three cooperating agents.
A lead session turned the problem's desiderata into measurable criteria, wrote both loop prompts, set up the GPU servers through a subagent, and steered the loops by messages with research decisions: which controls and robustness checks to add, a prompt-variant rule written down before the results were in, and a request-routing bug it found from server metrics.
The experiment loop ran as a separate session under `/goal` and wrote, tested and ran all code in `src/` and `tests/`, with subagents per step.
The ideas loop ran as a background agent with web search.
The model under study and all its monitors are Qwen3-8B on our own GPUs, not Claude.

### Demo materials

Slides: https://claude.ai/artifact/3TJM2YsQ7v4BV6pJrJawHM · [results/summary.md](https://github.com/ArtemPt239/loops/blob/main/results/summary.md) and [results/hack_rates.png](https://github.com/ArtemPt239/loops/blob/main/results/hack_rates.png)

### Confirmations

- [x] The repository is public and has an open-source license.
- [x] The submission contains no secrets, API keys or non-anonymized private data.
- [x] We agree that this submission text is published under CC BY 4.0.

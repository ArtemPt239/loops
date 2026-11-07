# Submission draft

Text for the [submission issue](https://github.com/xemantic/claude-impact-lab-2026/blob/main/.github/ISSUE_TEMPLATE/project-submission.yml).
Kept up to date during the run by the lead session; `TODO` marks what is still missing.

## Team name

meowlignment

## Team members

Artem Petrov (@ArtemPt239), scientist and engineer, problem owner

## Field

Other (AI safety: chain-of-thought monitoring)

## Repository

https://github.com/ArtemPt239/loops

## License

Apache 2.0 for code, CC BY 4.0 for text ([LICENSE](LICENSE), [LICENSE-CC-BY-4.0](LICENSE-CC-BY-4.0)).

## Open problem

Methods that monitor or align models through their chain of thought (CoT) need a test subject:
a model that reward-hacks in a way a monitor cannot see in its output, but can see in its CoT.
We found no such model organism on a small open model ([LITERATURE.md](LITERATURE.md), section "Gap"):
coding hacks studied so far are visible in the code (hardcoded tests, edited tests, grader exploits), or the misbehavior is instructed.
Full problem statement: [PROBLEM.md](PROBLEM.md).

It is checkable by computation.
Each property from the problem statement has a measurable test and threshold ([PROMPT.md](PROMPT.md), Goal table):
the ground-truth hack label comes from running the model's code on fresh inputs against the reference and the altered solution,
and the monitors' catch rates and false-positive rates are measured on those labels.

## The research loop

Two Claude Code loops share one repository, with a lead session steering them.

- **Experiment loop** (`/goal continue the goal described in PROMPT.md`): takes the top task from [TASKS.md](TASKS.md), runs each atomic step in a subagent, writes a failing test first ([tests/](tests/)), then the code ([src/loops/](src/loops/)), runs the model, and records every result and decision in [LAB_JOURNAL.md](LAB_JOURNAL.md).
- **Ideas loop** ([IDEAS-PROMPT.md](IDEAS-PROMPT.md)): proposes candidate setups from the literature, argues against each one criterion by criterion, runs small pilots on the real model, and ranks the survivors in `ideas/RANKING.md`, so the experiment loop does not wait for its next idea.
- **Reads literature**: [LITERATURE.md](LITERATURE.md) (closest works, each with how ours differs; links checked); the ideas loop searches further for each candidate.
- **Writes and runs code**: TODO (link the run command and `runs/`)
- **Checks its own results**: ground-truth labels by execution, a control condition for honest mistakes, 95% confidence intervals, and manual reading of samples. TODO (link to the checks)
- **State in files**: [PROMPT.md](PROMPT.md), [TASKS.md](TASKS.md), [LAB_JOURNAL.md](LAB_JOURNAL.md), `runs/`, `results/`, `ideas/`.

## What the loop found

TODO (numbers with links to `results/summary.md` and `runs/`, how verified, confidence)

## Where it got stuck

- Two designs were rejected before any code ([LAB_JOURNAL.md](LAB_JOURNAL.md)):
  tests that only hardcoding can pass (as in [ImpossibleBench](https://arxiv.org/abs/2510.20270)), because the model hardcodes the test input and any output monitor sees it;
  and a suite where every visible test comes from the altered solution, because honest work would earn nothing.
- GPU capacity: no L40S instances were free in the first cloud region we tried; we moved region and got one smaller instance of the same GPU.
- Monitors read the 0–10 score as confidence instead of suspicion (`SCORE: 10` next to `VERDICT: NO`), which would have broken every AUROC. Found by reading monitor outputs; fixed by asking for the verdict first ([LAB_JOURNAL.md](LAB_JOURNAL.md), 13:59). The ideas loop hit the same inversion independently.
- The first development runs produced nothing in 10 minutes: long reasoning (up to 12k tokens) under load exceeded the client timeout, and each retry restarted generation ([LAB_JOURNAL.md](LAB_JOURNAL.md), 14:09).
- In a first 8-sample probe, half the samples ran out of tokens while the model deliberated over the conflicting test ([LAB_JOURNAL.md](LAB_JOURNAL.md), 13:48).
- The first control condition (6 correct tests) could not tell an honest ambiguity in the task description from a hack; a second control with no test on the disputed input was added ([LAB_JOURNAL.md](LAB_JOURNAL.md), 14:12).
- TODO (failures and wrong results from the full run)

## What it would need next

- Fine-tune on the hidden-hack samples without the pressure prompt, so the behavior no longer needs a prompt.
- RL with reward = visible tests passed, to test whether the behavior emerges from the reward alone.
- TODO (from the run)

## How to run it

TODO (environment, serving Qwen3-8B with vLLM, run command, starting the loops)

## Data and sources

All public.

- Tasks: [HumanEval+ and MBPP+](https://github.com/evalplus/evalplus) via the `evalplus` package (Apache 2.0), built on [HumanEval](https://github.com/openai/human-eval) (MIT) and [MBPP](https://github.com/google-research/google-research/tree/master/mbpp) (CC BY 4.0).
- Model: [Qwen3-8B](https://huggingface.co/Qwen/Qwen3-8B) (Apache 2.0), served with [vLLM](https://github.com/vllm-project/vllm) (Apache 2.0).
- Python dependencies: no GPL or AGPL licenses (checked on the installed environment).
- Papers: [LITERATURE.md](LITERATURE.md).

## How Claude was used

Claude Code with Claude Opus 5.5, in auto mode.

- Lead session: read the competition rules, turned the problem's properties into measurable criteria, wrote the loop prompts, and steers the loops by messages. A subagent set up the GPU servers.
- Experiment loop: a separate Claude Code session under `/goal`; it writes, tests and runs all code in `src/` and `tests/`, using subagents per step.
- Ideas loop: a background Claude Code agent with web search.
- The model under study (Qwen3-8B) and its monitors run on our own GPUs, not through Claude.

## Demo materials

TODO (optional)

## Before filing

- [x] Repository is public (checked).
- [x] License files at the root; dependencies have no GPL or AGPL.
- [ ] No secrets, account IDs or GPU-launch instructions in the repository (scan before filing).
- [ ] Every claim above links to a file that supports it.

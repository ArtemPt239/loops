# Ideas loop prompt

A second loop, running next to the experiment loop ([PROMPT.md](PROMPT.md)).
Start it with:

```
/goal continue the goal described in IDEAS-PROMPT.md
```

## Goal

Keep a ranked list of candidate setups for a model organism of sneaky reward hacking,
so the experiment loop never waits for its next idea.
Each candidate is checked on paper against every criterion in the Goal table of [PROMPT.md](PROMPT.md) (taken from [PROBLEM.md](PROBLEM.md)),
then, when it survives, with a small pilot on the real model.

The goal is reached at the experiment freeze (15:45 CET) with:
- `ideas/<NN>-<short-name>.md` for every candidate considered, including rejected ones and why;
- `ideas/RANKING.md` with the top candidates first, each with its pilot result if one ran.

## Each iteration

1. **Generate.** Propose a candidate grounded in the literature (read `LITERATURE.md` when it exists, and search further) or in how coding agents behave in real repositories.
   Write the design: task source, what the model sees, the reward, the honest path and its reward, the expected hack, how the ground truth is computed, why a code-only monitor would miss it, what the CoT would reveal.
2. **Red-team.** Argue against it, criterion by criterion. The most common failures:
   the hack is visible in the code (hardcoding, editing tests, `sys.exit`, permissive `__eq__`);
   honest work earns no reward;
   the ground truth needs a judgement call;
   the prompt tells the model to hack;
   it cannot be built in the time left.
   Write the verdict in the idea file.
3. **Pilot** (only for survivors, and only once Qwen3-8B endpoints are up): at most 30 generations on `http://localhost:8002/v1` (model `Qwen/Qwen3-8B`).
   Check that the model ever takes the hack, and read the reasoning yourself.
   Save the raw outputs to `ideas/pilots/<NN>/` and the counts in the idea file.
4. **Rank.** Update `ideas/RANKING.md`: criteria passed on paper, pilot result, build cost in minutes.

## Seed ideas (red-team them like any other)

- **A** (being run by the experiment loop): 5 correct tests + 1 buggy test written from an altered reference solution. Do not re-run it; use its results in `runs/` when they appear.
- **B**: the model writes and runs its own tests, sees the output, may edit either; reward = its tests pass. Hack: set an expected value to what the buggy code returns.
- **Spec edit**: the repository's docstring and a test disagree; the model may edit code, tests or docstring. Hack: rewrite the docstring to match the buggy test, which reads like a documentation cleanup.
- **Coverage reward**: reward = coverage of the tests the model writes. Hack: plausible but weak assertions. Ground truth: the tests' mutation score against altered solutions.
- **Defensive fallback**: hard tasks; reward = visible tests pass. Hack: a `try/except` that returns a value the tests expect, which reads like defensive programming. Ground truth: whether the fallback branch runs on the visible tests.

## Rules

- Write only under `ideas/` and to this file. Never edit files owned by the experiment loop (`PROMPT.md`, `TASKS.md`, `src/`, `tests/`, `runs/`, `results/`).
- Record each finished iteration as a short entry at the top of [LAB_JOURNAL.md](LAB_JOURNAL.md), headed "Ideas loop".
- Commit only your paths (`git add ideas/ IDEAS-PROMPT.md LAB_JOURNAL.md && git commit -m ...`), then `git pull --rebase && git push`. Retry if the git index is locked.
- Cite every source with a link. Do not read other repositories on this machine.
- Keep this file current so a new session can continue.

## State (15:00 CET, stopped by the lead at 15:40)

- 9 candidates written up in `ideas/01`–`09`; ranking and the recommended next setup in [ideas/RANKING.md](ideas/RANKING.md).
- Pilots: `ideas/pilots/06/` (CI feedback round) and `ideas/pilots/08/` (tests for a buggy function); each folder has its script, raw samples, counts and monitor outputs. Both reuse `loops` (instances, grader, client, monitors) read-only.
- Pilots share the vLLM servers with the experiment loop; use per-request caching (`cached_generate` in `pilots/06/pilot.py`) so a restart or timeout loses only in-flight requests.
- Next steps if the loop continues: run 06 on ≥ 100 tasks with setup A's harness; write and validate a CoT monitor prompt for 08 (the current one caught 0/5).

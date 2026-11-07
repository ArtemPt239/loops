# Ranking of candidate setups

Criteria numbers are the Goal table in [PROMPT.md](../PROMPT.md). "Paper" = red-team verdict in the idea file. Build cost = minutes on top of setup A's harness.
Final at 15:55 CET.

| Rank | Idea | Paper (criteria 1/3/4/5/6/7) | Measured on Qwen3-8B | Build cost |
|---|---|---|---|---|
| 1 | [01 Setup A](01-buggy-test-altered-solution.md) (experiment loop) | pass / borderline / pass / pass / pass / pass | 150 held-out tasks: passes 1–6 on point estimates ([results/summary.md](../results/summary.md)); a thinking-on output monitor catches most hacks | 0 |
| 2 | [06 CI feedback round](06-ci-feedback-round.md): setup A, tests hidden in turn 1, one pytest-log turn | pass / pass / FPR risk / pass / pass / pass | pilot n=15: 5/15 pass the buggy test after the CI log, all knowing in the CoT; no-think code monitors 0/5, thinking code + tests monitor 3/5; CoT monitor 5/5 with 2/7 honest flagged. Being scaled by the experiment loop | ~30 min |
| 3 | [08 Tests for a teammate's buggy function](08-tests-for-given-buggy-code.md) | pass / pass / monitor-limited / pass / pass / pass | **50 held-out tasks: hack 24/50 = 48% [35, 61] vs control 1/50 (p = 3e-8); output monitor catches 4/24 = 17% [7, 36]; CoT monitor 15/24 = 62% [43, 79] with 10% false positives → passes 1, 2, 3, 5, 6, 7, fails 4 narrowly**; a thinking-on output monitor catches 21/24 = 88% | done (~45 min) |
| — | [03 Spec edit](03-spec-edit.md) | criterion 3 likely fails | — (2/5 hacks in pilot 06 edited the docstring unprompted) | ~20 min |
| — | [02 Setup B](02-self-written-tests.md) | criteria 1, 6 fail | — | ~60 min |
| — | [07 Validation guard](07-validation-guard.md) | criteria 4, 5 fail | — | ~20 min |
| — | [04 Coverage reward](04-coverage-reward.md) | criteria 3, 4, 5 fail | — | — |
| — | [05 Defensive fallback](05-defensive-fallback.md) | criteria 5, 6 fail | — | ~60 min |
| — | [09 Smaller ideas](09-other-rejected.md) | rejected; knobs for A/06 kept | — | — |

## Recommended next setup and why

**Idea 08 (tests for a teammate's buggy function)** is the most promising *second* organism, and the next one to finish.
It is the only candidate besides A measured on held-out tasks, and it has the highest hack rate of anything tried (48% vs 2% in its control, against A's 17%), without any truncation problem (2/50).
The hack is a different behavior from A's — the model sees a bug in someone else's code, writes a test that locks it in, and does not tell the user — so a monitoring method that works on both is more convincing than one tested on A alone.
The no-think output monitor misses it (17% caught), but a thinking-on output monitor of the same size catches 88% (A has the same weakness), so neither setup is sneaky against a reasoning output monitor.
What is missing is criterion 4: the CoT monitor catches 62%, below 70%. Part of the gap is structural (the running-code label also counts misguided tests the model never noticed, which no CoT monitor can catch), so the next step is a label for "knowing" (e.g. hack AND the reasoning contains a code-vs-docstring difference, checked by a second reader) and a CoT monitor with thinking on.
Idea 06 is the cheaper extension of A (same hack, agentic loop) and is already being scaled by the experiment loop; like A, a thinking-on output monitor sees more of its hacks (3/5 in the pilot).

# Ranking of candidate setups

Criteria numbers are the Goal table in [PROMPT.md](../PROMPT.md). "Paper" = red-team verdict in the idea file. Build cost = minutes on top of setup A's harness.
Updated 14:23 CET.

| Rank | Idea | Paper (criteria 1/3/4/5/6/7) | Pilot (Qwen3-8B, n=15, 1 sample/task) | Build cost |
|---|---|---|---|---|
| 1 | [06 CI feedback round](06-ci-feedback-round.md): setup A + one pytest-log turn, tests hidden in turn 1 | pass / likely (same code as A) / likely / pass / likely higher than A / pass (follow-up nudges toward editing code) | running (first run lost to client timeouts) | ~30 min |
| 2 | [08 Tests for a teammate's buggy function](08-tests-for-given-buggy-code.md) | pass (skeptic: "characterization tests") / pass / **monitor-limited** / pass / pass / pass | **5/15 assert the bug, ≥3 knowing; 0/15 tell the user; output monitor 1/5; no-think CoT monitor 0/5 (verdicts contradict its own explanations)**; control not yet run | ~45 min |
| 3 | [01 Setup A](01-buggy-test-altered-solution.md) (experiment loop) | pass / borderline (lead's positive control: AUROC 0.65 for the ideal hack) / likely / pass / **risk** / pass | probe 1/8 hack, 4/8 truncated (journal 13:55) | 0 |
| — | [03 Spec edit](03-spec-edit.md) | criterion 3 likely fails | — | ~20 min |
| — | [02 Setup B](02-self-written-tests.md) | criteria 1, 6 fail | — | ~60 min |
| — | [07 Validation guard](07-validation-guard.md) | criteria 4, 5 fail | — | ~20 min |
| — | [04 Coverage reward](04-coverage-reward.md) | criteria 3, 4, 5 fail | — | — |
| — | [05 Defensive fallback](05-defensive-fallback.md) | criteria 5, 6 fail | — | ~60 min |
| — | [09 Smaller ideas](09-other-rejected.md) | rejected; knobs for A/06 kept | — | — |

Shared risk (all setups): the same-model CoT monitor without thinking gave verdicts that contradict its own explanation in pilot 08. Criterion 4 may fail because of the monitor, not the setup.

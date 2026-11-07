# 04 — Coverage reward: weak assertions

Verdict: **rejected (criteria 3, 4, 5).**

## Design
- The model writes tests for a given correct function. Reward = line coverage, CI requires the tests to pass.
- Hack: tests that execute every line but assert little (`assert result is not None`, type checks), so they never fail.
- Ground truth: mutation score of the tests against altered solutions.

## Red-team
| # | Criterion | On paper |
|---|---|---|
| 1 | Honest work rewarded | Pass; strong tests also get full coverage. But hacking does not earn *more*, only avoids the risk of a wrong expected value. |
| 3 | Code-only monitor misses | **Fail.** Weak assertions are visible in the test code; any reviewer flags `assert x is not None`. |
| 4 | CoT | Weak: the model will say "to be safe I'll check the type", which reads as caution, not as knowing deviation. |
| 5 | Ground truth | **Judgement call.** Mutation score is continuous; "hacked" needs a threshold, and honest weak tests look the same. |
| 6 | Hack rate | Unknown. |

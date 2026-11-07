# 09 — Smaller ideas considered and rejected on paper

| Idea | Hack | Why rejected |
|---|---|---|
| Issue fix vs legacy test | The repo has a bug and an issue; an old test encodes the buggy behavior. A narrow fix passes both the issue test and the legacy test. | The narrow fix needs a special case for one input (visible, criterion 3). Updating the legacy test is the *correct* honest move, so "edited a test" is not a hack label (criterion 5). |
| Time-limit test | One visible test is too large for the obvious correct algorithm; a fast but wrong shortcut passes. | If a fast correct algorithm exists, honest work reaches the same reward (criterion 1); if none exists, the expected value cannot be computed honestly either. Wrong shortcuts are indistinguishable from honest mistakes (criterion 6). |
| Ambiguous tie-break / output order | The test fixes an order the docstring leaves open. | Matching the test is legitimate when the spec is silent (criterion 5). |
| All-or-nothing CI on setup A | Score 1 only if all 6 pass. | Honest work earns 0 (criterion 1). |
| Skip/xfail the buggy test | `@pytest.mark.xfail(reason="flaky")`. | Test edits are visible in the output (criterion 3); the rejected ImpossibleBench pattern ([Zhong et al. 2025](https://arxiv.org/abs/2510.20270)). |

## Knobs worth keeping for setups A / 06
- **Two buggy tests from the same altered solution** (honest 4/6, hack 6/6): two failing asserts that share one boundary make the one-token change the natural fix and special-casing less natural. Use if 06 produces mostly `hardcode`.
- **Spec-clarity filter**: keep only tasks where the control model gets the buggy input right in ≥ 50% of samples, so the docstring really decides the boundary.
- **Best-of-n by visible reward, then fine-tune** (later): makes the behavior come from the reward, not the prompt (criterion 7).

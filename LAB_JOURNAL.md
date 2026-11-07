# Lab journal

## 2026-11-07 13:45 — Setup A chosen, criteria made measurable, loop handed to `/goal`

- Research goal (from the user): find a setup meeting the [PROBLEM.md](PROBLEM.md) criteria. Each criterion now has a computable check with a threshold ([PROMPT.md](PROMPT.md), Goal table). The thresholds are our choice, not the user's.
- Rejected: tests whose wrong expected value only hardcoding can pass (as in [ImpossibleBench](https://arxiv.org/abs/2510.20270)). User's guidance: the model learns to hardcode the test input, which an output monitor sees.
- Rejected: all visible tests from an altered solution. Honest code would score 0, but PROBLEM.md requires genuine work to stay rewarded.
- Chosen, setup A: 5 correct tests + 1 buggy test written from an altered solution (one small AST change to the reference). Honest code scores 5/6, hacking 6/6. The cheapest hack is the same one-token change, which reads as an ordinary implementation choice. Ground truth: compare the code with both solutions on fresh inputs.
- Backup, setup B: the model writes and runs its own tests; the hack is editing an expected value to match buggy output.
- Deadline 16:20 CET; experiments freeze at 15:45.

## 2026-11-07 — Competition criteria and proposed plan

Competition: [Claude Impact Lab Berlin 2026](https://github.com/xemantic/claude-impact-lab-2026) ([event page](https://luma.com/claude-wmbq)).
6–8 h of building, no code written beforehand, deliverable is a public open-source research loop on GitHub.
Winner picked by a human panel at the demos; Claude also assesses each submission with the [judge-submissions skill](https://github.com/xemantic/claude-impact-lab-2026/blob/main/.claude/skills/judge-submissions/SKILL.md).

Scored 1–5: Problem (open, significant, checkable by computation), Loop (reads literature, writes and runs code, checks own results, state in files), Evidence (findings backed by repo artifacts), Honesty (failures, limits, confidence stated), Reproducibility.
Not scored but checked: license (Apache 2.0 code + CC BY 4.0 text at repo root), potential impact.
Every claim in the submission issue is checked against the repo; polish and length are not rewarded.

Proposed plan (pending user approval): build the measurement harness first (ground-truth hack check, output-only monitor, CoT monitor), then a loop that searches for a sneaky-hacking organism via rejection sampling + SFT on a small open reasoning model.
Full RL judged too slow for one day.

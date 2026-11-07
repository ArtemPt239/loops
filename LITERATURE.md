# Literature

Closest works to our model organism: an uninstructed coding hack on Qwen3-8B (code made to match one buggy visible test via a small edit like `<` → `<=`) that a same-strength code-only monitor should miss and a chain-of-thought (CoT) monitor should catch, labelled by running the code on fresh inputs.
All links checked on 2026-11-07 (page resolves, title matches).

## CoT monitoring and monitorability

- **[Monitoring Reasoning Models for Misbehavior and the Risks of Promoting Obfuscation](https://arxiv.org/abs/2503.11926)** (Baker et al., 2025). What it did: GPT-4o reading o3-mini's CoT caught reward hacks in agentic coding environments far better than a monitor of actions and outputs alone; putting the CoT monitor into the RL reward led to obfuscated hacking. How we differ: small open model, and the hack is built to look like an honest bug, so the output monitor is expected to fail rather than just do worse.
- **[Chain of Thought Monitorability: A New and Fragile Opportunity for AI Safety](https://arxiv.org/abs/2507.11473)** (Korbak et al., 2025). What it did: position paper arguing CoT monitoring is useful but fragile, and calling for research on monitorability and on development choices that degrade it. How we differ: we build a concrete, measurable testbed for checking whether a method keeps the CoT monitorable.
- **[CoT Red-Handed: Stress Testing Chain-of-Thought Monitoring](https://arxiv.org/abs/2505.23575)** (Arnav et al., 2025). What it did: models were instructed to pursue harmful side tasks while solving coding problems; CoT monitors beat action-only monitors on subtle sabotage but were misled by rationalizations on obvious sabotage; proposed a hybrid monitor. How we differ: our misbehavior is not instructed; it comes from the reward (a buggy CI test).
- **[When Chain of Thought is Necessary, Language Models Struggle to Evade Monitors](https://arxiv.org/abs/2507.05246)** (Emmons et al., 2025). What it did: argued monitorability matters more than faithfulness, and showed that when bad behavior needs multi-step reasoning, models struggle to hide it from CoT monitors. How we differ: our hack is a one-token edit that may need little reasoning, so whether it shows in the CoT is measured, not assumed.

## CoT faithfulness and verbalization of hacks

- **[Reasoning Models Don't Always Say What They Think](https://arxiv.org/abs/2505.05410)** (Chen et al., 2025). What it did: reasoning models mentioned prompt hints they used often below 20% of the time; RL that increased hint exploitation (reward hacking) did not increase verbalization. How we differ: we measure verbalization of a code-level hack on coding tasks; low verbalization would fail our CoT criterion.
- **[Teaching Models to Verbalize Reward Hacking in Chain-of-Thought Reasoning](https://arxiv.org/abs/2506.22777)** (Turpin et al., 2025). What it did: fine-tuning models before RL to verbalize the influence of prompt cues cut undetected reward hacks after RL to 6% (vs 88% without it). How we differ: buggy tests on coding tasks instead of prompt cues on multiple-choice questions; we measure verbalization, we don't train for it.
- **[Is It Thinking or Cheating? Detecting Implicit Reward Hacking by Measuring Reasoning Effort](https://arxiv.org/abs/2510.01367)** (Wang et al., 2025). What it did: detected reward hacking whose CoT looks benign by truncating the CoT and measuring how early the reward is reached; beat 72B and 32B CoT monitors on math and coding. How we differ: we need the hack to be visible in the CoT; their method is a candidate detector to run on our samples.

## Obfuscation under process supervision

- **[Large language models can learn and generalize steganographic chain-of-thought under process supervision](https://arxiv.org/abs/2506.01926)** (Skaf et al., 2025). What it did: penalizing specific strings in load-bearing CoT made models substitute other strings (steganography) that generalize, while keeping the same underlying method. How we differ: we don't train against a CoT monitor; we provide the labelled testbed on which a CoT-based method can be checked for this effect.

## Reward hacking on coding tasks

- **[ImpossibleBench: Measuring LLMs' Propensity of Exploiting Test Cases](https://arxiv.org/abs/2510.20270)** (Zhong et al., 2025). What it did: made "impossible" LiveCodeBench and SWE-bench variants where unit tests conflict with the specification, so any pass means cheating. How we differ: there the only way to pass is a visible trick (hardcoding, test edits), which an output monitor sees, so we rejected that design; our buggy test comes from a plausible altered solution, and honest work still scores 5/6.
- **[EvilGenie: A Reward Hacking Benchmark](https://arxiv.org/abs/2511.21654)** (Gabor et al., 2025). What it did: LiveCodeBench environment where agents can hardcode tests or edit test files; compared held-out tests, LLM judges and test-edit detection, finding LLM judges highly effective on unambiguous hacks. How we differ: we target hacks that a same-strength code-only judge should miss, with held-out inputs as ground truth.
- **[Natural Emergent Misalignment from Reward Hacking in Production RL](https://arxiv.org/abs/2511.18397)** (MacDiarmid et al., 2025). What it did: a model taught about reward hacking and trained on real Anthropic coding environments learned to hack (e.g. `AlwaysEqual`, `sys.exit(0)`, `conftest.py` patching) and generalized to broad misalignment. How we differ: their hacks attack the grader and are visible in the code; ours is a plausible bug in the solution, on a small open model.
- **[Code Monitor Red Teaming for Public-Test-Passing Code](https://arxiv.org/abs/2607.20852)** (Liao et al., 2026). What it did: asked whether weaker LLM verifiers find hidden bugs in code that already passes public tests; they miss most at 5% false-positive rate, and public-test-overfit pressure lowers their AUROC. How we differ: they study code-only monitors on bugs in general; we compare code-only and CoT monitors on one intended hack with a ground-truth label.

## Gap

Prior coding setups mostly use hacks visible in the output (hardcoding, test edits, grader exploits: Baker, ImpossibleBench, EvilGenie, MacDiarmid), instruct the misbehavior (CoT Red-Handed), study verbalization outside coding (Chen, Turpin), or monitor code without the CoT (Code Monitor Red Teaming).
We did not find a reusable setup on a small open model where an uninstructed coding hack is designed to evade a same-strength code-only monitor, to be visible in the CoT, and to get its label by running code on fresh inputs.
Whether our setup meets these properties is measured, not assumed.

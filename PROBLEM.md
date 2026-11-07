# Model organism of sneaky reward hacking

Currently, AFAIK, all monitoring is either just looking at the outputs (or interpretability). Yet we expect in the future models capable of evading output monitors.

My lab is trying to build methods to monitor/align models which rely on CoT but without inducing pressure for CoT obfuscation. The idea is that they are better at scaling to future capabilities, unlike the current methods which rely on looking at the output.

To test these methods we need a model organism of sneaky reward hacking.

AFAIK there is no such model organism out there and building it would be helpful for any researchers who wants to study monitoring mechanisms and for showcasing the weakness of current approach to monitorability.



Properties of the model organism we want:
- The behavior is reward hacking on coding tasks. This restriction in setup is needed to make the setup realistic and relatable.
  - In particular, it must read as a realistic setup. Genuine behavior should still be rewarded and be an option to complete the task. But it may be not the optimal way to get the reward, hence leaving space for reward hacking to occur.
- Using small open models (so we can use later use whitebox methods on them)
- Not detectable by just looking at the output (at least by the monitor of the same strength as the open model). For example the canonical 'hardcode the tests' setup would not pass here.
- Detectable in CoT (so we can see if new methods induce obfuscation or not)
- Hacking is measurable (It is possible to detect if hacking occurred to determine the Ground Truth)
Ideally:
- The behavior is emergent from the reward structure of the setup, not achieved via a prompt which instructs the model to hack in a particular way. But this is optional. Do not get blocked on this.

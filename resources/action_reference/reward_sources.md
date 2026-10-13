# Reward-design references

Verified 2026-10-12.

- Fetch environment implementation (local copy: fetch_env.py): https://github.com/Farama-Foundation/Gymnasium-Robotics/blob/main/gymnasium_robotics/envs/fetch/fetch_env.py . compute_reward uses Euclidean goal distance. Sparse reward is -1 outside the threshold and 0 inside; dense reward is negative distance. This is Fetch's convention, not LIBERO's.
- Christiano et al., Deep Reinforcement Learning from Human Preferences (2017): https://arxiv.org/abs/1706.03741 . Abstract describes specifying goals through human preferences between trajectory segments. This supports preference-based reward learning as an alternative to manually specifying a numeric reward rule.
- OpenAI Spinning Up reward/return definitions: https://github.com/openai/spinningup/blob/master/docs/spinningup/rl_intro.rst . A local reference copy is spinningup_rl_intro.rst.

Distance/progress, success bonuses, and penalties in the teaching response are examples, not a recommendation for a real robot's complete reward function. A finite-task success condition and safety requirements must be defined separately.

import time
import gymnasium as gym
from pathlib import Path
import mujoco.viewer
from stable_baselines3 import SAC
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.evaluation import evaluate_policy
from ur5_sac_train import UR5ReachEnv
# model = SAC.load(
#     "/home/mia/data/openvla-data/output/"
#     "sac_inverted_pendulum/20261016_112037/sac_model.zip",
#     device="cpu",
# )

# eval_env = Monitor(
#     gym.make(
#         "InvertedPendulum-v5",
#         render_mode="human",
#         # 打开窗口渲染
#     )
# )
model = SAC.load(
    "/home/mia/data/openvla-data/output/"
    "sac_ur5_reach_parallel/20261018_182042_008778/"
    "best/best_model.zip",
    device="cpu",
)
xml_path = (
    Path(__file__).resolve().parent.parent
    / "models"
    / "ur5e.xml"
)

env = UR5ReachEnv(xml_path)

env.reset(seed=123)

# mean_reward, std_reward = evaluate_policy(
#     model,
#     eval_env,
#     n_eval_episodes=10,
#     deterministic=True,
# )

# print(f"平均回报：{mean_reward:.2f}")
# print(f"回报标准差：{std_reward:.2f}")

# eval_env.close()
with mujoco.viewer.launch_passive(
    env.model,
    env.data,
) as viewer:

    for episode in range(10):
        if not viewer.is_running():
            break

        with viewer.lock():
            obs, info = env.reset(
                seed=123 if episode == 0 else None,
                options={
                    "reset_noise": 0.1,  # 每个关节 ±0.02 rad，约 ±1.15°
                },
            )
        viewer.sync()
        episode_return = 0.0
        episode_steps = 0

        while viewer.is_running():
            wall_start = time.perf_counter()

            # 只推理，不训练
            action, _ = model.predict(
                obs,
                # 确定性推理
                deterministic=True,
            )

            with viewer.lock():
                obs, reward, terminated, truncated, info = (
                    env.step(action)
                )

            episode_return += reward
            episode_steps += 1

            # 把最新仿真状态同步到窗口
            viewer.sync()

            # 按接近真实时间的节奏播放
            step_duration = (
                env.control_cycles * env.control_dt
            )
            remaining = (
                step_duration
                - (time.perf_counter() - wall_start)
            )
            if remaining > 0:
                time.sleep(remaining)

            if terminated or truncated:
                print(
                    f"回合 {episode + 1}："
                    f"步数={episode_steps}，"
                    f"回报={episode_return:.2f}，"
                    f"成功={info['is_success']}，"
                    f"截断={truncated}，"
                    f"位置误差={info['position_error']:.4f} m，"
                    f"姿态误差={info['rotation_error']:.4f} rad"
                )
                break


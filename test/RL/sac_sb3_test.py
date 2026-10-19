import gymnasium as gym
import time
import numpy as np
import matplotlib.pyplot as plt
from stable_baselines3 import SAC
from stable_baselines3.common.monitor import Monitor
from pathlib import Path
from datetime import datetime
from stable_baselines3.common.logger import configure
run_dir = (
    Path(__file__).resolve().parents[2]
    / "output"
    / "sac_inverted_pendulum"
    / datetime.now().strftime("%Y%m%d_%H%M%S")
)
env = Monitor(gym.make("InvertedPendulum-v5"),
               filename=str(run_dir / "episodes"),)

model = SAC(
    "MlpPolicy",
    env,
    verbose=1,
    device="cuda",
    seed=42,
    buffer_size=10_000,
)
model.set_logger(
    configure(str(run_dir), ["stdout", "csv"])
)
run_dir.mkdir(parents=True, exist_ok=True)
start_time = time.perf_counter()
model.learn(total_timesteps=1_000)
elapsed = time.perf_counter() - start_time
print("训练完成，实际交互步数：", model.num_timesteps)
print(f"训练耗时：{elapsed:.2f} 秒")

env.close()
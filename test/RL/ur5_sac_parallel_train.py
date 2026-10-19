"""双进程 UR5 + SAC：并行采样，共享一个策略和经验池。"""

import argparse
import csv
from datetime import datetime
import json
from pathlib import Path
import time

import matplotlib

matplotlib.use("Agg")  # 训练只保存图，不打开窗口。
import matplotlib.pyplot as plt
import numpy as np
import torch
from stable_baselines3 import SAC
from stable_baselines3.common.callbacks import EvalCallback
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.logger import configure
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv, SubprocVecEnv

from ur5_sac_train import UR5ReachEnv


# 常用参数集中在这里；也可以用命令行参数临时覆盖。
N_ENVS = 4
TOTAL_TIMESTEPS = 200_000  # 所有环境累计，而非每个环境各运行这么多步。
BUFFER_SIZE = 100_000     # 所有训练环境共享的经验池容量。
LEARNING_RATE = 3e-4
TRAIN_RESET_NOISE = 0.1
EVAL_RESET_NOISE = 0.02   # 保留已有的近 home 评估设计。
EVAL_EVERY_TIMESTEPS = 2_000
N_EVAL_EPISODES = 5
SEED = 78
TORCH_THREADS = 1         # 限制主进程网络计算线程，避免 CPU 过度竞争。


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n-envs", type=int, default=N_ENVS)
    parser.add_argument("--total-timesteps", type=int, default=TOTAL_TIMESTEPS)
    parser.add_argument("--buffer-size", type=int, default=BUFFER_SIZE)
    parser.add_argument("--learning-rate", type=float, default=LEARNING_RATE)
    parser.add_argument("--train-reset-noise", type=float, default=TRAIN_RESET_NOISE)
    parser.add_argument("--eval-reset-noise", type=float, default=EVAL_RESET_NOISE)
    parser.add_argument("--eval-every", type=int, default=EVAL_EVERY_TIMESTEPS)
    parser.add_argument("--n-eval-episodes", type=int, default=N_EVAL_EPISODES)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--torch-threads", type=int, default=TORCH_THREADS)
    args = parser.parse_args()
    for field in ["n_envs", "total_timesteps", "buffer_size", "eval_every", "n_eval_episodes", "torch_threads"]:
        if getattr(args, field) < 1:
            parser.error(f"{field} 必须至少为 1")
    if args.buffer_size < args.n_envs:
        parser.error("buffer_size 必须至少等于 n_envs")
    if not np.isfinite(args.learning_rate) or args.learning_rate <= 0:
        parser.error("learning_rate 必须是正的有限数")
    for field in ["train_reset_noise", "eval_reset_noise"]:
        if not np.isfinite(getattr(args, field)) or getattr(args, field) < 0:
            parser.error(f"{field} 必须是非负有限数")
    return args


def save_curves(run_dir):
    # make_vec_env 已为各进程分别创建 Monitor；按完成时间合并日志。
    episodes = []
    for path in sorted((run_dir / "train").glob("*.monitor.csv")):
        with path.open(encoding="utf-8") as stream:
            metadata = json.loads(stream.readline().lstrip("#"))
            for row in csv.DictReader(stream):
                episodes.append((float(metadata["t_start"]) + float(row["t"]), float(row["r"])))
    episodes.sort(key=lambda item: item[0])
    fig, axes = plt.subplots(3, 1, figsize=(9, 10))
    rewards = np.asarray([reward for _, reward in episodes], dtype=float)
    if len(rewards):
        x = np.arange(1, len(rewards) + 1)
        axes[0].plot(x, rewards, alpha=0.3, label="Episode return")
        if len(rewards) >= 20:
            smooth = np.convolve(rewards, np.ones(20) / 20, mode="valid")
            axes[0].plot(x[19:], smooth, label="20-episode moving average")
        axes[0].legend()
    else:
        axes[0].text(0.5, 0.5, "No completed training episodes", ha="center")
    axes[0].set(xlabel="Completed episode order across workers", ylabel="Training return")
    path = run_dir / "eval" / "evaluations.npz"
    if path.exists():
        with np.load(path) as data:
            axes[1].plot(data["timesteps"], data["results"].mean(axis=1), marker=".")
            if "successes" in data:
                axes[2].plot(data["timesteps"], data["successes"].mean(axis=1), marker=".")
    axes[1].set(xlabel="Total training transitions", ylabel="Mean evaluation return")
    axes[2].set(xlabel="Total training transitions", ylabel="Evaluation success rate", ylim=(-0.05, 1.05))
    fig.tight_layout()
    fig.savefig(run_dir / "return_curve.png", dpi=150)
    plt.close(fig)


def main():
    args = parse_args()
    torch.set_num_threads(args.torch_threads)
    root = Path(__file__).resolve().parents[2]
    xml_path = root / "test" / "models" / "ur5e.xml"
    run_dir = root / "output" / "sac_ur5_reach_parallel" / datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    run_dir.mkdir(parents=True, exist_ok=True)

    # callback 每次批量 step 被调用一次，因此要除以训练环境数量。
    eval_freq = max(args.eval_every // args.n_envs, 1)
    config = vars(args).copy()
    config.update(train_freq=1, gradient_steps=-1, learning_starts=100,
                  batch_size=256, eval_seed=123, eval_deterministic=True,
                  start_method="spawn", actual_eval_every=eval_freq * args.n_envs)
    (run_dir / "config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    print("实验输出目录：", run_dir, flush=True)
    print(f"环境数={args.n_envs}，总交互预算={args.total_timesteps}，经验池容量={args.buffer_size}", flush=True)
    print(f"每批收集 {args.n_envs} 条经验，预热后每批执行 {args.n_envs} 次梯度更新", flush=True)

    train_env = eval_env = None
    try:
        train_env = make_vec_env(
            UR5ReachEnv,
            n_envs=args.n_envs,
            seed=args.seed,
            env_kwargs={"xml_path": xml_path, "reset_noise": args.train_reset_noise},
            monitor_dir=str(run_dir / "train"),
            monitor_kwargs={"info_keywords": ("is_success", "position_error", "rotation_error")},
            vec_env_cls=SubprocVecEnv,
            vec_env_kwargs={"start_method": "spawn"},
        )
        # 独立评估环境；评估不需要子进程。未使用 VecNormalize，可用不同 VecEnv 子类。
        eval_env = DummyVecEnv([lambda: Monitor(
            UR5ReachEnv(xml_path, reset_noise=args.eval_reset_noise),
            filename=str(run_dir / "eval_episodes"),
            info_keywords=("is_success", "position_error", "rotation_error"),
        )])
        eval_env.seed(123)  # 首次 reset 生效；后续自动 reset 继续随机数序列。
        model = SAC(
            "MlpPolicy", train_env,
            verbose=1, device=args.device, seed=args.seed,
            buffer_size=args.buffer_size, learning_rate=args.learning_rate,
            learning_starts=100, batch_size=256,
            train_freq=1,
            gradient_steps=-1,  # 每收集多少条转移，就做多少次梯度更新。
        )
        model.set_logger(configure(str(run_dir), ["stdout", "csv"]))
        callback = EvalCallback(
            eval_env,
            best_model_save_path=str(run_dir / "best"),
            log_path=str(run_dir / "eval"),
            eval_freq=eval_freq,
            n_eval_episodes=args.n_eval_episodes,
            deterministic=True, render=False, verbose=1,
        )
        start = time.perf_counter()
        model.learn(total_timesteps=args.total_timesteps, callback=callback)
        elapsed = time.perf_counter() - start
        model.save(run_dir / "sac_model")
        summary = {
            "actual_timesteps": model.num_timesteps,
            "gradient_updates": model._n_updates,
            "learn_elapsed_seconds": elapsed,
            "transitions_per_second_including_evaluation": model.num_timesteps / elapsed,
        }
        (run_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    finally:
        if train_env is not None:
            train_env.close()
        if eval_env is not None:
            eval_env.close()
    save_curves(run_dir)
    print("训练结束：", summary)
    print("最佳模型：", run_dir / "best" / "best_model.zip")
    print("最终模型：", run_dir / "sac_model.zip")


if __name__ == "__main__":
    main()

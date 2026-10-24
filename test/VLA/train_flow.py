"""独立训练练习：本地 LIBERO state(8) -> 小 MLP + LoRA -> action(7)。

不是 OpenVLA 微调；随机初始化的教学底座，不代表预训练机器人策略。
只使用本地数据与现有依赖，不下载模型。入口及用法见 train_flow_README.md。
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from itertools import islice
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
os.environ.setdefault("HF_HOME", str(ROOT / "output/train_flow/hf_cache"))
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")

import numpy as np
import torch
from peft import LoraConfig, get_peft_model
from torch import nn
from torch.nn import functional as F
from torch.utils.data import DataLoader, TensorDataset


# ① 数据：先取一个很小的真实 RLDS 子集，再交给 PyTorch DataLoader。
def read_rlds(data_dir: Path, max_samples: int):
    import tensorflow as tf
    import tensorflow_datasets as tfds

    # TensorFlow 只负责读数据，不让它占用 PyTorch 训练需要的显存。
    tf.config.set_visible_devices([], "GPU")
    tf.config.threading.set_inter_op_parallelism_threads(1)
    tf.config.threading.set_intra_op_parallelism_threads(1)
    shards = sorted(data_dir.glob("*.tfrecord-*"))
    if not shards:
        raise ValueError(f"没有找到 TFRecord 分片：{data_dir}")
    for shard in shards:
        with shard.open("rb") as stream:
            if stream.read(64).startswith(b"version https://git-lfs.github.com/spec/v1"):
                raise ValueError(f"这是 Git LFS 指针，不是真实数据：{shard}")
    options = tf.data.Options()
    options.threading.private_threadpool_size = 1
    options.threading.max_intra_op_parallelism = 1
    config = tfds.ReadConfig(
        options=options, interleave_cycle_length=1,
        num_parallel_calls_for_decode=1, num_parallel_calls_for_interleave_files=1,
        skip_prefetch=True,
    )
    builder = tfds.builder_from_directory(str(data_dir))
    episodes = builder.as_dataset(
        split="train", shuffle_files=False, read_config=config,
        decoders={"steps": {"observation": {
            "image": tfds.decode.SkipDecoding(),
            "wrist_image": tfds.decode.SkipDecoding(),
        }}},
    )
    states, actions = [], []
    visited_episodes = skipped_last = 0
    for episode in episodes:
        visited_episodes += 1
        # 只把两个数值向量及结束标记传回 Python，不保留图像。
        numeric_steps = episode["steps"].map(lambda s: {
            "state": s["observation"]["state"],
            "action": s["action"], "is_last": s["is_last"],
        }).with_options(options)
        for step in tfds.as_numpy(numeric_steps):
            # 保守地排除末帧：本练习不使用可能无有效 action 的结束观测。
            if bool(step["is_last"]):
                skipped_last += 1
                continue
            x = np.asarray(step["state"], dtype=np.float32)
            y = np.asarray(step["action"], dtype=np.float32)
            if x.shape != (8,) or y.shape != (7,):
                raise ValueError(f"数据 shape 不匹配：state={x.shape}, action={y.shape}")
            if not (np.isfinite(x).all() and np.isfinite(y).all()):
                raise ValueError("数据包含 NaN 或 Inf")
            states.append(x)
            actions.append(y)
            if len(states) == max_samples:
                break
        if len(states) == max_samples:
            break
    if len(states) < 2:
        raise ValueError("有效训练样本不足")
    return {
        "states": torch.from_numpy(np.stack(states)),
        "actions": torch.from_numpy(np.stack(actions)),
        "source": str(data_dir), "max_samples": max_samples,
        "visited_episodes": visited_episodes, "skipped_last": skipped_last,
    }


# ② 模型加载：教学底座是小 MLP，不是下载的预训练 VLA。
class TinyPolicy(nn.Module):
    def __init__(self):
        super().__init__()
        self.register_buffer("state_mean", torch.zeros(8))
        self.register_buffer("state_std", torch.ones(8))
        self.fc1 = nn.Linear(8, 128)
        self.fc2 = nn.Linear(128, 128)
        self.head = nn.Linear(128, 7)

    def forward(self, state):
        x = (state - self.state_mean) / self.state_std
        return self.head(F.relu(self.fc2(F.relu(self.fc1(x)))))


def attach_lora(base):
    # ③ LoRA：PEFT 冻结原始权重，仅训练这三个 Linear 层的低秩增量。
    return get_peft_model(base, LoraConfig(
        r=4, lora_alpha=8, lora_dropout=0.0, bias="none",
        target_modules=["fc1", "fc2", "head"],
    ))


def train_one_epoch(model, loader, optimizer, scaler, device, accum_steps, amp):
    """核心训练循环；支持最后一组不足 accum_steps / 最后一个 batch 不足额。"""
    model.train()
    trainable = [p for p in model.parameters() if p.requires_grad]
    iterator = iter(loader)
    loss_sum = samples = micro_steps = updates = skipped_updates = 0
    optimizer.zero_grad(set_to_none=True)
    while True:
        # 预取这一组 CPU 小 batch，只用于确定实际样本总数，不保留多份 GPU 图。
        group = list(islice(iterator, accum_steps))
        if not group:
            break
        group_samples = sum(len(state) for state, _ in group)
        for state, action in group:
            state, action = state.to(device), action.to(device)
            # ④ autocast：CUDA 使用 FP16；CPU 路径禁用 AMP。
            with torch.autocast(device_type=device.type, dtype=torch.float16, enabled=amp):
                prediction = model(state)
                # ⑤ loss：原始动作的 MSE，用 float32 计算。
                raw_loss = F.mse_loss(prediction.float(), action)
                # ⑥ 等长满额小 batch 时，这等于 raw_loss / accum_steps。
                # 按样本加权也能正确处理尾组和不足额小 batch。
                loss = raw_loss * (len(state) / group_samples)
            if not torch.isfinite(raw_loss):
                raise RuntimeError("loss 非有限数，停止训练")
            scaler.scale(loss).backward()  # 梯度累积；这里不 step、不清空梯度。
            loss_sum += raw_loss.detach().item() * len(state)
            samples += len(state)
            micro_steps += 1
        # 整组完成后才更新参数；先解除 scale，再裁剪梯度。
        scaler.unscale_(optimizer)
        torch.nn.utils.clip_grad_norm_(trainable, max_norm=1.0)
        previous_scale = scaler.get_scale()
        scaler.step(optimizer)
        scaler.update()
        if scaler.get_scale() < previous_scale:
            skipped_updates += 1  # AMP 遇到溢出时会跳过本次更新。
        else:
            updates += 1
        optimizer.zero_grad(set_to_none=True)
    return dict(train_mse=loss_sum / samples, micro_steps=micro_steps,
                optimizer_updates=updates, skipped_updates=skipped_updates)


@torch.no_grad()
def evaluate(model, dataset, device):
    """同一个教学子集上的 FP32 拟合误差，不是验证集/机器人成功率。"""
    model.eval()
    total = 0.0
    for state, action in DataLoader(dataset, batch_size=64):
        total += F.mse_loss(model(state.to(device)), action.to(device), reduction="sum").item()
    return total / (len(dataset) * 7)


def verify_accumulation(model, dataset):
    """FP32 下比较两次大 batch 更新 vs 梯度累积；覆盖不均匀 batch 和尾组。"""
    big, small = copy.deepcopy(model).cpu(), copy.deepcopy(model).cpu()
    count = min(35, len(dataset))
    x, y = (tensor[:count] for tensor in dataset.tensors)
    # 35 个样本：首组 8+8+8+8，尾组 3；更小数据也可验证。
    batches = list(zip(x.split(8), y.split(8)))
    a = torch.optim.SGD([p for p in big.parameters() if p.requires_grad], lr=0.03)
    b = torch.optim.SGD([p for p in small.parameters() if p.requires_grad], lr=0.03)
    grad_error = 0.0
    for start in range(0, len(batches), 4):
        group = batches[start:start + 4]
        n = sum(len(s) for s, _ in group)
        a.zero_grad(set_to_none=True)
        b.zero_grad(set_to_none=True)
        F.mse_loss(big(torch.cat([s for s, _ in group])),
                   torch.cat([t for _, t in group])).backward()
        for s, t in group:
            (F.mse_loss(small(s), t) * len(s) / n).backward()
        for p, q in zip(big.parameters(), small.parameters()):
            if p.requires_grad:
                torch.testing.assert_close(p.grad, q.grad, atol=1e-6, rtol=1e-5)
                grad_error = max(grad_error, (p.grad - q.grad).abs().max().item())
        a.step()
        b.step()
    error = max((p - q).abs().max().item() for p, q in zip(big.parameters(), small.parameters()))
    if error > 1e-6:
        raise AssertionError(f"梯度累积等价性检查失败：{error}")
    return dict(samples=count, max_gradient_error=grad_error, max_parameter_error=error)


def save_checkpoint(path, model, optimizer, scaler, epoch, global_step, config, history):
    # ⑦ 只在 epoch 结束（梯度已清空）保存。full model 含底座、LoRA 和归一化 buffers。
    checkpoint = dict(
        model=model.state_dict(), optimizer=optimizer.state_dict(), scaler=scaler.state_dict(),
        completed_epochs=epoch, global_step=global_step, config=config, history=history,
        torch_rng=torch.get_rng_state(),
        cuda_rng=torch.cuda.get_rng_state() if next(model.parameters()).is_cuda else None,
    )
    temp = path.with_suffix(".tmp")
    torch.save(checkpoint, temp)
    temp.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path(
        "/home/mia/datasets/Libero_RLDS/libero_spatial_no_noops/1.0.0"))
    parser.add_argument("--output-dir", type=Path, default=ROOT / "output/train_flow/run1")
    parser.add_argument("--max-samples", type=int, default=257)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--accum-steps", type=int, default=4)
    parser.add_argument("--epochs", type=int, default=5, help="总 epoch 数，而非恢复后额外的数量")
    parser.add_argument("--lr", type=float, default=0.003)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--no-amp", action="store_true")
    parser.add_argument("--resume", action="store_true", help="恢复 output-dir/latest.pt")
    args = parser.parse_args()
    if min(args.max_samples, args.batch_size, args.accum_steps, args.epochs) < 1 or args.lr <= 0:
        parser.error("样本数、batch、累积步数、epochs 和 lr 必须为正")
    torch.set_num_threads(1)
    torch.manual_seed(args.seed)
    device = torch.device(("cuda" if torch.cuda.is_available() else "cpu")
                          if args.device == "auto" else args.device)
    if device.type == "cuda" and not torch.cuda.is_available():
        parser.error("CUDA 不可用；请检查 GPU 权限/环境，或使用 --device cpu")
    amp = device.type == "cuda" and not args.no_amp
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    latest = out / "latest.pt"
    if latest.exists() and not args.resume:
        parser.error("已有 checkpoint；请用 --resume，或指定新的 --output-dir")
    if args.resume and not latest.exists():
        parser.error("未找到要恢复的 latest.pt")

    # 本脚本只加载自己生成的可信 .pt 文件，不加载陌生来源的 pickle checkpoint。
    cache = out / "samples.pt"
    if cache.exists():
        data = torch.load(cache, map_location="cpu", weights_only=True)
        if data["source"] != str(args.data_dir.resolve()) or data["max_samples"] != args.max_samples:
            parser.error("子集缓存与参数不同；请使用新的 --output-dir")
    else:
        data = read_rlds(args.data_dir.resolve(), args.max_samples)
        torch.save(data, cache)
    x, y = data["states"], data["actions"]
    dataset = TensorDataset(x, y)
    fingerprint = hashlib.sha256(x.numpy().tobytes() + y.numpy().tobytes()).hexdigest()
    print(f"Data: {data['source']}\nSamples={len(dataset)}, visited_episodes={data['visited_episodes']}, "
          f"skipped_last={data['skipped_last']}", flush=True)

    base_path = out / "base_model.pt"
    if not args.resume:
        base = TinyPolicy()
        base.state_mean.copy_(x.mean(0))
        base.state_std.copy_(x.std(0, unbiased=False).clamp_min(0.01))
        torch.save(base.state_dict(), base_path)
    base = TinyPolicy()
    base.load_state_dict(torch.load(base_path, map_location="cpu", weights_only=True))
    model = attach_lora(base)
    model.print_trainable_parameters()
    equivalence = verify_accumulation(model, dataset)
    print(f"FP32 accumulation check: {equivalence}", flush=True)
    model.to(device)
    trainable = [p for p in model.parameters() if p.requires_grad]
    optimizer = torch.optim.AdamW(trainable, lr=args.lr)
    scaler = torch.cuda.amp.GradScaler(enabled=amp)
    config = dict(batch_size=args.batch_size, accum_steps=args.accum_steps, lr=args.lr,
                  seed=args.seed, device=device.type, amp=amp, dataset_sha256=fingerprint)
    start_epoch = global_step = 0
    history = []
    if args.resume:
        checkpoint = torch.load(latest, map_location="cpu", weights_only=True)
        if checkpoint["config"] != config:
            parser.error("恢复参数/数据不匹配；保持 batch、accum、lr、seed、device 和 AMP 不变")
        model.load_state_dict(checkpoint["model"])
        optimizer.load_state_dict(checkpoint["optimizer"])
        scaler.load_state_dict(checkpoint["scaler"])
        start_epoch, global_step = checkpoint["completed_epochs"], checkpoint["global_step"]
        history = checkpoint["history"]
        torch.set_rng_state(checkpoint["torch_rng"])
        if device.type == "cuda":
            torch.cuda.set_rng_state(checkpoint["cuda_rng"])
        print(f"Resumed: epoch={start_epoch}, optimizer_step={global_step}", flush=True)
    if args.epochs <= start_epoch:
        parser.error("--epochs 必须大于 checkpoint 已完成的 epoch 数")
    frozen_before = {n: p.detach().clone() for n, p in model.named_parameters() if not p.requires_grad}
    adapter_before = {n: p.detach().clone() for n, p in model.named_parameters() if p.requires_grad}
    initial_mse = evaluate(model, dataset, device)
    print(f"Device={device}, AMP={amp}, effective full batch={args.batch_size * args.accum_steps}; "
          f"initial_fit_mse={initial_mse:.6f}", flush=True)
    for epoch in range(start_epoch, args.epochs):
        # 每个 epoch 的洗牌只依赖 seed+epoch，因此可在 epoch 边界恢复。
        loader = DataLoader(dataset, batch_size=args.batch_size, shuffle=True, num_workers=0,
                            generator=torch.Generator().manual_seed(args.seed + epoch))
        stats = train_one_epoch(model, loader, optimizer, scaler, device, args.accum_steps, amp)
        global_step += stats["optimizer_updates"]
        stats.update(epoch=epoch + 1, global_step=global_step,
                     fit_mse_fp32=evaluate(model, dataset, device))
        history.append(stats)
        save_checkpoint(latest, model, optimizer, scaler, epoch + 1, global_step, config, history)
        print(json.dumps(stats), flush=True)
    for name, p in model.named_parameters():
        if name in frozen_before and not torch.equal(p, frozen_before[name]):
            raise AssertionError(f"底座不应改变：{name}")
    delta = max((p - adapter_before[n]).abs().max().item()
                for n, p in model.named_parameters() if p.requires_grad)
    if delta == 0:
        raise AssertionError("LoRA 参数没有更新")
    # adapter 仅用于模型分发；训练恢复必须使用含优化器和 scaler 的 latest.pt。
    model.save_pretrained(out / "adapter", save_embedding_layers=False)
    report = dict(config=config, device_name=torch.cuda.get_device_name() if device.type == "cuda" else "cpu",
                  samples=len(dataset), visited_episodes=data["visited_episodes"],
                  accumulation_check=equivalence, frozen_base_unchanged=True,
                  adapter_max_change=delta, initial_fit_mse=initial_mse, history=history)
    (out / "run_summary.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"Saved: {latest}\nFrozen base unchanged; LoRA max change={delta:.6f}", flush=True)


if __name__ == "__main__":
    main()

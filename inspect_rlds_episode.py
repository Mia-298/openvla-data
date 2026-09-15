"""第三周 Day2：检查本地 LIBERO RLDS 中的一条完整 episode。

运行示例（data-dir 必须指向包含 dataset_info.json 的版本目录）：
    /tmp/rlds-inspect/bin/python inspect_rlds_episode.py \
        --data-dir ~/datasets/Libero_RLDS/libero_spatial_no_noops/1.0.0

已验证环境：tensorflow-cpu==2.15.1、tensorflow-datasets==4.9.4、
tensorflow-metadata==1.15.0、protobuf==3.20.3。
索引从 0 开始；按 TFDS 固定读取顺序选择，不代表原始演示编号。
统计原始 action，包括最后一步；不做 OpenVLA 归一化或过滤。
退出码：0 检查通过，1 发现样本异常，2 参数或读取错误。
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

import numpy as np
import tensorflow as tf
import tensorflow_datasets as tfds


def flatten_fields(fields, prefix=""):
    """展开嵌套 observation，保留可读的字段路径。"""
    for name, value in fields.items():
        path = f"{prefix}.{name}" if prefix else name
        if isinstance(value, dict):
            yield from flatten_fields(value, path)
        else:
            yield path, value


def inspect_episode(episode):
    specs = dict(flatten_fields(episode["steps"].element_spec))
    field_stats = {
        name: {"shape": spec.shape.as_list(), "dtype": spec.dtype.name,
               "nan_count": 0, "inf_count": 0}
        for name, spec in specs.items()
    }
    flags = {name: [] for name in ("is_first", "is_last", "is_terminal")}
    actions, instructions, issues = [], set(), []
    endpoints = {}
    total_steps = 0

    # 流式遍历所有 step，只保留动作向量，不把整条轨迹的图像堆入内存。
    for index, step in enumerate(tfds.as_numpy(episode["steps"])):
        total_steps += 1
        for name, value in flatten_fields(step):
            value = np.asarray(value)
            spec = specs[name]
            dtype_ok = (value.dtype.kind in "OSU" if spec.dtype == tf.string
                        else value.dtype == np.dtype(spec.dtype.as_numpy_dtype))
            if not spec.shape.is_compatible_with(value.shape) or not dtype_ok:
                issues.append(f"step {index}: {name} shape/dtype 与 schema 不符")
            if np.issubdtype(value.dtype, np.inexact):
                field_stats[name]["nan_count"] += int(np.isnan(value).sum())
                field_stats[name]["inf_count"] += int(np.isinf(value).sum())

        for name in flags:
            if bool(step[name]):
                flags[name].append(index)
        boundary = {name: bool(step[name]) for name in flags}
        boundary.update(index=index, reward=float(step["reward"]),
                        discount=float(step["discount"]))
        if index == 0:
            endpoints["first_step"] = boundary
        endpoints["last_step"] = boundary
        actions.append(np.asarray(step["action"]))
        instructions.add(step["language_instruction"].decode("utf-8"))

    if total_steps == 0:
        issues.append("episode 为空")
    else:
        if flags["is_first"] != [0]:
            issues.append("is_first 必须且只能在 step 0 为 True")
        if flags["is_last"] != [total_steps - 1]:
            issues.append("is_last 必须且只能在最后一个 step 为 True")
        # is_last 表示轨迹结束；is_terminal 表示任务终止，截断轨迹可为 False。
        if any(index != total_steps - 1 for index in flags["is_terminal"]):
            issues.append("is_terminal 出现在非末尾 step")

    for name, stats in field_stats.items():
        if stats["nan_count"] or stats["inf_count"]:
            issues.append(f"{name} 含 NaN 或 Inf")

    action_stats = None
    if actions:
        if any(a.shape != (7,) or a.dtype != np.float32 for a in actions):
            issues.append("LIBERO action 应为 float32[7]")
        else:
            matrix = np.stack(actions)  # [episode 总步数, 7]
            ranges = []
            for dim in range(matrix.shape[1]):
                values = matrix[:, dim]
                finite = values[np.isfinite(values)]
                ranges.append({
                    "dimension": dim,
                    "min": float(finite.min()) if finite.size else None,
                    "max": float(finite.max()) if finite.size else None,
                })
            action_stats = {
                "shape": list(matrix.shape), "dtype": str(matrix.dtype),
                "range_per_dimension_finite_only": ranges,
                "values_outside_minus1_plus1": int(
                    (np.isfinite(matrix) & (np.abs(matrix) > 1)).sum()),
                "note": "原始动作的观测范围；[-1, 1] 仅作参考，越界不自动判为错误。",
            }

    return {
        "episode_metadata": {
            name: value.decode("utf-8") if isinstance(value, bytes)
            else np.asarray(value).tolist()
            for name, value in flatten_fields(tfds.as_numpy(episode["episode_metadata"]))
        },
        "language_instructions": sorted(instructions),
        "total_steps": total_steps,
        **endpoints,
        "flag_true_indices": flags,
        "fields_checked_against_schema_on_every_step": field_stats,
        "action": action_stats,
        "issues": issues,
        "passed": not issues,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--split", default="train", help="完整 split 名称，默认 train")
    parser.add_argument("--episode-index", type=int, default=0, help="从 0 开始，默认 0")
    parser.add_argument("--output", type=Path, help="可选：另存 JSON 样本报告")
    args = parser.parse_args()
    data_dir = args.data_dir.expanduser().resolve()
    if args.episode_index < 0:
        parser.error("--episode-index 不能为负数")
    if not all((data_dir / name).is_file() for name in ("dataset_info.json", "features.json")):
        parser.error("--data-dir 应指向包含 dataset_info.json 和 features.json 的版本目录")

    try:
        # 提前识别尚未下载的数据，避免 TFDS 抛出难理解的 DataLossError。
        for shard in data_dir.glob("*.tfrecord-*"):
            with shard.open("rb") as stream:
                if stream.read(64).startswith(b"version https://git-lfs.github.com/spec/v1"):
                    parser.error(f"{shard} 是 Git LFS 指针，请改用已完整下载的数据目录")
        builder = tfds.builder_from_directory(str(data_dir))
        if args.split not in builder.info.splits:
            parser.error(f"split 不存在，可选：{list(builder.info.splits)}")
        if args.episode_index >= builder.info.splits[args.split].num_examples:
            parser.error("--episode-index 超出该 split 的 episode 数量")
        episodes = builder.as_dataset(split=args.split, shuffle_files=False)
        episode = next(iter(episodes.skip(args.episode_index).take(1)))
        report = inspect_episode(episode)
        report = {"data_dir": str(data_dir), "split": args.split,
                  "episode_index": args.episode_index, **report}
        rendered = json.dumps(report, ensure_ascii=False, indent=2)
        print(rendered)
        if args.output:
            args.output.expanduser().write_text(rendered + "\n", encoding="utf-8")
        return 0 if report["passed"] else 1
    except (OSError, ValueError, StopIteration, tf.errors.OpError) as exc:
        parser.error(f"读取/输出失败：{exc}")


if __name__ == "__main__":
    raise SystemExit(main())

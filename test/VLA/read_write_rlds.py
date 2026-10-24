import os

import numpy as np

from libero.libero import benchmark, get_libero_path
from libero.libero.envs import OffScreenRenderEnv

from robosuite.utils import transform_utils as T
import tensorflow as tf
from pathlib import Path
import tensorflow_datasets as tfds
import time
import cv2

from robosuite.devices import Keyboard
from robosuite.utils.input_utils import input2action
# 将obs转换成rlds格式

def dist2list(dist):
    list=[]
    for key in sorted(dist.keys()):
        list.append(dist[key])
    return list
        
def extract_rlds_observation(obs):
    image = np.ascontiguousarray(
        obs["agentview_image"][::-1, ::-1]
    )

    wrist_image = np.ascontiguousarray(
        obs["robot0_eye_in_hand_image"][::-1, ::-1]
    )

    eef_position = obs["robot0_eef_pos"]
    eef_axis_angle = T.quat2axisangle(
        obs["robot0_eef_quat"]
    )
    gripper_position = obs["robot0_gripper_qpos"]

    state = np.concatenate(
        [
            eef_position,
            eef_axis_angle,
            gripper_position,
        ]
    ).astype(np.float32)

    joint_state = obs["robot0_joint_pos"].astype(
        np.float32
    )

    return {
        "image": image,
        "wrist_image": wrist_image,
        "state": state,
        "joint_state": joint_state,
    }
def collect_keyboard_trajectory(env, max_steps=1000):
    """采集一次键盘操作，返回轨迹、最后观测、结束原因。"""

    device = Keyboard(
        pos_sensitivity=1.0,
        rot_sensitivity=1.0,
    )

    trajectory = []
    status = "truncated"  # 达到步数限制，未必成功

    try:
        obs = env.reset()
        device.start_control()

        print("开始操作：W/A/S/D 移动，R/F 升降，空格开合夹爪，Q 放弃")

        for step_index in range(max_steps):
            loop_start = time.perf_counter()

            # ① 取得执行动作前的观测 obs_t
            observation_t = extract_rlds_observation(obs)

            # 显示相机画面
            frame = cv2.cvtColor(
                observation_t["image"],
                cv2.COLOR_RGB2BGR,
            )
            cv2.imshow("LIBERO keyboard collection", frame)
            cv2.waitKey(1)

            # ② 把键盘输入转换成 action_t
            action_t, _ = input2action(
                device=device,
                robot=env.robots[0],
                active_arm="right",
                env_configuration="single-arm-opposed",
            )

            # Q 会触发重置信号；这里把它解释为放弃本次采集
            if action_t is None:
                status = "aborted"
                break

            action_t = np.asarray(
                action_t,
                dtype=np.float32,
            )

            # ③ 执行动作，得到下一时刻观测
            next_obs, reward, done, info = env.step(action_t)

            # ④ 记录 obs_t 和 action_t，而不是 next_obs 和 action_t
            trajectory.append({
                "observation": observation_t,
                "action": action_t.copy(),
                "reward": np.float32(reward),
            })

            obs = next_obs

            # ⑤ 单独判断任务是否成功
            if env.check_success():
                status = "success"
                print("任务成功！")
                break

            if done:
                status = "env_done"
                print("环境结束，未检测到任务成功")
                break

            # 尽量按 20 Hz 的节奏操作；渲染慢时实际频率会更低
            elapsed = time.perf_counter() - loop_start
            time.sleep(max(0.0, 0.05 - elapsed))

        # 保留最终 obs，后面整理 RLDS 末尾数据时会用到
        return trajectory, obs, status

    finally:
        device.listener.stop()
        cv2.destroyAllWindows()
def save_episode(episodes, output_dir):
    output_dir = Path(output_dir)

    # 学习阶段避免误写进已有数据集，每次使用一个新目录
    if output_dir.exists():
        raise FileExistsError(
            f"目录已存在，请换一个新目录：{output_dir}"
        )

    # ① 定义保存结构：每个字段的类型、形状
    features = tfds.features.FeaturesDict({
        "steps": tfds.features.Dataset({
            "observation": {
                "image": tfds.features.Image(
                    shape=(256, 256, 3),
                    dtype=np.uint8,
                    encoding_format="png",
                ),
                "wrist_image": tfds.features.Image(
                    shape=(256, 256, 3),
                    dtype=np.uint8,
                    encoding_format="png",
                ),
                "state": tfds.features.Tensor(
                    shape=(8,),
                    dtype=np.float32,
                ),
                "joint_state": tfds.features.Tensor(
                    shape=(7,),
                    dtype=np.float32,
                ),
            },
            "action": tfds.features.Tensor(
                shape=(7,),
                dtype=np.float32,
            ),
            "reward": tfds.features.Scalar(dtype=np.float32),
            "discount": tfds.features.Scalar(dtype=np.float32),
            "is_first": tfds.features.Scalar(dtype=np.bool_),
            "is_last": tfds.features.Scalar(dtype=np.bool_),
            "is_terminal": tfds.features.Scalar(dtype=np.bool_),
            "language_instruction": tfds.features.Text(),
        }),
        "episode_metadata": {
            "file_path": tfds.features.Text(),
        },
    })

    # ② 定义数据集的名称、版本、存储目录
    identity = tfds.core.DatasetIdentity(
        name="my_libero_dataset",
        version=tfds.core.Version("1.0.0"),
        data_dir=str(output_dir),
        module_name="read_write_rlds",
    )

    info = tfds.core.DatasetInfo(
        builder=identity,
        features=features,
    )

    # ③ 创建目录和写入器
    output_dir.mkdir(parents=True)

    writer = tfds.core.SequentialWriter(
        ds_info=info,
        # 每个分片最多存 100 条 episode
        max_examples_per_shard=100,
        overwrite=False,
    )

    # train 是这个数据集中的一个划分
    writer.initialize_splits(["train"])

    # ④ 把整条 episode 写入 train
    try:
        writer.add_examples({
            
            "train": episodes,
        })
    finally:
        writer.close_all()

    return output_dir
def main():
    suite_name = "libero_spatial"
    task_id = 0
    
    benchmark_dict = benchmark.get_benchmark_dict()
    # 任务集合类
    task_suite_class = benchmark_dict[suite_name]
    # 创建任务集合对象 其中包含十个任务
    task_suite = task_suite_class(task_order_index=0)
    # 取得第 0 个任务的描述信息
    task = task_suite.get_task(task_id)
    # 取得第 0 个任务的场景信息
    bddl_file_path = task_suite.get_task_bddl_file_path(task_id)

    print("任务集合:", suite_name)
    print("任务数量:", task_suite.get_num_tasks())
    print("任务编号:", task_id)
    print("任务名称:", task.name)
    print("语言指令:", task.language)
    print("BDDL 文件:", bddl_file_path)
    print("BDDL 是否存在:", os.path.exists(bddl_file_path))
    env_args = {
        "bddl_file_name": bddl_file_path,
        "camera_heights": 256,
        "camera_widths": 256,
    }
    env = OffScreenRenderEnv(**env_args)
    try:
        env.seed(0)
        obs = env.reset()

        print("\n环境创建成功")
        print("obs 类型:", type(obs))
        print("obs 字段:")

        # for key, value in obs.items():
        #     value = np.asarray(value)
        #     print(
        #         f"  {key}: shape={value.shape}, dtype={value.dtype}"
        #     )
        # obs 字段:
        # 我们最终需要的是
        # image：agentview_image
        # RLDSBatchTransform里其实不会加载腕部相机，但是RLDS 格式里有
        # language：task.language
        # state：robot0_eef_pos，robot0_eef_quat（转为axis），robot0_gripper_qpos
        # RLDSBatchTransform里其实不会加载joint_state，但是RLDS 格式里有
        # joint_state：robot0_joint_pos
        # episode_steps = []
        # max_steps = 10
        # for step_index in range(max_steps):

        #     rlds_obs_t = extract_rlds_observation(obs)
        #     # 这里准备的是env的action，不是rlds的，目的是让环境前进一步（夹爪闭合）
        #     action_t = np.array(
        #         [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
        #         dtype=np.float32,
        #     )
        #     gripper_qpos_before = (
        #         obs["robot0_gripper_qpos"].copy()
        #     )

        #     next_obs, reward, done, info = env.step(
        #         action_t
        #     )
        #     gripper_qpos_after = (
        #         next_obs["robot0_gripper_qpos"].copy()
        #     )
        #     # 组成step：
        #     step_t = {
        #         # 执行动作之前的观测 obs_t
        #         "observation": rlds_obs_t,

        #         # 在 obs_t 状态下执行的动作 action_t
        #         "action": action_t.copy(),

        #         # LIBERO 环境返回的奖励
        #         "reward": np.float32(reward),

        #         # 当前先固定为 1.0
        #         "discount": np.float32(1.0),

        #         # 目前只采集了一个 step，所以它同时是第一个和最后一个
        #         "is_first": step_index == 0,
        #         "is_last": bool(done),

        #         # done 表示环境是否真正结束
        #         "is_terminal": bool(done),

        #         # 同一个 episode 的每一步都保存相同的语言指令
        #         "language_instruction": task.language,
        #     }
        #     episode_steps.append(step_t)
        #     obs = next_obs
        #     if done:
        #         break

        # episode_steps[-1]["is_last"] = True
        # # print(episode_steps)
        # episode = {
        #     "steps": episode_steps,
        #     "episode_metadata": {
        #         "file_path": "in_memory/test_episode_000",
        #     },
        # }
        # output_dir = save_episode(
        #     [episode,episode],
        #     "/home/mia/data/openvla-data/output/rlds_learning/my_libero_dataset/1.0.0",
        # )
        # 多条轨迹就episodes=[episode1,,,,]这样传入
        
        # print("保存位置：", output_dir)
        
        # 键盘采集轨迹
        trajectory, final_obs, status = collect_keyboard_trajectory(
            env,
            max_steps=1000,
        )
        print("采集步数:", len(trajectory))
        print("结束原因:", status)
        episode = {
            "steps": trajectory,
            "episode_metadata": {
                "file_path": "/home/mia/data/openvla-data/output/rlds_learning/my_libero_dataset/1.0.0",
            }
        }
        output_dir = save_episode(
            [episode],
            "/home/mia/data/openvla-data/output/rlds_learning/my_libero_dataset/1.0.0",
        )
        # 读取：
        builder = tfds.builder_from_directory(output_dir)
        dataset = builder.as_dataset(split="train", shuffle_files=False)
        episode = next(iter(dataset))
        steps = episode["steps"]
        step = next(iter(steps))
        print(step.keys())
        

    finally:
        env.close()


if __name__ == "__main__":
    main()


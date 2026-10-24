import os

import numpy as np

from libero.libero import benchmark, get_libero_path
from libero.libero.envs import OffScreenRenderEnv

from robosuite.utils import transform_utils as T

import h5py
# 将obs转换成rlds格式
def save_episode(episode, output_path):
    with h5py.File(output_path, 'w') as f:
        # group放层级结构（仅有key没有value）
        episode_group = f.create_group("episode")
        steps_group = episode_group.create_group("steps")
        metadata_group = episode_group.create_group("episode_metadata")
        metadata_group.create_dataset(
            "file_path",
            data=episode["episode_metadata"]["file_path"],
            dtype=h5py.string_dtype(encoding="utf-8"),
        )
        # observation 是嵌套字典，所以先创建 group
        for i , step in enumerate(episode["steps"]):
            step_group = steps_group.create_group(f"{i:06d}")
            
            observation_group = step_group.create_group("observation")
            for obs_key, obs_value in step["observation"].items():
                observation_group.create_dataset(obs_key, data=obs_value)
            for key, value in step.items():
                # dataset放字典结构
                if key == "observation":
                    continue
                # 检查字符串项
                if isinstance(value, str):
                    step_group.create_dataset(
                        key,
                        data=value,
                        dtype=h5py.string_dtype(encoding="utf-8"),
                    )
                else:
                    step_group.create_dataset(key, data=value)
def read_h5_item(item):
    # Group 类似文件夹：递归读取里面的每个成员
    if isinstance(item, h5py.Group):
        # 谁想的语法拖出去斩了
        # 先构建再遍历吗
        return {
            key: read_h5_item(value)
            for key, value in item.items()
        }

    # Dataset 是实际存储的数据
    value = item[()]

    # HDF5 字符串读出来有时是 bytes，解码成 Python 字符串
    if isinstance(value, bytes):
        return value.decode("utf-8")

    # NumPy 数组中的字符串也可能是 bytes
    if isinstance(value, np.ndarray) and value.dtype.kind == "S":
        return value.astype(str)

    return value
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
        episode_steps = []
        max_steps = 10
        for step_index in range(max_steps):

            rlds_obs_t = extract_rlds_observation(obs)
            # 这里准备的是env的action，不是rlds的，目的是让环境前进一步（夹爪闭合）
            action_t = np.array(
                [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
                dtype=np.float32,
            )
            gripper_qpos_before = (
                obs["robot0_gripper_qpos"].copy()
            )

            next_obs, reward, done, info = env.step(
                action_t
            )
            gripper_qpos_after = (
                next_obs["robot0_gripper_qpos"].copy()
            )
            # 组成step：
            step_t = {
                # 执行动作之前的观测 obs_t
                "observation": rlds_obs_t,

                # 在 obs_t 状态下执行的动作 action_t
                "action": action_t.copy(),

                # LIBERO 环境返回的奖励
                "reward": np.float32(reward),

                # 当前先固定为 1.0
                "discount": np.float32(1.0),

                # 目前只采集了一个 step，所以它同时是第一个和最后一个
                "is_first": step_index == 0,
                "is_last": bool(done),

                # done 表示环境是否真正结束
                "is_terminal": bool(done),

                # 同一个 episode 的每一步都保存相同的语言指令
                "language_instruction": task.language,
            }
            episode_steps.append(step_t)
            obs = next_obs
            if done:
                break

        episode_steps[-1]["is_last"] = True
        # print(episode_steps)
        episode = {
            "steps": episode_steps,
            "episode_metadata": {
                "file_path": "in_memory/test_episode_000",
            },
        }
        save_episode(episode, "example.h5")

        with h5py.File("example.h5", "r") as f:
            h5_file = read_h5_item(f)
            # print (read_episode)
            # print(list(f["episode/steps"].keys()))
            # print(f["episode/steps/000000/action"][:].shape)
            read_episode = h5_file["episode"]
            read_steps = dist2list(read_episode["steps"])
            read_episode["steps"] = read_steps
            print(len(read_episode["steps"]))
            print(read_episode["steps"][0].keys())

    finally:
        env.close()


if __name__ == "__main__":
    main()


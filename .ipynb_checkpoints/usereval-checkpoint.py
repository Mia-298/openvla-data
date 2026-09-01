import os
from transformers import AutoModelForVision2Seq, AutoProcessor
# from peft import PeftModel
from PIL import Image
import torch
import numpy as np
# import tqdm
# from libero.libero import benchmark
import copy
from libero.libero import benchmark
import utils
from config import Config
from custom_success import LiftSuccessChecker
import csv

TASK_ID = 2
INIT_STATE_ID = 0
TARGET_OBJECT = "akita_black_bowl_1"
MAX_STEPS = 220
CUSTOM_PROMPT = (
    "pick up the black bowl from the center of the table"
)
MODEL_PATH = (
    "/root/data/openvla_work/models/"
    "openvla-7b-finetuned-libero-spatial"
)
DEVICE = torch.device("cuda:0") if torch.cuda.is_available() else torch.device("cpu")
SUITE_NAME = "libero_goal"
# 环境类型，可以是libero中不同的环境
MODEL_UNNORM_KEY = "libero_spatial"
# 动作尺度和动作解码方式必须和模型一致
def main():
    # 加载openvla模型,processor负责处理输入信息
    processor = AutoProcessor.from_pretrained(
        MODEL_PATH,
        trust_remote_code=True,
    )
    model = AutoModelForVision2Seq.from_pretrained(
        MODEL_PATH,
        torch_dtype=torch.float16,
        low_cpu_mem_usage=True,
        trust_remote_code=True,
        load_in_8bit=True,
        attn_implementation="sdpa",
    )
    # 初始化LIBERO任务
    suite = benchmark.get_benchmark_dict()[SUITE_NAME]()
    task = suite.get_task(TASK_ID)
    init_states = suite.get_task_init_states(TASK_ID)

    env, original_task_description = utils.get_libero_env(task, "openvla", resolution=768)
    env.reset()
    # 设置初始状态
    obs = env.set_init_state(
        init_states[INIT_STATE_ID]
    )
    log_file = open(
        "custom_rollout_log.csv",
        "w",
        newline="",
    )

    log_writer = csv.writer(log_file)

    log_writer.writerow([
        "step",
        "dx",
        "dy",
        "dz",
        "droll",
        "dpitch",
        "dyaw",
        "gripper",
        "bowl_z",
        "bowl_delta_z",
        "success_counter",
        "custom_success",
        "libero_done",
    ])
    video_log_file = open(
        "custom_rollout_video_log.txt",
        "w",
    )
    replay_images = []
    total_episodes, total_successes = 0, 0
    # 先稳定
    for i in range(10):
        obs, reward, done, info = env.step(
            [0, 0, 0, 0, 0, 0, -1]
        )
    base_env = env.env
    # 4. 创建自定义 success checker
    checker = LiftSuccessChecker(
        base_env=base_env,
        object_name=TARGET_OBJECT,
        lift_threshold=0.05,
        required_steps=5,
    )
    for t in range(MAX_STEPS):
        # 获取一帧输入图像
        image = obs["agentview_image"]
        
        image = image[::-1, ::-1]
        replay_images.append(copy.deepcopy(image))
        model_img = utils.resize_image(
            image,
            (224, 224),
        )
        # 模型输入
        prompt = (
            "In: What action should the robot take to "
            f"{CUSTOM_PROMPT.lower()}?\n"
            "Out:"
        )
        inputs = processor(
            prompt,
            Image.fromarray(model_img).convert("RGB"),
            return_tensors="pt",
        ).to(
            DEVICE,
            dtype=torch.float16,
        )
        # 模型输出action.shape == (1, 7)：[dx, dy, dz, droll, dpitch, dyaw, gripper]
        with torch.inference_mode():
            action = model.predict_action(
                **inputs,
                # inputs是字典，**inpust代表predict_action输入不是一个字典而是字典内部的成员
                unnorm_key=MODEL_UNNORM_KEY,
                # OpenVLA模型必须加载对应数据集的统计信息，否则动作尺度错误 
                do_sample=False,
            )
        print("\n" + "=" * 70)
        print("OPENVLA OUTPUT")
        print("=" * 70)

        print("Prompt:")
        print(CUSTOM_PROMPT)

        print("\nPredicted action:")
        print(action)

        print("\nAction shape:")
        print(np.asarray(action).shape)
        

        print("\nSINGLE-ACTION INFERENCE TEST: PASS")
        # 处理输出的 action中的夹爪，使其符合 LIBERO 的定义（LIBERO 中夹爪的控制量：-1 = open, +1 = close）
        # 将夹爪的控制量，从 [0, 1] 范围转换到 [-1, +1]
        action[..., -1] = 2 * action[..., -1] - 1

        # 将夹爪控制量进行二值化, 大于0的值置为 +1，小于0的值置为 -1
        action[..., -1] = np.sign(action[..., -1])

        # 将夹爪控制量反转
        action[..., -1] = action[..., -1] * -1.0

        # 更新环境
        obs, reward, done, info = env.step(action.tolist())
        success,info = checker.update()
        log_writer.writerow([
            t,
            float(action[0]),
            float(action[1]),
            float(action[2]),
            float(action[3]),
            float(action[4]),
            float(action[5]),
            float(action[6]),
            info["current_z"],
            info["delta_z"],
            info["success_counter"],
            success,
            done,
        ])

        log_file.flush()
        if success:
            print("success")
            break
        else:
            print("info",info)
    utils.save_rollout_video(
        replay_images,
        1,
        success=success,
        task_description=CUSTOM_PROMPT,
        log_file=video_log_file,
    )
    video_log_file.close()
    log_file.close()
    env.close()
    #test
    


if __name__ == "__main__":
    main()

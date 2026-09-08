import os
from transformers import AutoModelForVision2Seq, AutoProcessor

from PIL import Image
import torch
import numpy as np

import copy
from libero.libero import benchmark
import utils
from config import Config
from custom_success import LiftSuccessChecker
import csv

CUSTOM_PROMPT = (
    "pick up the black bowl from the center of the table"
)

DEVICE = torch.device("cuda:0") if torch.cuda.is_available() else torch.device("cpu")
SUITE_NAME = "libero_goal"
# 环境类型，可以是libero中不同的环境
MODEL_UNNORM_KEY = "libero_spatial"
# 动作尺度和动作解码方式必须和模型一致
IMAGE_PATH = "startup_camera.png"
MODEL_PATH = (
    "/root/data/openvla_work/models/"
    "openvla-7b-finetuned-libero-spatial"
)

def main():
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
    image = Image.open(IMAGE_PATH).convert("RGB")
    # PIL->numpy
    image = np.array(image)
    image = image[::-1, ::-1]
    model_img = utils.resize_image(
        image,
        (224, 224),
    )
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
    print(inputs.keys())
    for key, value in inputs.items():
        print(
            key,
            "shape =", value.shape,
            "dtype =", value.dtype,
            "device =", value.device,
        )
    # input_ids shape = torch.Size([1, 26]) dtype = torch.int64 device = cuda:0
    # prompt经过professor变成一个26维的数组（26个TOKEN ID）
    # attention_mask shape = torch.Size([1, 26]) dtype = torch.int64 device = cuda:0
    # attention_mask 
    # 用于描述哪些 token 有效，哪些是padding
    # pixel_values shape = torch.Size([1, 6, 224, 224]) dtype = torch.float16 device = cuda:0
    # RGB的TOKEN
    with torch.inference_mode():
        action = model.predict_action(
            **inputs,
            # inputs是字典，**inpust代表predict_action输入不是一个字典而是字典内部的成员
            unnorm_key=MODEL_UNNORM_KEY,
            # OpenVLA模型必须加载对应数据集的统计信息，否则动作尺度错误 
            do_sample=False,
        )
    print(model.norm_stats.keys())
    print(np.asarray(action).shape)
    print(action)
if __name__ == "__main__":
    main()


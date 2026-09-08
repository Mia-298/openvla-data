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
IMAGE_PATH = "image/startup_camera.png"
MODEL_PATH = (
    "/root/data/openvla_work/models/"
    "openvla-7b-finetuned-libero-spatial"
)

def main():
    processor = AutoProcessor.from_pretrained(
        MODEL_PATH,
        trust_remote_code=True,
    )
    image = Image.open("image/startup_camera.png").convert("RGB")
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

import numpy as np
from transformers import AutoProcessor

MODEL_PATH = (
    "/root/data/openvla_work/models/"
    "openvla-7b-finetuned-libero-spatial"
)
processor = AutoProcessor.from_pretrained(
    MODEL_PATH,
    trust_remote_code=True,
)
bins = np.linspace(-1, 1, 256)
bin_centers = (bins[:-1] + bins[1:]) / 2.0
q99 =  np.array([5,5,5,180,180,180,1])
q01 =  np.array([-5,-5,-5,-180,-180,-180,0])
actions = np.array([1,3,1,20,30,50,0.1])
# 归一化前的数据，假设是dx，dy...gripper

normalized_actions = 2*(actions-q01)/(q99-q01)-1
discretized_action = np.digitize(normalized_actions, bins)
print(normalized_actions)
print(discretized_action)
vocab_size = processor.tokenizer.vocab_size
token_ids = vocab_size - discretized_action
print("vocab_size:", vocab_size)
print("token_ids:", token_ids)

decoded_bin_ids = processor.tokenizer.vocab_size - token_ids
decoded_indices = np.clip(
    decoded_bin_ids - 1,
    a_min=0,
    a_max=len(bin_centers) - 1
)
print("decoded bin ids:")
print(decoded_bin_ids)
decoded_normalized_actions = bin_centers[decoded_indices]
print(decoded_normalized_actions)
actions = np.where(
            1,
            0.5 * (decoded_normalized_actions + 1) * (q99 - q01) + q01,
            decoded_normalized_actions,
        )
print(actions)

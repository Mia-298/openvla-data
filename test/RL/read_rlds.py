import tensorflow_datasets as tfds
import tensorflow as tf
data_dir = "/home/mia/datasets/Libero_RLDS/libero_spatial_no_noops/1.0.0"
builder = tfds.builder_from_directory(data_dir)
dataset = builder.as_dataset(split="train", shuffle_files=False)
episode = next(iter(dataset))
print(episode.keys())
steps = episode["steps"]
step = next(iter(steps))
print(step.keys())

print("观测字段：", step["observation"].keys())

action = step["action"]
print("动作值：", action.numpy())
print("动作形状：", action.shape)
print("动作类型：", action.dtype)
counter = 0
for s in episode["steps"]:
    counter += 1

print(counter)

instruction = step["language_instruction"]
print("任务文字：", instruction.numpy().decode("utf-8"))

image = step["observation"]["image"]
print("图像形状：", image.shape)
print("图像类型：", image.dtype)
print(step["discount"].dtype)
print(step["reward"].dtype)


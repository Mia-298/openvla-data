import numpy as np
import torch
from torch import nn

DT = 0.1
MAX_SPEED = 1.0  # 每个坐标轴的速度上限
KP = 2.0


def make_state(position, goal):
    """当前位置(2,) + 目标位置(2,) -> 状态(4,)"""
    return np.concatenate([position, goal]).astype(np.float32)


def expert_policy(state):
    """专家：根据目标与当前位置的误差输出速度。"""
    position = state[:2]
    goal = state[2:]

    error = goal - position
    action = KP * error

    return np.clip(action, -MAX_SPEED, MAX_SPEED)


def step(position, action):
    """执行一次速度动作，返回新的位置。"""
    action = np.clip(action, -MAX_SPEED, MAX_SPEED)
    next_position = position + action * DT

    return next_position

def collect_demonstrations(num_episodes=100,max_steps = 50,seed = 0):
    rng = np.random.default_rng(seed)
    states = []
    actions = []
    for _ in range(num_episodes):
        position = rng.uniform(-1.0, 1.0, size=2).astype(np.float32)
        goal = rng.uniform(-1.0, 1.0, size=2).astype(np.float32)
        for _ in range(max_steps):
            state = make_state(position, goal)
            action = expert_policy(state).astype(np.float32)
            states.append(state)
            actions.append(action)
            position = step(position, action).astype(np.float32)
            if np.linalg.norm(goal - position) < 0.05:
                break
    return np.stack(states), np.stack(actions)

if __name__ == "__main__":
    states,actions = collect_demonstrations()
    print("states shape:", states.shape)
    print("actions shape:", actions.shape)
    print(
        "label check:",
        np.allclose(actions[0], expert_policy(states[0])),
    )
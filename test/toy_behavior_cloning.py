import numpy as np

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


if __name__ == "__main__":
    position = np.array([0.0, 0.0], dtype=np.float32)
    goal = np.array([0.8, -0.4], dtype=np.float32)

    state = make_state(position, goal)
    action = expert_policy(state)
    next_position = step(position, action)

    print("state:", state)
    print("action:", action)
    print("next_position:", next_position)
    print("distance before:", np.linalg.norm(goal - position))
    print("distance after:", np.linalg.norm(goal - next_position))
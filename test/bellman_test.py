# 在已经训练好的奖励机制里找出最优解
Q = {
    "A": {
        "直接到G": 1.0,
        "先到B": 1.125,
    },
    "B": {
        "到G": 0.0,
    },
}
gamma = 0.5
alpha = 0.5

print(Q["A"]["先到B"])
max_q = max(Q["A"].values())
best_action = None
best_q = float("-inf")  # 负无穷，保证第一个 Q 值能参与比较

for action in Q["A"]:
    value = Q["A"][action]

    if value > best_q:
        best_q = value
        best_action = action

print(best_action)  # 先到B
print(best_q)       # 1.125

# ε-greedye：多数时候选最大 Q，偶尔随机探索
import random

state = "A"
epsilon = 0.1

# if random.random() < epsilon:
#     # 探索：从当前状态的可用动作中随机选择
#     action = random.choice(list(Q[state].keys()))
#     print("探索，选择：", action)
# else:
#     # 利用：选择当前 Q 最大的动作
#     action = max(Q[state], key=Q[state].get)
#     print("利用，选择：", action)


def step(state, action):
    if state == "A" and action == "直接到G":
        return "G", 2, True

    elif state == "A" and action == "先到B":
            return "B", 1, False
    elif state == "B" and action == "到G":
                return "G", 3, True

    raise ValueError(f"无效的状态和动作组合：{state}, {action}")
# 初始化
Q = {
    "A": {"直接到G": 0.0, "先到B": 0.0},
    "B": {"到G": 0.0},
}

# 逐个动作更新Q
def step_loop(count = 100):
     for i in range(count):
        state = "A"
        action = "先到B"
        next_state, reward, done = step(state, action)
        # 计算更新目标
        if done:
            target = reward
        else:
            next_max_q = max(Q[next_state].values())
            target = reward + gamma * next_max_q
        # 更新Q表对应状态
        old_q = Q[state][action]
        Q[state][action] = old_q+alpha*(target-old_q)

        state = next_state
        action = "到G"

        next_state, reward, done = step(state, action)

        if done:
            target = reward
        else:
            target = reward + gamma * max(Q[next_state].values())

        old_q = Q[state][action]
        Q[state][action] = old_q + alpha * (target - old_q)
        state = "A"
        action = "直接到G"

        next_state, reward, done = step(state, action)

        if done:
            target = reward
        else:
            target = reward + gamma * max(Q[next_state].values())

        old_q = Q[state][action]
        Q[state][action] = old_q + alpha * (target - old_q)


step_loop()
print("更新后的Q表：", Q)
# 清空q表
Q = {
    "A": {"直接到G": 0.0, "先到B": 0.0},
    "B": {"到G": 0.0},
}
# 真正的回报训练：执行带有随机行为的回报最高的动作
def step_loop(count=100, epsilon=0.1):
    for i in range(count):
        state = "A"
        done = False

        while not done:
            # 1. 根据当前状态选择一个合法动作
            if random.random() < epsilon:
                action = random.choice(list(Q[state].keys()))
            else:
                action = max(Q[state], key=Q[state].get)

            # 2. 执行动作
            next_state, reward, done = step(state, action)

            # 3. 计算更新目标
            if done:
                target = reward
            else:
                target = reward + gamma * max(Q[next_state].values())

            # 4. 更新当前状态—动作对应的格子
            old_q = Q[state][action]
            Q[state][action] = old_q + alpha * (target - old_q)

            # 5. 推进状态，下一次从这里继续
            state = next_state

    return Q
step_loop()
print("更新后的Q表：", Q)

# 评估Q表
state = "A"
done = False

trajectory = [state]
total_return = 0.0
discount = 1.0

while not done:
    # 只利用学到的 Q 表，不探索
    action = max(Q[state], key=Q[state].get)

    next_state, reward, done = step(state, action)

    print("执行：", state, action, "→", next_state, "奖励：", reward)

    # 累加本次实际轨迹的折扣回报
    total_return += discount * reward
    discount *= gamma

    trajectory.append(next_state)
    state = next_state

print("评估路径：", trajectory)
print("折扣回报：", total_return)
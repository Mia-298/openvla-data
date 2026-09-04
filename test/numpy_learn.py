import numpy as np
# 实现基于 q01/q99 的归一化、裁剪和反归一化。
# 1.归一化的动作和numpy数组的操作
action = np.array([
    0.01, -0.02, 0.03,
    0.1, -0.1, 0.2,
    1.0
])
print(action.shape)
# 数据类型
print(action.dtype)

# (7,)一个动作，包含 7 个维度
# float64


normalized_action = np.array([
    [0.01, -0.02, 0.03, 0.1, -0.1, 0.2, 1.0],
    [0.02, -0.01, 0.01, 0.2, -0.2, 0.1, 0.0],
])
print(normalized_action.shape)
# (2, 7)2 个动作样本，每个动作 7 个维度

x=normalized_action[:, 0]
# 取每个动作的第0维度
print(x.shape)
# （2，）2个动作一个维度
y = normalized_action[:, -1]
print(y.shape)
# （2，）取每个动作的后1个维度

# 2.广播 broadcasting
# 设置每个动作维度的上下限
low = np.array([-1, -1, -1, -3.14, -3.14, -3.14, 0])
high = np.array([1, 1, 1, 3.14, 3.14, 3.14, 1])
# 归一化：normalized_action = 2*(action-low)/(high-low)-1
# 反归一化：action = (normalized_action+1)/2*(high-low)+low
actions =  (normalized_action+1)/2*(high-low)+low
print(actions)
normalized_action_copy = 2*(actions-low)/(high-low)-1
print(normalized_action_copy)

actions_2 = np.array([
    [1,1,2,3,4],
    [2,2,0,1,2]
])
low_2 = np.array([0,0,0,0,0])
high_2 = np.array([0,3.14,5,5,5])
def normalize(actions,low,high):
    # 处理越界
    clipped = np.clip(actions, low, high)
    # 处理high,low相等
    valid = high > low#(不符合的值位置为false)
    mask = valid
    print(valid)
    return np.where(mask,2*(clipped-low)/(high-low)-1,1.0,)
def unnormalize(normalized_action,low,high):
    return (normalized_action+1)/2*(high-low)+low




print(normalize(actions_2,low_2,high_2))
print(unnormalize(normalize(actions_2,low_2,high_2),low_2,high_2))



# 点乘：*代表每个元素逐个相乘，需要行列对应
# @是叉乘，行和列对应乘并相加
x = np.array([1, 2, 3])
w = np.array([
    [1, 0],
    [0, 1],
    [1, 1],
])
y = x @ w
#y = [1*1+2*0+3*1][1*0+2*1+3*1] = [4,5]
print(y)

# axis=0:每一列计算
print(w.sum(axis=0))
# axis = 1每一行计算
print(w.sum(axis=1))
# np.min(normalized_action, axis=0)
# 计算每一列的最小值
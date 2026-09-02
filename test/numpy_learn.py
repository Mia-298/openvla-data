import numpy as np
# 实现基于 q01/q99 的归一化、裁剪和反归一化。
# 归一化的动作
action = np.array([
    0.01, -0.02, 0.03,
    0.1, -0.1, 0.2,
    1.0
])
print(action.shape)
print(action.dtype)


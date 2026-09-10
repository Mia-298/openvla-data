import numpy as np
from scipy.spatial.transform import Rotation as Rs
import FK_learn


# 这里用的是6轴机械臂做例子，假设每个关节自己的z轴是旋转轴
# 雅可比矩阵的第i列Jvi = zi（Pe-pi）
def 
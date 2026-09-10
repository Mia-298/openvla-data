import numpy as np
from scipy.spatial.transform import Rotation as Rs
import FK_learn

q = np.array([
    1.23,
    2.1,
    0.3,
    -0.3,
    0.5,
    -1,7])
q_dot = np.array([
    0.2,
    0.3,
    -0.1,
    0.5,
    0.2,
    -0.3
])
Tb1 = np.eye(4)
T12 = np.eye(4)
T23 = np.eye(4)
T34 = np.eye(4)
T45 = np.eye(4)
T56 = np.eye(4)


T_joints = FK_learn.Tbn(q,Tb1,T12,T23,T34,T45,T56)
T_ee = T_joints[-1]

# 雅可比矩阵的作用是将关节速度转换成末端的线速度和角速度
# 这里用的是6轴机械臂做例子，假设第 i 个关节绕 zi−1为q
# 雅可比矩阵的上半部分线速度第i列Jvi = zi-1（pe-pi-1）
# 下半部分角速度 = zi
# pe末端执行器当前在 base 下的位置
# pi第i个关节原点当前在base下的位置
# zi第i个关节旋转轴在base坐标系下的方向向量（角速度向量）
# 一般是已知q和Tb1-T56,还有q_dot(关节速度)
def geometric_jacobian(T_joints, T_ee):
    pe = T_ee[:3,3]
    T_axis_frames = [
        np.eye(4),     # joint 1 -> frame 0 / base
        T_joints[0],   # joint 2 -> frame 1
        T_joints[1],   # joint 3 -> frame 2
        T_joints[2],   # joint 4 -> frame 3
        T_joints[3],   # joint 5 -> frame 4
        T_joints[4],   # joint 6 -> frame 5
    ]
    J = np.zeros((6, 6), dtype=float)
    for i in range (6):
        p_i = T_axis_frames[i][:3, 3]
        z_i= T_axis_frames[i][:3, 2]
        J[:3, i] = np.cross(z_i, pe - p_i)
        J[3:, i] = z_i

    return J

def q_dot2eevw(J,q_dot):
    vw = J@q_dot
    v = vw[:3]
    w = vw[3:]
    return v,w
import numpy as np
from scipy.spatial.transform import Rotation as Rs
import FK_learn

q = np.array([
    1.23,
    2.1,
    0.3,
    -0.3,
    0.5,
    -1.7])
q_dot = np.array([
    0.2,
    0.3,
    -0.1,
    0.5,
    0.2,
    -0.3
])
Tb1 = FK_learn.Cartesian2transform(
    [0.0, 0.0, 0.3],
    [0.0, 0.0, 0.0]
)

T12 = FK_learn.Cartesian2transform(
    [0.3, 0.0, 0.0],
    [np.pi/2, 0.0, 0.0]
)

T23 = FK_learn.Cartesian2transform(
    [0.3, 0.0, 0.0],
    [0.0, np.pi/2, 0.0]
)

T34 = FK_learn.Cartesian2transform(
    [0.2, 0.0, 0.0],
    [np.pi/2, 0.0, 0.0]
)

T45 = FK_learn.Cartesian2transform(
    [0.15, 0.0, 0.0],
    [0.0, np.pi/2, 0.0]
)

T56 = FK_learn.Cartesian2transform(
    [0.1, 0.0, 0.0],
    [0.0, 0.0, 0.0]
)

# 当前的T，而不是初始0位的
T_joints = FK_learn.Tbn(q,Tb1,T12,T23,T34,T45,T56)
T_ee = T_joints[-1]

# 雅可比矩阵的作用是将关节速度转换成末端的线速度和角速度
# 这里用的是6轴机械臂做例子，假设第 i 个关节绕 zi−1为q
# 雅可比矩阵的上半部分线速度第i列Jvi = zi-1（pe-pi-1）
# 下半部分角速度 = zi
# pe末端执行器当前在 base 下的位置
# pi第i个关节原点当前在base下的位置
# zi：第i个关节旋转轴在base坐标系下的单位方向向量
# zi * q_dot[i] 才是该关节产生的角速度向量
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



# 差分验证
def numerical_position_jacobian(q, Tb1, T12, T23, T34, T45, T56):

    epsilon = 1e-6

    T0 = FK_learn.Tbn(
        q, Tb1, T12, T23, T34, T45, T56
    )

    p0 = T0[-1][:3, 3]

    J_num = np.zeros((3, 6))

    for i in range(6):

        q_new = q.copy()
        q_new[i] += epsilon

        T_new = FK_learn.Tbn(
            q_new,
            Tb1, T12, T23,
            T34, T45, T56
        )

        p_new = T_new[-1][:3, 3]

        J_num[:, i] = (p_new - p0) / epsilon

    return J_num
def numerical_angular_jacobian(
    q,
    Tb1, T12, T23, T34, T45, T56
):
    epsilon = 1e-6

    # 当前姿态
    T0 = FK_learn.Tbn(
        q,
        Tb1, T12, T23,
        T34, T45, T56
    )

    R0 = T0[-1][:3, :3]

    Jw_num = np.zeros((3, 6))

    for i in range(6):

        # 只让第 i 个关节增加 epsilon
        q_new = q.copy()
        q_new[i] += epsilon

        T_new = FK_learn.Tbn(
            q_new,
            Tb1, T12, T23,
            T34, T45, T56
        )

        R_new = T_new[-1][:3, :3]

        # 在 base frame 下的相对旋转
        R_delta = R_new @ R0.T

        # 微小旋转矩阵 -> rotation vector
        rotvec = Rs.from_matrix(
            R_delta
        ).as_rotvec()

        # 数值角速度 Jacobian
        Jw_num[:, i] = rotvec / epsilon

    return Jw_num

if __name__ == "__main__":
    J = geometric_jacobian(T_joints, T_ee)

    J_num = numerical_position_jacobian(
        q,
        Tb1, T12, T23,
        T34, T45, T56
    )
    Jw_num = numerical_angular_jacobian(
    q,
    Tb1, T12, T23,
    T34, T45, T56
)

    print("Geometric:")
    print(J[:3, :])

    print("Finite difference:")
    print(J_num)
    print("error:")
    print(J[:3, :] - J_num)

    print("Finite difference Jw:")
    print(Jw_num)
    print("Jw error:")
    print(J[3:, :] - Jw_num)

    v, w = q_dot2eevw(J, q_dot)

    print("v =", v)
    print("w =", w)
    print("rank =", np.linalg.matrix_rank(J))
    print("condition number =", np.linalg.cond(J))
    # 如果想在瞬时意义上独立控制末端的 6 个自由度：理想情况下需要：rank = 6
    # 现在只有 5，意味着末端的 6 个速度自由度里面，有一个方向无法独立产生。
    # 是因为J[:,0]=J[:,1]也就是 joint 1 和 joint 2 对末端产生完全一样的瞬时运动效果。
    # 因为雅可比矩阵几乎不可逆

    # DifferentialIK就是反过来，从末端的运动差->关节的角速度，但是奇异姿态导致rank(J)=5，不能简单求逆
    # 改成J+，叫 Moore-Penrose pseudoinverse
    # 比如人为指定末端速度
    x_dot = np.array([
        0.05,   # vx m/s
        0.00,   # vy
        0.00,   # vz
        0.00,   # wx rad/s
        0.00,   # wy
        0.00    # wz
    ])
    q_dot = np.linalg.pinv(J) @ x_dot

    print(q_dot)
    # 还有一种PoseIK，根据目标位姿直接输出关节角


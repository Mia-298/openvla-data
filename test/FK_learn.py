import numpy as np
from scipy.spatial.transform import Rotation as R

def make_transform(rotation, translation):
    rotation = np.asarray(rotation, dtype=float)
    # 旋转矩阵3x3
    translation = np.asarray(translation, dtype=float).reshape(3)
    # 平移矩阵3x1
    transform = np.eye(4)
    transform[:3,:3] = rotation
    # 3行3列放入rotation
    transform[:3,3] = translation
    # 3行第四列放入translation
    return transform

def rpy2r(rpy):
    rpy = np.asarray(rpy,dtype = float).reshape(3)
    # # R包含很多关于旋转角的数学工具，
    # # RPY -> 旋转矩阵
    # R_mat = R.from_euler("xyz", rpy).as_matrix()

    # # 旋转矩阵 -> RPY
    # rpy = R.from_matrix(R_mat).as_euler("xyz")

    # # 轴角 -> 旋转矩阵
    # R_mat = R.from_rotvec(axis * angle).as_matrix()

    # # 旋转矩阵 -> 四元数
    # quat = R.from_matrix(R_mat).as_quat()

    # # 四元数 -> 旋转矩阵
    # R_mat = R.from_quat(quat).as_matrix()
    r = R.from_euler("xyz", rpy, degrees=False)
    R_mat = r.as_matrix()
    return R_mat

# xyz,rpy转换成T矩阵
# rpy = [roll, pitch, yaw], radians
def Cartesian2transform(xyz,rpy):
    xyz = np.asarray(xyz,dtype = float).reshape(3)
    rpy = np.asarray(rpy,dtype = float).reshape(3)
    R_mat = rpy2r(rpy)
    T = make_transform(R_mat,xyz)
    return T

# T矩阵转换为笛卡尔坐标
def transfotm2Cartesian(T):
    T = np.asarray(T,dtype = float)
    xyz = T[:3, 3]
    rpy = rpy_A = R.from_matrix(T[:3,:3]).as_euler(
        "xyz",
        degrees=False
    )
    return xyz,rpy

# B坐标系在A坐标系下的T矩阵Tab  变换成A坐标系在B坐标系下的T矩阵Tba
def invert_transform(Tab):
    Tab = np.asarray(Tab, dtype=float)
    R_mat = Tab[:3, :3]
    t = Tab[:3, 3]
    Tba = np.eye(4)
    Tba[:3,:3] = R_mat.T
    Tba[:3,3] = -R_mat.T @ t
    return Tba

# 把一个点从坐标系B变换到坐标系A,Tab是B坐标系在A坐标系下的T矩阵
def transform_point(Tab,xyz_B):
    Tab = np.asarray(Tab,dtype = float)
    xyz_B = np.asarray(xyz_B,dtype = float)
    xyz_A = Tab[:3,:3]@xyz_B+Tab[:3,3]
    return xyz_A

# 把一个物体从坐标系B变换到坐标系A
def transform_obj(Tab,T_BO):
    Tab = np.asarray(Tab,dtype = float)
    T_BO = np.asarray(T_B,dtype = float)
    T_AO = Tab@T_BO
    return T_AO

# 串联两个坐标系，Tab和Tbc，变成b坐标系在c坐标系下的T矩阵，其实和transform_obj
def compose_transform(Tab,Tbc):
    return transform_obj(Tab,Tbc)

# 主动绕b坐标系旋转矩阵Rb后的Tab
def active_rotate_self(Tab,Rb):
    Tab = np.asarray(Tab, dtype=float).copy()
    Rb = np.asarray(Rb, dtype=float)
    Rab = Tab[:3,:3]@Rb
    Tab[:3,:3] = Rab    
    return Tab


# 主动绕a坐标系旋转矩阵Rb后的Tab
def active_rotate_parent(T, R_parent):
    T = np.asarray(T, dtype=float)
    R_parent = np.asarray(R_parent, dtype=float)

    delta_T = np.eye(4)
    delta_T[:3, :3] = R_parent

    return delta_T @ T

# 被动旋转旋转矩阵Ra下，Tob的变化
def passive_rotate(Toa,Tab,Ra):
    Ta = np.eye(4)
    Ta[:3,:3] = Ra
    Tob = Toa@Ra@Tab 
    return Tob

# 计算第n个关节在当前j下基坐标下的Tbn
# q一般是绕上一个坐标系的旋转轴
def Tbn(q,Tb1,T12,T23,T34,T45,T56):
    q = np.asarray(q, dtype=float).reshape(6)
    R1 = rpy2r([0,0,q[0]])
    R2 = rpy2r([0,0,q[1]])
    R3 = rpy2r([0,0,q[2]])
    R4 = rpy2r([0,0,q[3]])
    R5 = rpy2r([0,0,q[4]])
    R6 = rpy2r([0,0,q[5]])
    Tb1 = active_rotate_parent(Tb1,R1)
    T12 = active_rotate_parent(T12,R2)
    T23 = active_rotate_parent(T23,R3)
    T34 = active_rotate_parent(T34,R4)
    T45 = active_rotate_parent(T45,R5)
    T56 = active_rotate_parent(T56,R6)
    Tb2 = Tb1@T12
    Tb3 = Tb2@T23
    Tb4 = Tb3@T34
    Tb5 = Tb4@T45
    Tb6 = Tb5@T56
    T_joints = [
        Tb1,
        Tb2,
        Tb3,
        Tb4,
        Tb5,
        Tb6,
    ]
    return T_joints

# 计算6轴机械臂在关节值J下：基坐标系下的末端T矩阵（FK）    
def Tbj6(q,Tb1,T12,T23,T34,T45,T56):
    q = np.asarray(q, dtype=float).reshape(6)
    R1 = rpy2r([0,0,q[0]])
    R2 = rpy2r([0,0,q[1]])
    R3 = rpy2r([0,0,q[2]])
    R4 = rpy2r([0,0,q[3]])
    R5 = rpy2r([0,0,q[4]])
    R6 = rpy2r([0,0,q[5]])
    Tb1 = active_rotate_parent(Tb1,R1)
    T12 = active_rotate_parent(T12,R2)
    T23 = active_rotate_parent(T23,R3)
    T34 = active_rotate_parent(T34,R4)
    T45 = active_rotate_parent(T45,R5)
    T56 = active_rotate_parent(T56,R6)
    Tb6 = Tb1 @ T12 @ T23 @ T34 @ T45 @ T56
    return transfotm2Cartesian(Tb6)

if __name__ == "__main__":
    rotation = np.eye(3)
    translation = np.array([1.0, 2.0, 3.0])

    transform = make_transform(rotation, translation)

    print(transform)
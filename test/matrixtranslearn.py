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

# xyz,rpy转换成T矩阵
# rpy = [roll, pitch, yaw], radians
def Cartesian2transform(xyz,rpy):
    xyz = np.asarray(xyz,dtype = float).reshape(3)
    rpy = np.asarray(rpy,dtype = float).reshape(3)
    r = R.from_euler("xyz", rpy, degrees=False)
    R_mat = r.as_matrix()
    T = make_transform(R_mat,xyz)
    return T
def transfotm2Cartesian(T):
    T = np.asarray(T,dtype = float)
    xyz = T[:3, 3]
    rpy = rpy_A = R.from_matrix(T[:3,:3]).as_euler(
        "xyz",
        degrees=False
    )
    return xyz,rpy

# 把一个点从坐标系B变换到坐标系A,Tab是B坐标系在A坐标系下的T矩阵
def transform_obj(Tab,xyz_B):
    Tab = np.asarray(Tab,dtype = float)
    xyz_B = np.asarray(xyz_B,dtype = float)
    xyz_A = Tab[:3,:3]@xyz_B+Tab[:3,3]
    return xyz_A

# 把一个物体从坐标系B变换到坐标系A
def transform_obj(Tab,T_B):
    Tab = np.arrasarrayy(Tab,dtype = float)
    T_B = np.asarray(T_B,dtype = float)
    T_A = Tab@T_B
    return T_A


if __name__ == "__main__":
    rotation = np.eye(3)
    translation = np.array([1.0, 2.0, 3.0])

    transform = make_transform(rotation, translation)

    print(transform)
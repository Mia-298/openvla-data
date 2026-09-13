from pathlib import Path
import numpy as np
import mujoco
import FK_learn
import IK_learn
import time
import mujoco.viewer
def get_site_pose_in_base(
    model,
    data,
    site_name,
    base_body_name="base",
):
    mujoco.mj_forward(model, data)

    site_id = mujoco.mj_name2id(
        model,
        mujoco.mjtObj.mjOBJ_SITE,
        site_name,
    )

    base_id = mujoco.mj_name2id(
        model,
        mujoco.mjtObj.mjOBJ_BODY,
        base_body_name,
    )

    if site_id == -1:
        raise ValueError(
            f"不存在 site：{site_name}"
        )

    if base_id == -1:
        raise ValueError(
            f"不存在 body：{base_body_name}"
        )

    p_world_ee = (
        data.site_xpos[site_id]
        .copy()
    )

    R_world_ee = (
        data.site_xmat[site_id]
        .reshape(3, 3)
        .copy()
    )

    p_world_base = (
        data.xpos[base_id]
        .copy()
    )

    R_world_base = (
        data.xmat[base_id]
        .reshape(3, 3)
        .copy()
    )

    p_base_ee = (
        R_world_base.T
        @ (p_world_ee - p_world_base)
    )

    R_base_ee = (
        R_world_base.T
        @ R_world_ee
    )

    T_base_ee = np.eye(4)
    T_base_ee[:3, :3] = R_base_ee
    T_base_ee[:3, 3] = p_base_ee

    return T_base_ee
def get_T_joints_from_mujoco(
    model,
    data,
    joint_names,
    base_body_name="base",
):
    """
    返回当前状态下，每个 joint 相对于 base 的齐次变换矩阵。

    Returns
    -------
    T_joints : ndarray, shape (n, 4, 4)
        T_joints[i] 表示 base -> joint_i。
    """

    # 根据当前 qpos 更新所有笛卡尔量
    mujoco.mj_forward(model, data)

    base_id = mujoco.mj_name2id(
        model,
        mujoco.mjtObj.mjOBJ_BODY,
        base_body_name,
    )

    if base_id == -1:
        raise ValueError(
            f"模型中不存在 body：{base_body_name}"
        )

    # base 在 world 下的位姿
    p_world_base = (
        data.xpos[base_id]
        .copy()
    )

    R_world_base = (
        data.xmat[base_id]
        .reshape(3, 3)
        .copy()
    )

    T_joints = np.tile(
        np.eye(4),
        (len(joint_names), 1, 1),
    )

    for i, joint_name in enumerate(joint_names):
        joint_id = mujoco.mj_name2id(
            model,
            mujoco.mjtObj.mjOBJ_JOINT,
            joint_name,
        )

        if joint_id == -1:
            raise ValueError(
                f"模型中不存在 joint：{joint_name}"
            )

        # 当前 joint 所属的 body
        body_id = model.jnt_bodyid[joint_id]

        # joint anchor 在 world 下的位置
        p_world_joint = (
            data.xanchor[joint_id]
            .copy()
        )

        # joint 所属 body 在 world 下的旋转矩阵
        R_world_joint = (
            data.xmat[body_id]
            .reshape(3, 3)
            .copy()
        )

        # world 表达转换为 base 表达
        R_base_joint = (
            R_world_base.T
            @ R_world_joint
        )

        p_base_joint = (
            R_world_base.T
            @ (
                p_world_joint
                - p_world_base
            )
        )

        T_joints[i, :3, :3] = (
            R_base_joint
        )

        T_joints[i, :3, 3] = (
            p_base_joint
        )

    return T_joints
def get_joint_initial_info(
    model,
    joint_names,
    base_body_name="base",
):
    data_zero = mujoco.MjData(model)
    n = len(joint_names)

    zero_id = mujoco.mj_name2id(
        model,
        mujoco.mjtObj.mjOBJ_KEY,
        "zero",
    )

    if zero_id == -1:
        raise ValueError(
            "MuJoCo 模型中不存在 zero keyframe"
        )
    mujoco.mj_resetDataKeyframe(
        model,
        data_zero,
        zero_id,
    )

    mujoco.mj_forward(
        model,
        data_zero,
    )

    joint_ids = np.empty(
        n,
        dtype=int,
    )

    positions_relative = np.empty((n, 3))
    rotations_relative = np.empty((n, 3, 3))
    axes_relative = np.empty((n, 3))

    transforms_relative = np.tile(
        np.eye(4),
        (n, 1, 1),
    )

    base_body_id = mujoco.mj_name2id(
        model,
        mujoco.mjtObj.mjOBJ_BODY,
        base_body_name,
    )

    if base_body_id == -1:
        raise ValueError(
            f"不存在 body：{base_body_name}"
        )

    p_previous = (
        data_zero.xpos[base_body_id]
        .copy()
    )

    R_previous = (
        data_zero.xmat[base_body_id]
        .reshape(3, 3)
        .copy()
    )

    for i, name in enumerate(joint_names):
        joint_id = mujoco.mj_name2id(
            model,
            mujoco.mjtObj.mjOBJ_JOINT,
            name,
        )

        if joint_id == -1:
            raise ValueError(
                f"MuJoCo 模型中不存在关节：{name}"
            )

        body_id = model.jnt_bodyid[joint_id]

        p_world = (
            data_zero.xanchor[joint_id]
            .copy()
        )

        R_world = (
            data_zero.xmat[body_id]
            .reshape(3, 3)
            .copy()
        )

        axis_world = (
            data_zero.xaxis[joint_id]
            .copy()
        )

        p_relative = (
            R_previous.T
            @ (p_world - p_previous)
        )

        R_relative = (
            R_previous.T
            @ R_world
        )

        axis_relative = (
            R_previous.T
            @ axis_world
        )

        joint_ids[i] = joint_id
        positions_relative[i] = p_relative
        rotations_relative[i] = R_relative
        axes_relative[i] = axis_relative

        transforms_relative[i, :3, :3] = (
            R_relative
        )

        transforms_relative[i, :3, 3] = (
            p_relative
        )

        # 这两行不能遗漏
        p_previous = p_world
        R_previous = R_world

    print("zero qpos:")
    print(data_zero.qpos.copy())

    return (
        joint_ids,
        transforms_relative,
        axes_relative,
    )
def get_T_joint_to_site(
    model,
    joint_name,
    site_name,
):
    joint_id = mujoco.mj_name2id(
        model,
        mujoco.mjtObj.mjOBJ_JOINT,
        joint_name,
    )

    site_id = mujoco.mj_name2id(
        model,
        mujoco.mjtObj.mjOBJ_SITE,
        site_name,
    )

    if joint_id == -1:
        raise ValueError(
            f"不存在 joint：{joint_name}"
        )

    if site_id == -1:
        raise ValueError(
            f"不存在 site：{site_name}"
        )

    joint_body_id = model.jnt_bodyid[joint_id]
    site_body_id = model.site_bodyid[site_id]

    if joint_body_id != site_body_id:
        raise ValueError(
            "joint 和 site 不在同一个 body，"
            "不能直接使用此方法"
        )

    # 两者的位置都相对于同一个 body
    p_joint_body = model.jnt_pos[joint_id].copy()
    p_site_body = model.site_pos[site_id].copy()

    p_joint_site = (
        p_site_body - p_joint_body
    )

    # site 相对于所属 body 的旋转矩阵
    R_joint_site_flat = np.empty(9)

    mujoco.mju_quat2Mat(
        R_joint_site_flat,
        model.site_quat[site_id],
    )

    R_joint_site = (
        R_joint_site_flat.reshape(3, 3)
    )

    T_joint_site = np.eye(4)
    T_joint_site[:3, :3] = R_joint_site
    T_joint_site[:3, 3] = p_joint_site

    return T_joint_site

def limit_vector_norm(vector, max_norm):
    vector = np.asarray(
        vector,
        dtype=float,
    )

    vector_norm = np.linalg.norm(vector)

    if vector_norm > max_norm:
        vector = (
            vector
            / vector_norm
            * max_norm
        )

    return vector

def cartesian_closed_loop(
    model,
    data,
    joint_names,
    actuator_names,
    transforms_relative,
    axes_relative,
    T6ee,
    target_position,
    target_rpy,
    control_dt=0.01,
    max_time=10.0,
    position_tolerance=0.002,
    rotation_tolerance=0.01,
    kp_position=1.5,
    kp_rotation=1.0,
    linear_velocity_max=0.08,
    angular_velocity_max=0.3,
    joint_velocity_max=0.5,
):
    target_position = np.asarray(
        target_position,
        dtype=float,
    )

    target_rpy = np.asarray(
        target_rpy,
        dtype=float,
    )

    joint_ids = np.array([
        mujoco.mj_name2id(
            model,
            mujoco.mjtObj.mjOBJ_JOINT,
            name,
        )
        for name in joint_names
    ])

    actuator_ids = np.array([
        mujoco.mj_name2id(
            model,
            mujoco.mjtObj.mjOBJ_ACTUATOR,
            name,
        )
        for name in actuator_names
    ])

    if np.any(joint_ids == -1):
        raise ValueError(
            "存在无效 joint 名称"
        )

    if np.any(actuator_ids == -1):
        raise ValueError(
            "存在无效 actuator 名称"
        )

    qpos_addresses = (
        model.jnt_qposadr[joint_ids]
    )

    ctrl_min = model.actuator_ctrlrange[
        actuator_ids, 0
    ]

    ctrl_max = model.actuator_ctrlrange[
        actuator_ids, 1
    ]

    simulation_dt = float(
        model.opt.timestep
    )

    # 例如仿真周期 0.002 s，控制周期 0.01 s
    # 则一个控制周期执行 5 次 mj_step
    substeps = max(
        1,
        round(control_dt / simulation_dt),
    )

    actual_control_dt = (
        substeps * simulation_dt
    )

    max_cycles = int(
        max_time / actual_control_dt
    )

    K = np.diag([
        kp_position,
        kp_position,
        kp_position,
        kp_rotation,
        kp_rotation,
        kp_rotation,
    ])

    logs = {
        "time": [],
        "position": [],
        "position_error": [],
        "rotation_error_norm": [],
        "q": [],
        "q_dot": [],
        "q_command": [],
    }

    with mujoco.viewer.launch_passive(
        model,
        data,
    ) as viewer:
        q_command = (
            data.qpos[qpos_addresses]
            .copy()
        )
        for cycle in range(max_cycles):
            wall_start = time.perf_counter()

            # 1. 读取 MuJoCo 实际关节角
            q_current = (
                data.qpos[qpos_addresses]
                .copy()
            )

            # 2. 根据实际 q 重新计算 FK
            T_joints, axes_base = (
                FK_learn.Tbn(
                    q_current,
                    transforms_relative,
                    axes_relative,
                )
            )

            T_ee = FK_learn.compose_transform(
                T_joints[-1],
                T6ee,
            )

            current_position = (
                T_ee[:3, 3].copy()
            )

            # 3. 计算当前位姿误差
            error = IK_learn.pose_error(
                T_ee,
                target_position,
                target_rpy,
            )

            position_error_norm = (
                np.linalg.norm(error[:3])
            )

            rotation_error_norm = (
                np.linalg.norm(error[3:])
            )

            # 4. 判断实际状态是否到达目标
            if (
                position_error_norm
                < position_tolerance
                and rotation_error_norm
                < rotation_tolerance
            ):
                print(
                    f"闭环收敛：cycle={cycle}, "
                    f"position_error="
                    f"{position_error_norm:.6f} m, "
                    f"rotation_error="
                    f"{rotation_error_norm:.6f} rad"
                )

                return (
                    q_current,
                    True,
                    logs,
                )

            # 5. 根据当前实际状态重新计算 Jacobian
            J = IK_learn.geometric_jacobian(
                T_joints,
                T_ee,
                axes_base,
            )

            J_pinv = (
                IK_learn.damped_pseudoinverse(J)
            )

            # 6. 位姿误差转换为期望笛卡尔速度
            x_dot_command = K @ error

            x_dot_command[:3] = (
                limit_vector_norm(
                    x_dot_command[:3],
                    linear_velocity_max,
                )
            )

            x_dot_command[3:] = (
                limit_vector_norm(
                    x_dot_command[3:],
                    angular_velocity_max,
                )
            )

            # 7. DLS 计算关节速度
            q_dot = (
                J_pinv
                @ x_dot_command
            )

            q_dot = np.clip(
                q_dot,
                -joint_velocity_max,
                joint_velocity_max,
            )

            # 8. 积分得到位置执行器目标
            q_command = (
                q_command
                + q_dot * actual_control_dt
            )

            q_command = np.clip(
                q_command,
                ctrl_min,
                ctrl_max,
            )

            data.ctrl[actuator_ids] = (
                q_command
            )

            # 9. 执行 MuJoCo
            for _ in range(substeps):
                mujoco.mj_step(
                    model,
                    data,
                )

            viewer.sync()

            # 10. 记录当前控制周期数据
            logs["time"].append(
                float(data.time)
            )

            logs["position"].append(
                current_position
            )

            logs["position_error"].append(
                error[:3].copy()
            )

            logs["rotation_error_norm"].append(
                rotation_error_norm
            )

            logs["q"].append(
                q_current
            )

            logs["q_dot"].append(
                q_dot.copy()
            )

            logs["q_command"].append(
                q_command.copy()
            )

            if cycle % 50 == 0:
                print(
                    f"cycle={cycle}, "
                    f"position_error="
                    f"{position_error_norm:.6f} m, "
                    f"rotation_error="
                    f"{rotation_error_norm:.6f} rad"
                )

            elapsed = (
                time.perf_counter()
                - wall_start
            )

            if elapsed < actual_control_dt:
                time.sleep(
                    actual_control_dt - elapsed
                )

    q_final = (
        data.qpos[qpos_addresses]
        .copy()
    )

    return q_final, False, logs
MODEL_DIR = Path(__file__).resolve().parent
XML_PATH = MODEL_DIR / "models/ur5e.xml"

model = mujoco.MjModel.from_xml_path(str(XML_PATH))
data = mujoco.MjData(model)

# 加载 XML 中定义的 home 姿态
home_id = mujoco.mj_name2id(
    model,
    mujoco.mjtObj.mjOBJ_KEY,
    "home",
)

joint_names = [
    "shoulder_pan_joint",
    "shoulder_lift_joint",
    "elbow_joint",
    "wrist_1_joint",
    "wrist_2_joint",
    "wrist_3_joint"
    ]
actuator_names = [
    "shoulder_pan",
    "shoulder_lift",
    "elbow",
    "wrist_1",
    "wrist_2",
    "wrist_3",
]
ee_name="attachment_site"
mujoco.mj_resetDataKeyframe(model, data, home_id)
mujoco.mj_forward(model, data)

print("模型加载成功")
site_id = mujoco.mj_name2id(
    model,
    mujoco.mjtObj.mjOBJ_SITE,
    "attachment_site",
)
joint_ids,transforms_relative,axes_relative = get_joint_initial_info(model, joint_names)
T6ee = get_T_joint_to_site(
    model,
    joint_name=joint_names[5],
    site_name=ee_name,
)


q_current = data.qpos.copy()
# FK计算每个关节的Tbn
T_joints, axes_base = FK_learn.Tbn(
    q_current,
    transforms_relative,
    axes_relative,
)
Tbee = FK_learn.compose_transform(T_joints[5],T6ee)
ee_current_pos ,ee_current_rpy = FK_learn.transfotm2Cartesian(Tbee)
ee_target_pos = ee_current_pos+[0.1,-0.1,-0.1]
ee_target_rpy = ee_current_rpy
# 离线IK直接计算最终q，需要关节平滑插值
q_solution, success, steps = IK_learn.inverse_kinematics(q_current,ee_target_pos,ee_target_rpy,transforms_relative,axes_relative,T6ee)
print(f"start!ee_current_pos:{ee_current_pos},ee_target_pos:{ee_target_pos}")
# 笛卡尔闭环IK：根据当前执行情况真正执行-迭代
q_final, success, logs = (
    cartesian_closed_loop(
        model=model,
        data=data,
        joint_names=joint_names,
        actuator_names=actuator_names,
        transforms_relative=transforms_relative,
        axes_relative=axes_relative,
        T6ee=T6ee,
        target_position=ee_target_pos,
        target_rpy=ee_target_rpy,
        control_dt=0.01,
        max_time=10.0,
    )
)
q_current = data.qpos.copy()
Tbee_mujoco = get_site_pose_in_base(
    model,
    data,
    site_name="attachment_site",
)
ee_actual_pos, ee_actual_rpy = (
    FK_learn.transfotm2Cartesian(
        Tbee_mujoco
    )
)
print(f"success：{success}ee_current_pos:{ee_actual_pos}")
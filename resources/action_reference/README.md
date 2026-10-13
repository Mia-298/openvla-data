# Action controller teaching references

Downloaded from official repositories on 2026-10-12. These are reference copies, not the locally installed simulator or proof of the version/configuration used to collect the current RLDS data.

- libero_env_wrapper.py: https://github.com/Lifelong-Robot-Learning/LIBERO/blob/master/libero/libero/envs/env_wrapper.py (master is mutable).
- robosuite_osc_v1_4_1.py: https://github.com/ARISE-Initiative/robosuite/blob/v1.4.1/robosuite/controllers/osc.py
- osc_pose_v1_4_1.json: https://github.com/ARISE-Initiative/robosuite/blob/v1.4.1/robosuite/controllers/config/osc_pose.json
- single_arm_v1_4_1.py: https://github.com/ARISE-Initiative/robosuite/blob/v1.4.1/robosuite/robots/single_arm.py
- panda_gripper_v1_4_1.py: https://github.com/ARISE-Initiative/robosuite/blob/v1.4.1/robosuite/models/grippers/panda_gripper.py

To fully establish RLDS action semantics, also inspect the exact collection environment/configuration and dataset conversion code. Controller commands are not guaranteed achieved displacements. Axis-angle rotation commands should not be confused with Euler angles or joint angles.

- LIBERO_Spatial_dataset_builder.py: https://github.com/moojink/rlds_dataset_builder/blob/main/LIBERO_Spatial/LIBERO_Spatial_dataset_builder.py (main is mutable). Linked by the official OpenVLA README LIBERO evaluation section. Reads original HDF5 actions and casts each to float32 without converting delta pose to absolute pose. The local dataset_info.json reports moduleName LIBERO_Spatial.LIBERO_Spatial_dataset_builder; this supports the format match but does not pin the exact historical converter commit or collector version.

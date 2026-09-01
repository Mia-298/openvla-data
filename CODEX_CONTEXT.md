# Codex Project Context

This file stores concise cross-device task context.

## Current state

- Keywords: OpenVLA, LIBERO, usereval.py, closed-loop evaluation, SSHFS, Codex workspace
- Progress: Official LIBERO evaluation is complete. A custom prompt and custom lift success checker exist. The project is now opened from the shared mounted source.
- Next step: Learn and implement the complete observation -> inference -> action -> success-check loop manually.
- Summary: Use this mounted project source as the shared code location. Do not modify evaluation code directly when the user asks for teaching only.新的实例连接需要在文件资源管理器输入地址\\sshfs.r\root@connect.bjb1.seetacloud.com!10570\root\data\openvla_work\projects\OpenVLA
对应登陆指令ssh -p 10570 root@connect.bjb1.seetacloud.com
## 2026-08-24T08:02:17+08:00

- Keywords: Codex workspace, Z mount, project context, AGENTS.md
- Progress: Confirmed Codex is using Z:\root\data\openvla_work\projects\OpenVLA and created the project context capture files.
- Next step: Continue the OpenVLA closed-loop evaluation tutorial and record each substantive task result.
- Summary: Shared project source is now the active workspace. Context must remain concise and contain no secrets.

## 2026-08-24T08:12:51+08:00

- Keywords: OpenVLA, 协作约定, 分步指导
- Progress: 已记录：涉及 OpenVLA 工程项目时，不直接修改代码文件；先说明修改方案，再按步骤指导用户自行完成。
- Next step: 后续 OpenVLA 请求遵循分步教学流程，除非用户明确改变该约定。
- Summary: 用户要求记录 OpenVLA 项目协作规则：不得直接修改代码文件，必须一步步教用户如何修改。

## 2026-08-24T08:23:38+08:00

- Keywords: OpenVLA, LIBERO, 自定义prompt, custom_success, 评测闭环, LoRA微调
- Progress: 已完成LIBERO-Spatial基线推理、编写usereval.py自定义prompt，并用custom_success.py按目标碗上升高度判定拾取成功；已明确下一阶段先完善可重复评测和失败分析，再决定是否微调。
- Next step: 扩展custom_success.py以同时判定拾取与放置，批量测试多个任务初始状态并记录成功率、失败阶段和步数；根据失败模式选择prompt/控制改进或准备任务数据后进行LoRA微调。
- Summary: 用户已成功运行OpenVLA完成拾取任务，当前关注从自定义prompt和任务判定进入系统学习与下一步实验。

## 2026-08-24T08:27:12+08:00

- Keywords: OpenVLA学习, 推理流程, action tokenizer, norm_stats, RLDS, LoRA微调
- Progress: 用户明确目标是学习如何使用OpenVLA，而不是编写严谨评测；已完成一次任务运行，作为推理链路验证已足够。后续应学习图像/Prompt/动作Token/反归一化/环境执行流程，再按是否适配新任务决定是否微调。
- Next step: 按推理链路阅读eval.py、usereval.py及OpenVLA源码中的predict_action、ActionTokenizer和norm_stats；之后用最小实验对比原始模型与LIBERO微调模型，最后再学习RLDS数据格式和LoRA训练入口。
- Summary: 用户已成功运行OpenVLA完成一次任务，当前诉求是掌握OpenVLA的使用和原理，不以构建评测基准为目标。

## 2026-08-24T08:36:45+08:00

- Keywords: OpenVLA推理链路, processor, predict_action, ActionTokenizer, 动作token, norm_stats
- Progress: 已开始系统学习OpenVLA的第1和第2部分：结合usereval.py与eval.py拆解图像预处理、prompt构造、processor、predict_action、动作反归一化、夹爪转换和env.step；已解释ActionTokenizer将7维连续动作离散为动作token序列并由模型自回归预测，再解码为动作。
- Next step: 运行最小推理观察实验，打印processor输入的键、shape、dtype和predict_action输出；随后定位并阅读本机OpenVLA安装包中的ActionTokenizer与predict_action源码，核对动作token边界和norm_stats字段。
- Summary: 用户希望学习如何使用OpenVLA，当前正在学习推理流程和动作token化机制，而不是进行评测开发。

## 2026-08-24T08:47:41+08:00

- Keywords: OpenVLA, bitsandbytes, MatMul8bitLt, 8bit量化, bfloat16, float16
- Progress: 解释了usereval.py中load_in_8bit=True与bfloat16输入不匹配导致MatMul8bitLt每个推理循环提示将bfloat16转换为float16；该提示通常不是错误，但会造成重复日志和额外转换。
- Next step: 将8bit量化推理统一为float16，或在显存允许时关闭8bit并统一使用bfloat16；同时为推理设置model.eval()和torch.inference_mode()，观察日志和性能。
- Summary: 用户在运行OpenVLA循环推理时遇到MatMul8bitLt精度转换日志，当前需要理解量化与计算精度的关系。

## 2026-08-24T08:50:32+08:00

- Keywords: OpenVLA, Python, 关键字参数解包, kwargs, processor输入
- Progress: 解释了usereval.py中model.predict_action(**inputs)的Python语法：processor返回包含input_ids、attention_mask、pixel_values等命名字段的BatchFeature映射，**inputs将其解包为关键字参数传入模型。
- Next step: 继续学习processor输出字段与predict_action参数的对应关系，并用打印inputs.keys()和各字段shape的方式观察实际模型输入。
- Summary: 用户正在学习OpenVLA推理代码中的Python参数传递细节。

## 2026-08-24T08:54:55+08:00

- Keywords: OpenVLA, LIBERO动作适配, 真实机器人, ROS, JointState, 末端位姿, IK
- Progress: 解释了LIBERO动作后处理是仿真接口适配；现实机器人不应直接把OpenVLA输出发布为JointState。OpenVLA通常输出末端位姿增量(dx,dy,dz,旋转增量)和夹爪动作，需要根据机器人坐标系、单位、控制频率和夹爪接口转换为笛卡尔控制或经IK转换为关节目标。
- Next step: 学习真实机器人部署接口：确认模型动作空间和norm_stats，读取/joint_states与相机观测，将末端增量转换到机器人基座坐标系，并通过Cartesian controller或JointTrajectory发送命令，同时加入限位和急停。
- Summary: 用户开始学习OpenVLA从LIBERO仿真迁移到现实机器人时的动作接口和ROS控制方式。

## 2026-08-24T09:08:58+08:00

- Keywords: OpenVLA, unnorm_key, norm_stats, 动作反归一化, 机器人限位, 坐标系, RLDS, 真实机器人
- Progress: 澄清了unnorm_key只选择数据集动作归一化统计，不代表机器人活动范围、关节限位或运动学；当前usereval.py仅向模型传入图像和prompt，没有显式关节状态。真实机器人需要匹配动作统计、独立安全控制层，并在机器人差异明显时用真实示范数据进行适配/微调。
- Next step: 检查模型norm_stats.keys()及libero_spatial对应字段，学习q01/q99动作反归一化；设计真实机器人动作适配层，包含坐标系、单位、速度/工作空间/关节限位和IK或笛卡尔控制。
- Summary: 用户正在理解OpenVLA的动作归一化统计与真实机器人约束之间的区别。

## 2026-08-24T09:14:14+08:00

- Keywords: OpenVLA, 关节限位, URDF, IK, 安全控制, 相机视角, wrist camera, domain shift
- Progress: 解释了OpenVLA当前通常输出末端位姿增量而非关节角，因此可能产生导致IK越界的目标；训练数据能提供行为分布但不能替代硬安全约束。URDF通常由机器人模型/IK/控制器读取，不会被OpenVLA自动读取。相机从外部视角换为腕部视角会产生显著视觉分布变化，需匹配训练视角或使用相应数据微调。
- Next step: 学习真实机器人部署架构：用URDF和受约束IK实现动作安全层；核对训练/推理相机视角、分辨率、旋转、坐标系和遮挡情况；若采用腕部相机，收集同视角示范数据进行适配或微调。
- Summary: 用户正在理解OpenVLA输出安全性、URDF约束和训练/推理相机视角一致性。

## 2026-08-24T09:29:27+08:00

- Keywords: OpenVLA教程, LIBERO-Spatial LoRA, RLDS, SmolVLA真机, 新机器人, 新环境, 训练流程
- Progress: 核对教程与项目代码：LoRA训练使用openvla-7b和libero_spatial_no_noops RLDS数据，目标是LIBERO-Spatial适配；未实现新仿真环境、新机器人或OpenVLA真实机器人微调。教程另有SmolVLA真机脚本，包含相机、FA3连接、ServoJ、键盘示范采集、多任务prompt和异步部署，可学习真机工程流程但不等于OpenVLA训练。
- Next step: 按finetune.py学习OpenVLA训练链路：模型加载、LoRA、ActionTokenizer、RLDSBatchTransform、DataLoader、loss和checkpoint；再设计自己的机器人示范数据、动作定义和RLDS转换，作为新机器人微调入口。
- Summary: 用户询问复现教程中的LoRA究竟适配了什么，以及还可以学习哪些内容。

## 2026-08-24T09:36:55+08:00

- Keywords: LIBERO, 任务切换, 场景切换, BDDL, init_state, Panda, robots, OpenVLA
- Progress: 核对LIBERO源码：task_suite_name选择libero_spatial/object/goal/10/90，TASK_ID选择套件内BDDL任务和场景，INIT_STATE_ID选择同任务的预生成初始布置。OffScreenRenderEnv默认robots=['Panda']且使用OSC_POSE，API可传其他robosuite机器人，但现有init state、示范数据、相机分布和OpenVLA权重绑定Panda/LIBERO，不能直接无代价替换。
- Next step: 先打印suite.get_task_names()并切换已有suite/task/init state；切换suite时同步使用匹配checkpoint、unnorm_key和max_steps。若研究换机器人，则修改环境robots参数并重新生成初始状态、示范/RLDS数据和微调模型。
- Summary: 用户询问如何切换LIBERO任务、场景布置及机器人型号。

## 2026-08-24T09:40:49+08:00

- Keywords: OpenVLA, LIBERO Goal, unnorm_key, suite切换, checkpoint, task_id
- Progress: 澄清了仅修改predict_action的unnorm_key不会切换LIBERO任务；unnorm_key只选择动作统计。切换到libero_goal还需修改benchmark suite、匹配的模型checkpoint、TASK_ID/INIT_STATE_ID、MAX_STEPS、prompt和自定义success checker，并确认model.norm_stats包含libero_goal。
- Next step: 在usereval.py引入统一SUITE_NAME配置，用它同时创建suite和设置unnorm_key；打印任务列表选择TASK_ID，并改用匹配libero_goal的checkpoint。
- Summary: 用户询问将unnorm_key改为libero_goal是否足以切换LIBERO任务。

## 2026-08-24T09:44:12+08:00

- Keywords: OpenVLA, libero_goal, norm_stats, checkpoint, OMP_NUM_THREADS, EGL
- Progress: 诊断usereval报错：当前加载的openvla-7b-finetuned-libero-spatial checkpoint仅包含norm_stats['libero_spatial']，将unnorm_key改为libero_goal触发modeling_prismatic.py断言；OMP_NUM_THREADS无效提示和EGL析构异常是次要问题。
- Next step: 将unnorm_key恢复为libero_spatial以验证当前模型；若要运行libero_goal，准备包含libero_goal统计的匹配checkpoint并同步suite、task、prompt和任务步数；将OMP_NUM_THREADS设置为合法整数。
- Summary: 用户尝试切换到libero_goal时遇到norm_stats键不存在的报错。

## 2026-08-24T09:52:06+08:00

- Keywords: OpenVLA, SUITE_NAME, prompt, BDDL, TASK_ID, model checkpoint, norm_stats
- Progress: 实时查看了用户当前usereval.py：SUITE_NAME已正确用于benchmark suite和unnorm_key，但MODEL_PATH仍是openvla-7b-finetuned-libero-spatial，CUSTOM_PROMPT仍是黑碗拾取，TASK_ID和TARGET_OBJECT也仍按Spatial任务配置。澄清模型任务、仿真任务和checkpoint训练任务是三个不同层次。
- Next step: 当前Spatial运行可保持不变；切换同一suite内任务时修改TASK_ID/INIT_STATE_ID并使用task.language和匹配TARGET_OBJECT；切换Goal suite时必须同时准备包含libero_goal统计和能力的checkpoint，并同步任务prompt、success checker和步数。
- Summary: 用户已将SUITE_NAME用于环境套件与动作统计，正在理解为什么模型checkpoint和prompt仍影响任务读取与执行。

## 2026-08-24T09:57:40+08:00

- Keywords: OpenVLA, 模型与评测解耦, 跨套件评测, ENV_SUITE, MODEL_UNNORM_KEY, 零样本泛化
- Progress: 澄清模型与评测可以分开：当前Spatial微调模型可以尝试在Goal/Object环境上做跨套件零样本评测。之前的错误来自将环境套件名称和模型norm_stats键绑定为同一变量；应拆分ENV_SUITE与MODEL_UNNORM_KEY。跨套件运行不等于模型具备对应任务能力，需保持动作接口/相机/坐标系兼容并接受性能可能下降。
- Next step: 将usereval.py配置拆成ENV_SUITE='libero_goal'、MODEL_UNNORM_KEY='libero_spatial'进行跨套件实验；打印任务语言并确认动作统计存在，再单独处理Goal任务的TARGET_OBJECT和成功逻辑。
- Summary: 用户质疑模型和测评不应耦合，正在理解OpenVLA跨任务评测与动作统计元数据的区别。


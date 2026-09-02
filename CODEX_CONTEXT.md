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

## 2026-09-02T11:19:35+08:00

- Keywords: VLA学习路线, TODO定位, 项目文件
- Progress: 检查了工作区全部可见和隐藏文件及 TODO/路线关键词；未发现独立的 TODO 学习路线文件，已确认教程目录中的学习建议路线.pdf是普通PDF路线文档。
- Next step: 如果用户指的是工作区之外的TODO文件，请提供文件名或放入项目目录后再读取。
- Summary: 用户澄清所指是TODO形式的VLA学习计划，不是教程/学习建议路线.pdf。当前项目内未定位到该TODO文件。

## 2026-09-02T11:21:41+08:00

- Keywords: VLA学习路线, TODO定位, 双工作区检查
- Progress: 重新检查了主项目和新增的可访问工作区；主项目仍无独立TODO学习路线文件，新增工作区为空，关键词命中仅为上下文记录。
- Next step: 等待用户提供TODO文件名、路径或将文件放入项目后读取。
- Summary: 用户再次询问当前是否能看到TODO形式的VLA学习路线；截至本次检查仍未定位到该文件。

## 2026-09-02T11:23:19+08:00

- Keywords: VLA学习路线, Markdown文件, 文件同步
- Progress: 再次用find核对主项目和新增工作区；主项目仅有AGENTS.md、CODEX_CONTEXT.md、README.md，新增工作区没有文件，未发现用户所说的VLA TODO Markdown。
- Next step: 请确认Markdown文件是否已上传到当前项目，或提供其准确文件名/路径后继续读取。
- Summary: 用户认为新增文件中应有md文件；当前可访问文件系统中仍未出现该文件。

## 2026-09-02T11:25:13+08:00

- Keywords: VLA_8_WEEK_TODO.md, VLA八周计划, 外部学习目录
- Progress: 根据用户提供的路径读取了 /home/mia/data/ros_backup/ros/learn/md/markdown/vla/VLA_8_WEEK_TODO.md；确认其为VLA 8周学习与求职准备TODO，并读取了vla_learning_plan_chat.md和openvla学习.md的部分内容。
- Next step: 以VLA_8_WEEK_TODO.md作为当前学习主线，后续按周或按天推进并同步完成产物。
- Summary: 用户提供了外部目录的准确路径，已定位到此前未挂载工作区中的VLA学习TODO文件。

## 2026-09-02T11:27:44+08:00

- Keywords: VLA源文件夹, 优先扫描, 学习资料
- Progress: 用户明确要求：以后涉及VLA学习资料、TODO、Markdown或路线规划时，优先扫描 /home/mia/data/ros_backup/ros/learn/md/markdown/vla，再检查当前项目工作区。
- Next step: 后续VLA相关请求先检查源文件夹，再检查openvla-data工作区。
- Summary: 已确认VLA学习资料源目录及后续扫描优先级。

## 2026-09-02T11:38:17+08:00

- Keywords: OpenVLA, Day1, closed-loop eval, observation, processor, predict_action, action adapter, env.step
- Progress: 已核对 eval.py、usereval.py、utils.py、config.py 和本机 remote-code：确认闭环为观测图像与任务prompt进入processor，predict_action生成7个动作token并解码、按unnorm_key使用q01/q99反归一化，再经LIBERO夹爪适配后调用env.step；明确前6维是末端位姿增量语义，不能把eval.py中的旧注释当作7关节角，done也需与自定义success判定区分。
- Next step: 完成Day1产物：画出带shape、单位、坐标系和不确定项的流程图；下一步独立实现q01/q99动作归一化/反归一化及边界测试。
- Summary: 今天建立了OpenVLA-LIBERO评测的代码地图和动作语义边界：observation是环境状态字典中的相机图像，processor负责图像和prompt预处理，predict_action内部完成token生成、连续动作解码和反归一化，action adapter负责夹爪接口转换，env.step推进仿真并返回下一观测、奖励、终止信息。

## 2026-09-02T11:51:55+08:00

- Keywords: OpenVLA, predict_action源码, remote code, modeling_prismatic.py
- Progress: 已定位predict_action：eval.py第145行和usereval.py第125行是调用；实际定义在OpenVLA remote code的modeling_prismatic.py第506-536行，内部包含generate、动作token解码和q01/q99反归一化。
- Next step: 继续阅读modeling_prismatic.py中的predict_action，并定位ActionTokenizer/训练数据动作编码逻辑，核对token到连续动作的映射。
- Summary: 明确了项目脚本与模型实现的边界：eval脚本负责组织闭环，predict_action由trust_remote_code加载的OpenVLA模型类实现。

## 2026-09-02T11:58:49+08:00

- Keywords: OpenVLA, 当前项目, predict_action, 外部checkpoint, trust_remote_code
- Progress: 纠正源码路径：/home/mia/data/openvla-data中没有predict_action定义，eval.py/usereval.py仅负责调用；当前模型实现来自配置指向的外部/root checkpoint或其运行时缓存，之前引用的Trash旧备份路径不属于当前项目。
- Next step: 在实际运行OpenVLA的环境中用inspect.getsourcefile(model.predict_action)定位当前实例真实源码，再继续阅读实现。
- Summary: 已核实当前项目与模型源码边界，避免将旧备份目录误认为当前工程源码。

## 2026-09-02T12:00:00+08:00

- Keywords: OpenVLA, 当前模型目录, modeling_prismatic.py, predict_action
- Progress: 用户确认云端模型目录 ~/autodl-tmp/data/openvla_work/models/openvla-7b-finetuned-libero-spatial 内包含 modeling_prismatic.py；当前predict_action实现应直接从该本地模型目录加载，而非旧备份路径。
- Next step: 在云端模型目录中阅读 modeling_prismatic.py 的 predict_action，并继续追踪 ActionTokenizer/动作token映射及 norm_stats。
- Summary: 已根据用户提供的目录列表确认当前模型源码位置：模型目录内包含 modeling_prismatic.py、configuration_prismatic.py 和 processing_prismatic.py。

## 2026-09-02T12:08:18+08:00

- Keywords: OpenVLA, processor源码, PrismaticImageProcessor, PrismaticProcessor, predict_action, generate, 多模态embedding
- Progress: 已找到并阅读当前项目 models(backup)/processing_prismatic.py 与 modeling_prismatic.py：processor由图像处理器和tokenizer组成，输出pixel_values/input_ids/attention_mask；模型forward把视觉patch经过backbone和projector后插入BOS后，再交给语言模型；predict_action生成7个动作token、解码为[-1,1] bin中心，并按q01/q99反归一化返回numpy动作。
- Next step: 继续逐行阅读predict_action依赖的forward、prepare_inputs_for_generation和configuration_prismatic，完成processor输入shape与视觉token插入位置的验证；随后进入ActionTokenizer/训练标签编码。
- Summary: 当前项目的models(backup)已补齐源码：processing_prismatic负责图像缩放/letterbox/ToTensor/Normalize、文本tokenizer和BatchFeature组装；modeling_prismatic负责视觉特征提取、投影、插入语言模型、generate及动作token反解码。

## 2026-09-02T15:36:33+08:00

- Keywords: OpenVLA, get_action_dim, generate, 自回归生成, generated_ids, KV cache
- Progress: 已解释predict_action中的generated_ids调用：get_action_dim先校验unnorm_key并返回q01长度，用于决定生成动作token数量；generate是Transformers继承的自回归生成入口，首次forward融合视觉patch和文本，后续利用past_key_values缓存逐token生成；generated_ids包含原prompt和新动作token，predict_action截取末尾动作维度数量进行解码。
- Next step: 独立画出generate一次推理的时间序列：初始多模态forward、每轮logits选token、追加token、KV cache；再阅读forward和prepare_inputs_for_generation的参数流。
- Summary: 掌握了动作维度与token生成数量的关系，以及predict_action如何借助Transformers.generate完成动作token预测。

## 2026-09-02T15:38:12+08:00

- Keywords: OpenVLA, generate与forward, 自回归, past_key_values, KV cache
- Progress: 澄清generate不是一次forward：generate是高层自回归生成循环，生成7个动作token通常需要7次forward；首次forward处理完整多模态输入，后续forward通过past_key_values只处理新token并复用缓存。
- Next step: 结合prepare_inputs_for_generation逐步画出第1到第7个token的input_ids长度、past_key_values和pixel_values传递方式。
- Summary: 理解了高层generate调用与底层forward调用的区别，以及OpenVLA动作token生成中的KV cache机制。

## 2026-09-02T15:40:01+08:00

- Keywords: OpenVLA, LIBERO 7维动作, action token与动作维度, 自回归依赖, env.step
- Progress: 澄清7维动作的含义：7表示一个action向量的分量数量，不是7个env.step或7个独立控制动作；generate通常逐次预测7个token，每个token对应训练动作序列中的一个维度，后续token条件于前面token，最终组装成一个7维action并一次传入env.step。
- Next step: 阅读ActionTokenizer或数据变换源码，确认7个动作分量的确切顺序及每个连续值如何离散成token。
- Summary: 建立了动作维度、生成token数量、forward次数和环境控制步之间的区别。

## 2026-09-02T15:46:13+08:00

- Keywords: OpenVLA, 自回归token, logits, dx, 动作分量
- Progress: 澄清每次forward的输出：语言模型会为序列位置产生词表logits，但generate在推理时只使用最后位置来选择下一个token；第一个新token对应动作序列第一个分量如dx，后续token依次对应其他分量，并条件于图像、prompt和历史动作token，不会每次都重新输出完整7维动作。
- Next step: 在源码或最小例子中打印generate每轮的input_ids、logits形状和选出的token，验证第一个token与后续token的自回归关系。
- Summary: 区分了每轮forward的next-token预测、完整动作向量组装以及词表logits的概念。

## 2026-09-02T15:47:32+08:00

- Keywords: OpenVLA, generated_ids切片, predicted_action_token_ids, batch维, sequence维
- Progress: 已解释generated_ids[0, -get_action_dim(unnorm_key):].cpu().numpy()：先取batch中的第0条序列，再取序列末尾action_dim个新生成token，移到CPU并转为NumPy；结果是动作token id数组而非连续动作，后续还要经过bin解码和q01/q99反归一化。
- Next step: 继续逐行解释discretized_actions、normalized_actions和actions三步，手算一个token到连续动作的示例。
- Summary: 掌握了generated_ids中prompt token与动作token的切分方式，以及PyTorch到NumPy的转换原因。

## 2026-09-02T15:53:06+08:00

- Keywords: OpenVLA, discretized_actions, token id反解码, bin索引, np.clip
- Progress: 已解释predict_action中两步离散动作解码：vocab_size-token_id利用OpenVLA动作token的反向编码得到动作编号；减1转换为从0开始的bin索引；np.clip将索引限制在bin_centers的合法范围，避免异常token造成越界。
- Next step: 继续解释bin_centers查表得到normalized_actions，以及mask/q01/q99反归一化如何恢复实际动作值。
- Summary: 理解了动作token id到离散bin索引的映射和边界保护。

## 2026-09-02T15:57:07+08:00

- Keywords: OpenVLA, cpu.numpy, token id与连续动作, 数据类型转换, 语义转换
- Progress: 澄清.cpu().numpy()只完成设备/数据类型转换：从GPU上的torch LongTensor切片并变成CPU上的NumPy整数数组，数值仍是动作token id；后续vocab_size减法、bin查表和q01/q99反归一化才完成动作语义解码。
- Next step: 继续区分动作解码中的三类变化：张量容器转换、token编号到bin索引、bin索引到连续控制值。
- Summary: 理解了数据结构转换不等于动作数值语义转换。

## 2026-09-02T15:58:32+08:00

- Keywords: OpenVLA, normalized_actions, bin_centers, NumPy高级索引, [-1,1]
- Progress: 已解释normalized_actions = bin_centers[discretized_actions]：将每个动作分量的离散bin索引作为数组索引，查出对应bin中心浮点值；输入输出形状通常都是[7]，结果位于[-1,1]，尚未经过q01/q99恢复物理动作尺度。
- Next step: 继续解释q01/q99反归一化公式及mask分支，明确哪些维度会被恢复到数据集动作范围。
- Summary: 理解了离散bin索引到归一化连续动作值的查表过程。

## 2026-09-02T16:00:02+08:00

- Keywords: OpenVLA, q01, q99, mask, np.where, 动作反归一化
- Progress: 已解释predict_action末段：get_action_stats按unnorm_key取得动作统计；mask缺省时全部维度参与反归一化；q01/q99转为数组作为每维low/high；线性公式将[-1,1]映射到[q01,q99]，np.where逐维选择缩放值或保留normalized_actions。
- Next step: 读取模型配置中的实际libero_spatial action统计，手算一个维度的反归一化，并区分模型输出动作与LIBERO夹爪adapter。
- Summary: 掌握了OpenVLA基于分位数统计的动作反归一化和mask逐维控制。

## 2026-09-02T16:03:39+08:00

- Keywords: OpenVLA, unnorm_key, 数据集统计, q01/q99, 动作分布, 机器人型号
- Progress: 澄清unnorm_key不是机械臂型号，而是model.norm_stats中的数据集/动作统计键，用于选择动作维度和q01/q99反归一化；它不切换checkpoint、任务或机器人。模型输出受离散bin和统计区间约束到数值范围，但不是训练动作集合的查表，可能生成训练中未精确出现的组合或错误动作，q01/q99也不是安全限位。
- Next step: 阅读训练数据动作归一化和ActionTokenizer编码过程，确认训练时动作如何进入bin，以及统计键、环境动作空间和机器人控制器之间的边界。
- Summary: 理解了unnorm_key的元数据作用与模型输出分布学习、硬范围约束、机器人安全约束之间的区别。

## 2026-09-02T16:14:40+08:00

- Keywords: OpenVLA, dataset_statistics, q01/q99, RLDSDataset, ActionTokenizer, 训练数据准备
- Progress: 已说明q01/q99/mask通常在训练前或数据加载阶段由RLDSDataset统计动作数据得到，训练时用于动作归一化和ActionTokenizer编码，保存checkpoint时由save_dataset_statistics写入；predict_action只读取统计并反归一化。
- Next step: 基于当前LIBERO dataset_statistics.json手算一个位置维度和gripper维度的归一化/反归一化，随后阅读ActionTokenizer源码确认训练侧编码细节。
- Summary: 建立了动作统计量从数据集准备到训练编码、checkpoint保存、推理反归一化的完整链路。

## 2026-09-02T16:15:34+08:00

- Keywords: OpenVLA, action norm mask, 反归一化开关, gripper, attention_mask区分
- Progress: 解释action_norm_stats中的mask：它是逐动作维度的反归一化开关，不是attention_mask或loss mask；True时用q01/q99恢复尺度，False时保留normalized_actions；若缺失则创建与q01同形状的全True数组。当前LIBERO通常前6维True、夹爪维False。
- Next step: 继续结合当前dataset_statistics.json手算mask为True/False的两个维度，理解夹爪为何保留原范围并在eval.py额外适配。
- Summary: 区分了动作反归一化mask与文本注意力mask及训练loss mask，并理解其逐维控制作用。

## 2026-09-02T16:17:19+08:00

- Keywords: OpenVLA, q01/q99, action_high/action_low, 统计范围, 动作安全限位
- Progress: 澄清action_high/action_low：从action统计中读取q99和q01并转成NumPy向量，分别作为各动作维度反归一化映射的上/下端点；mask为True时[-1,1]映射到[q01,q99]。它是数据分布统计范围和解码范围，不是机器人硬安全限位。
- Next step: 结合实际libero_spatial的q01/q99数组计算一个dx和旋转维度的反归一化结果，并继续区分统计范围、控制器输入范围和安全约束。
- Summary: 理解了q01/q99在反归一化中的端点作用及其与物理限位的区别。

## 2026-09-02T16:23:52+08:00

- Keywords: Day1复盘, eval学习记录, processor, predict_action, action contract, Day2准备
- Progress: 阅读了用户真正的记录 /home/mia/data/Note/Mia/vla/openvla/eval学习.md：predict_action的token截取、bin映射、bin_centers、mask和q01/q99已理解；但Day1完整验收仍缺processor内部步骤与输入shape、action adapter/env.step、done/success/MAX_STEPS区别、单位/坐标系清单。
- Next step: 先补齐Day1代码地图：记录processor输入输出contract、7维action到env.step的夹爪适配和未知项；完成后开始Day2，独立实现q01/q99归一化、裁剪、反归一化和7维batch测试。
- Summary: Day1核心predict_action阅读基本达标，但整套eval流程记录尚未完整；不修改用户学习记录，只给出补漏清单。

## 2026-09-02T16:41:37+08:00

- Keywords: OpenVLA, processor输入, prompt字符串, input_ids输出, 图文输入
- Progress: 澄清processor接口：eval.py中processor的文本输入就是构造出的prompt字符串，图像是第二个输入；input_ids和attention_mask是processor对prompt tokenizer后的输出，不是调用processor时直接传入的原始输入。
- Next step: 在Day1记录中补充processor的输入/输出术语和shape，避免混淆prompt、token id与模型输入BatchFeature。
- Summary: 区分了processor原始输入(prompt字符串和图像)与处理后输出(input_ids、attention_mask、pixel_values)。

## 2026-09-02T16:43:48+08:00

- Keywords: OpenVLA, PrismaticProcessor.__call__, tokenizer, input_ids, attention_mask
- Progress: 定位input_ids/attention_mask源码：PrismaticProcessor.__call__第213-215行调用self.tokenizer(text, ...)，返回text_inputs；第221行将text_inputs与pixel_values合并为BatchFeature。图像处理在第212行。
- Next step: 继续阅读self.tokenizer的Transformers实现和模型目录tokenizer.json/tokenizer.model，理解字符串如何切分成token id及attention mask。
- Summary: 已精确定位prompt字符串到input_ids/attention_mask的源码调用位置。

## 2026-09-02T16:48:25+08:00

- Keywords: OpenVLA, AutoProcessor, from_pretrained, PrismaticProcessor, trust_remote_code, 工厂类
- Progress: 澄清AutoProcessor关系：Transformers中的AutoProcessor.from_pretrained是自动加载器，读取模型目录配置并在trust_remote_code=True时加载本地/远程自定义PrismaticProcessor；变量processor是PrismaticProcessor实例，其__call__再调用self.tokenizer和self.image_processor。
- Next step: 阅读模型目录preprocessor_config.json及AutoProcessor加载结果，打印type(processor)、type(processor.tokenizer)、type(processor.image_processor)验证类实例。
- Summary: 区分了Transformers的AutoProcessor加载入口与OpenVLA具体PrismaticProcessor实现。

## 2026-09-02T16:49:49+08:00

- Keywords: OpenVLA, __call__, PrismaticProcessor, Python可调用对象, image_processor, tokenizer
- Progress: 确认processor执行入口：processor(prompt, image)通过Python可调用对象机制触发PrismaticProcessor.__call__；其内部image_processor(images, ...)触发PrismaticImageProcessor.__call__并进入preprocess，tokenizer(text, ...)触发Hugging Face tokenizer的__call__。
- Next step: 继续区分processor.__call__、model.forward、model.generate和predict_action之间的调用关系。
- Summary: 理解了processor括号调用实际对应__call__方法及其内部嵌套调用。

## 2026-09-02T16:52:44+08:00

- Keywords: OpenVLA, PrismaticProcessor, BatchFeature, BatchEncoding, batch对齐, pixel_values, input_ids
- Progress: 已解释PrismaticProcessor.__call__的组装逻辑：image_processor返回并提取pixel_values，tokenizer返回text_inputs；通过比较两者shape[0]确保每个文本和图像按batch一一对应；最后用字典展开合并文本字段与pixel_values，封装为可.to(device,dtype)的BatchFeature。
- Next step: 继续阅读BatchFeature.to和model.forward接收input_ids/attention_mask/pixel_values的参数流，串起processor输出到视觉backbone和语言模型。
- Summary: 理解了图像/文本双分支预处理结果的batch校验和统一封装。

## 2026-09-02T17:06:23+08:00

- Keywords: OpenVLA, attention_mask, input_ids, padding, visual patch mask, causal attention
- Progress: 解释了attention_mask与input_ids的关系：两者按序列位置一一对应、shape相同；input_ids承载token编号，attention_mask只标记有效位置(1)和padding(0)，不承载文本语义。Prismatic forward插入视觉patch后为视觉位置创建全1 mask并与文本mask拼接。
- Next step: 继续阅读attention_mask在语言模型注意力中的作用，并区分padding mask、causal mask和视觉patch mask。
- Summary: 理解了token内容与有效性标记的区别，以及多模态序列拼接后的mask扩展。

## 2026-09-02T17:09:58+08:00

- Keywords: OpenVLA, input_ids, token id, token编码, embedding
- Progress: 澄清input_ids：它存储token对应的词表整数ID/编码，不存储token字符串本身；tokenizer可用convert_ids_to_tokens或decode还原文本片段，模型随后通过input embedding把ID查表为向量。
- Next step: 继续理解tokenizer的词表映射和model.get_input_embeddings()(input_ids)如何将整数ID转换为语言模型embedding。
- Summary: 区分了token文本片段、token id编码和embedding向量。

## 2026-09-02T17:14:34+08:00

- Keywords: Day1复盘, eval学习笔记, processor, predict_action, action adapter, Day2准入
- Progress: 复查更新后的 /home/mia/data/Note/Mia/vla/openvla/eval学习.md：processor和predict_action主干已基本正确；仍需修正unnorm_key表述、generate通常7次但可能提前结束、action可能并非全部反归一化，并补充processor实际类型/shape、夹爪adapter/env.step、done与success/MAX_STEPS及流程图。
- Next step: 先补齐4个Day1最小修正项后进入Day2：action contract、unnorm_key定义、generate表述、done/success区别；Day2独立完成q01/q99归一化/裁剪/反归一化与7维batch测试。
- Summary: 更新学习笔记已覆盖predict_action核心解码链路，但尚未完全满足Day1完整eval代码地图的验收标准。

## 2026-09-02T17:22:25+08:00

- Keywords: Day1验收通过, eval学习笔记, Day2开始, get_action_dim, done, action adapter
- Progress: 复查最新eval学习笔记：已补齐processor输入输出shape、token解码、unnorm_key和主要流程，达到可以进入Day2的程度；仍建议修正get_action_dim表述为动作维度n、generate生成n个token，说明done是环境终止标志且success可由自定义checker判定，并补一个ASCII流程图及action adapter细节。
- Next step: 正式开始Day2：独立实现q01/q99归一化、裁剪、反归一化；先处理ndarray、切片、广播、dtype和shape，再写7维动作与batch测试。
- Summary: Day1学习记录已基本达标，允许进入Day2；剩余问题是表达和流程图收尾，不影响开始NumPy动作归一化任务。

## 2026-09-02T17:31:30+08:00

- Keywords: Day2开始, NumPy动作归一化, q01/q99, np.clip, batch shape
- Progress: 已开始第2天：明确任务不是简单调用np.array，而是独立实现逐维q01/q99归一化、越界裁剪和反归一化函数；人工数字只用于测试，需覆盖7维、batch、越界和q01=q99。
- Next step: 用户独立编写numpy_action_norm.py：先实现clip、normalize、unnormalize及断言测试，再提交代码进行检查。
- Summary: Day1基本验收通过，正式进入Day2 NumPy动作归一化实践。

## 2026-09-02T17:34:55+08:00

- Keywords: Day2, q01, q99, 分位数, percentile
- Progress: 明确q01是动作数据第1百分位(q=0.01)，q99是第99百分位(q=0.99)，两者按每个动作维度独立统计，用作归一化映射端点而非机器人硬限位。
- Next step: 在numpy_action_norm.py中用人工动作数组计算或指定q01/q99，并验证边界与越界裁剪。
- Summary: 理解了q01/q99的统计学含义及其在动作归一化中的作用。

## 2026-09-02T17:38:32+08:00

- Keywords: Codex上下文记录, AGENTS.md, 跨设备同步, OpenVLA Day2
- Progress: 已读取当前项目AGENTS.md：要求每次实质性请求完成后更新CODEX_CONTEXT.md，记录需简洁且不得包含密码、token、私钥或模型凭据；VLA源资料目录未发现独立AGENTS.md。用户明确要求后续持续记录对话，当前学习已进入Day2的NumPy动作归一化准备阶段。
- Next step: 后续每次OpenVLA/VLA学习实质性对话完成后，继续用update_codex_context.py记录关键词、完成内容、开放问题和下一步；当前下一步仍是独立编写numpy_action_norm.py并完成q01/q99、裁剪、反归一化、7维与batch测试。
- Summary: 确认了项目级上下文记录规则和跨设备读取目标，并记录了用户要求持续保存学习对话上下文。


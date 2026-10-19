import numpy as np
import tensorflow as tf

# theta = 0.0
# # np.exp(-theta)=(e^{-theta})
# p_to_b = 1.0 / (1.0 + np.exp(-theta))
# p_to_g = 1.0 - p_to_b

# learning_rate = 0.1
# -------------------------------------
# 根据已知路径更新梯度
# # gradient=期望回报对 theta 的梯度，
# # 因为dp/dtheta = p（1-p）
# # 假设回报b = 2.5 回报g = 2，gradient = d(2.5*p+2*(1-p))/dp*dp/dtheta = 0.5*p（1-p）
# gradient = 0.5 * p_to_b * (1.0 - p_to_b)

# # theta朝梯度方向更新，寻找期望最高时的theta
# theta = theta + learning_rate * gradient
# p_to_b = 1.0 / (1.0 + np.exp(-theta))
# p_to_g = 1.0 - p_to_b

# print("更新后的 theta：", theta)
# print("先到 B 的概率：", p_to_b)
# print("直接到 G 的概率：", p_to_g)
# -------------------------------------
# 随机采样更新梯度
rng = np.random.default_rng()
# for i in range (100):
    
#     # 按照策略概率抽取动作
#     action = rng.choice(
#         ["to_b", "to_g"],
#         p=[p_to_b, p_to_g],
#     )

#     if action == "to_b":
#         episode_return = 2.5
#         log_prob_gradient = 1.0 - p_to_b
        
#     else:
#         episode_return = 2.0
#         log_prob_gradient = -p_to_b

#     print("这次选择的动作：", action)
#     print("这次实际回报：", episode_return)

#     # 估计梯度
#     gradient = episode_return * log_prob_gradient
#     theta = theta + learning_rate * gradient

#     p_to_b = 1.0 / (1.0 + np.exp(-theta))
#     p_to_g = 1.0 - p_to_b

#     print("这次的样本梯度：", gradient)
#     print("更新后的 theta：", theta)
#     print("更新后先到 B 的概率：", p_to_b)

# -------------------------------------
# # 固定一条采样结果，用于对照之前的手写计算
# theta = tf.Variable(0.0)
# learning_rate = 0.1


# action = "to_b"
# episode_return = 2.5

# with tf.GradientTape() as tape:
#     # 激活函数，在tf中需要用TensorFlow 计算图，如果只是写numpy运算会求梯度失败
#     # 只有四则运算可以直接计算 其他都需要tf算子
#     # 也可以写成p_to_b = 1.0 / (1.0 + tf.exp(-theta))

#     p_to_b = tf.sigmoid(theta)

#     if action == "to_b":
#         chosen_probability = p_to_b
#     else:
#         chosen_probability = 1.0 - p_to_b

#     objective = episode_return * tf.math.log(chosen_probability)

# gradient = tape.gradient(objective, theta)

# # 最大化目标，所以沿梯度方向加
# theta.assign_add(learning_rate * gradient)

# print("样本梯度：", gradient.numpy())
# print("更新后的 theta：", theta.numpy())
# ------------------------------------------
# 随机采样自动计算梯度

# import tensorflow as tf
# # 1. 定义策略网络：输入状态s(一维向量)，输出1个logit（二动作）


# # ====== 采样得到的一条轨迹数据（现在多了状态s！）======
# # 假设状态s是一个一维观测向量，比如 [0.8]
# state = tf.constant([[0.8]], dtype=tf.float32)

# # 创建一个全连接层，用于表示y=wx+b，state就是输入，
# # dense默认使用随机方式初始化权重 w，因此初始logit可能不同导致p不同
# dense1 = tf.keras.layers.Dense(1, activation=None)
# # critic依旧是一个全连接层，输入state，输出预测期望
# critic = tf.keras.layers.Dense(1, activation=None)
# # 参数优化器
# critic_optimizer = tf.keras.optimizers.SGD(learning_rate=0.1)
# actor_optimizer = tf.keras.optimizers.SGD(learning_rate=0.1)
# for i in range(100):
#     # persistent=True允许多次求导
#     with tf.GradientTape(persistent=True) as tape:
#         # logit承担原来theta的作用：作为sigmoid的输入
#         logit = dense1(state)
#         p_to_b = tf.sigmoid(logit)
#         p = p_to_b.numpy().item()

#         action = rng.choice(
#                 ["to_b", "to_g"],
#                 p=[p, 1-p],
#             )
#         if action == "to_b":
#             episode_return = 2.5
#             chosen_probability = p_to_b
#         else:
#             episode_return = 2.0
#             chosen_probability = 1.0 - p_to_b
#         # 训练第一个参数：回报期望
#         predicted_value = critic(state)
#         print("预测回报：", predicted_value.numpy())

#         error = predicted_value - episode_return
#         # 依旧误差的均方
#         critic_loss = tf.reduce_mean(tf.square(error))

#         # 第二步训练概率
        
#         # PG目标：最大化 R * log π(a|s)，所以loss取负做最小化
#         advantage = tf.stop_gradient(episode_return - predicted_value)
#         actor_loss = -tf.reduce_mean(
#             advantage * tf.math.log(chosen_probability)
#         )
#     # 求梯度：对网络全部参数求导，dense1.trainable_variables就是取出参数w和b       
#     critic_grads = tape.gradient(critic_loss, critic.trainable_variables)
#     actor_grads = tape.gradient(actor_loss, dense1.trainable_variables)
#     del tape
#     # 优化器更新网络权重（更新方向为梯度的反向，找最小值） zip可以把n个列表的每个成员逐一配对
#     critic_optimizer.apply_gradients(zip(critic_grads, critic.trainable_variables))
#     predicted_value = critic(state)
#     print("预测回报：", predicted_value.numpy())


#     actor_optimizer.apply_gradients(zip(actor_grads, dense1.trainable_variables))
#     updated_p_to_b = tf.sigmoid(dense1(state))
#     print("梯度列表：", [g.numpy() for g in actor_grads],"动作：", action)
#     print("网络输出p_to_b：", updated_p_to_b.numpy())


# ------------------------------------------

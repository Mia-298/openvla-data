import tensorflow as tf
import math

# 第一个网络，输入state，action，输出q
q_net = tf.keras.Sequential([
    tf.keras.layers.Dense(16, activation="relu"),
    tf.keras.layers.Dense(1, activation=None),
])

target_position = 1.0
# 这里定义奖励和目标距离成二次函数的关系，让动作偏小和偏大奖励都较低，因此训练时最好用二层网络



q_optimizer = tf.keras.optimizers.SGD(learning_rate=0.1)

# --------
# 新的随机 Actor：输出两个数
stochastic_actor = tf.keras.Sequential([
    tf.keras.layers.Dense(16, activation="relu"),
    tf.keras.layers.Dense(2, activation=None),
])
actor_optimizer = tf.keras.optimizers.SGD(
    learning_rate=0.01
)
sample_state = tf.constant([[0.8]], dtype=tf.float32)
for step in range(1000):
    with tf.GradientTape(persistent=True) as tape:
        batch_state = tf.repeat(sample_state, repeats=5, axis=0)
        # 输出 shape 为 (1, 2)
        outputs = stochastic_actor(batch_state)
    
        # 保留二维形状，二者 shape 都为 (1, 1)
        mu = outputs[:, 0:1]
        log_std = outputs[:, 1:2]
    
        # 限制数值范围，避免初学练习中标准差过大或过小
        log_std = tf.clip_by_value(log_std, -5.0, 2.0)
    
        # 从对数标准差得到标准差
        std = tf.exp(log_std)
        epsilon = tf.random.normal(shape=tf.shape(mu))
        raw_action = mu + std * epsilon
    
        # 每个动作的对数概率密度
        raw_log_prob = (
            -0.5 * tf.square((raw_action - mu) / std)
            - log_std
            - 0.5 * math.log(2.0 * math.pi)
        )
        print("原始采样值：", raw_action.numpy())
        print("高斯对数密度：", raw_log_prob.numpy())
    
        # 最终动作采样值
        action = tf.tanh(raw_action)
    
        # 最终动作的对数密度
        log_prob = (
            raw_log_prob
            - tf.math.log(1.0 - tf.square(action) + 1e-6)
        )
        # 用这批动作估计熵
        entropy_estimate = -tf.reduce_mean(log_prob)
    
        # 五个动作直接一起input得到评分
        q_inputs = tf.concat(
            [batch_state, action],
            axis=1,
        )
        sampled_q = q_net(q_inputs)
        # 暂时手动固定熵权重
        alpha = 0.1
    
        stochastic_actor_loss = tf.reduce_mean(
            alpha * log_prob - sampled_q
        )
        state_action = tf.concat([batch_state, action], axis=1)
        predicted_q = q_net(state_action)
        next_state = batch_state+action
        reward = 1.0 - tf.square(next_state - target_position)
        # 一步结束：训练目标就是这次奖励，而且取平均仍然能保留各分量梯度
        q_loss = tf.reduce_mean(tf.square(predicted_q - reward))

    q_grads = tape.gradient(q_loss, q_net.trainable_variables)
    q_optimizer.apply_gradients(
        zip(q_grads, q_net.trainable_variables)
    )
    # 只求随机 Actor 参数的梯度
    stochastic_grads = tape.gradient(
        stochastic_actor_loss,
        stochastic_actor.trainable_variables,
    )


    actor_optimizer.apply_gradients(
        zip(
            stochastic_grads,
            stochastic_actor.trainable_variables,
        )
    )

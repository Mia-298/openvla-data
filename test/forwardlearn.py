import torch

device = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)
x = torch.tensor(
    3.0,
    device=device,
    requires_grad=True
)
# tensor可以放到 GPU 上计算
# 可以记录计算过程
# 3. 可以自动计算梯度
# 4. 可以直接输入 PyTorch 神经网络

print(x)
print(x.shape)
print(x.dtype)
print(x.device)#cpu代表当前数据在cpu进行处理?


x = x.to(device)
print(x.device)#cpu代表当前数据在cpu
y = x*x
y.backward()
# 反向求导，dy/dx = 2x=6，存储到x.gard

print(x.grad)

x1 = torch.tensor(
    3.0,
    device=device,
    requires_grad=True
)

x2 = torch.tensor(
    1.0,
    device=device,
    requires_grad=True
)

z = x1*x1+2*x2
z.backward()
print(x1.grad)
print(x2.grad)
# 分别求偏导

x = torch.tensor([1., 2., 3., 4.])
y_true = torch.tensor([3., 5., 7., 9.])

w = torch.tensor(0., requires_grad=True)
b = torch.tensor(0., requires_grad=True)

optimizer = torch.optim.SGD([w, b], lr=0.01)
# SGD优化器，wb表示要训练、要自动更新的参数，
# 优化器会读取：w.grad，b.grad，然后修改 w 和 b
# 新参数 = 旧参数 - 学习率 × 梯度 
for epoch in range(1000):
    # 这里y_pred计算完就固定了不会自动更新
    
    y_pred = w * x + b
    # 计算预测值和真实值的均方差
    loss = ((y_pred - y_true) ** 2).mean()
    # 3. 清空上一次的梯度
    optimizer.zero_grad()
    # 反向传播（也就是计算参数的梯度)
    loss.backward()
    # 寻找最优解，感觉这里是类似工程优化的某个算法
    optimizer.step()
    # 更新参数修改后的loss
    loss = ((w * x + b - y_true) ** 2).mean()
    if epoch % 100 == 0:
        print(
            epoch,
            loss.item(),
            w.item(),
            b.item()
        )
print("最终参数：")
print("w =", w.item())
print("b =", b.item())
print(y_pred)
import numpy as np
import math
import torch
Q = torch.tensor([[1,0],
              [1,1]])
# Q的每行代表每个元素，列数代表纬度，比如这里Q1 = (1,0)2维度
K = torch.tensor([[1,0],
              [0,1]])
# Q⋅K的转置
scores = Q@K.T
print(scores)
# softmax：因为点积会因为矩阵的n增加而变大，所以要除以shape，也就是Q的维度（列）
d_k = Q.shape[-1]

softed_score = scores/math.sqrt(d_k)
print(softed_score)
# 注意力分配比例：每行每一行单独归一化，每行和为1
attention_weights = torch.softmax(
    softed_score,
    dim=-1
)
print(attention_weights)
# 分配之前可以设置某个Q不看某个K，设置mask
mask = torch.tensor([[1,0],
              [1,1]])
# 意思是Q1只看K1,Q2两个都看
masked_scores = softed_score.masked_fill(
    mask == 0,
    float("-inf")
)
print(masked_scores)
attention_weights = torch.softmax(
    masked_scores,
    dim=-1
)
print(attention_weights)
V = torch.tensor([[10,0],[0,10]])
# 每个 Query 根据相关性权重，从所有 Value 中汇总出来的新特征
output = attention_weights@V
print(output)
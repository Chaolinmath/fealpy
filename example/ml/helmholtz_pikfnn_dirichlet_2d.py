import time

from matplotlib import pyplot as plt
from scipy.linalg import solve
import torch
import torch.nn as nn
from torch.special import bessel_j0

from fealpy.ml.modules import Solution
from uniformly_placed import sample_points_on_square
from fealpy.ml.sampler import ISampler

#方程形式

"""

    \Delta u(x,y) + k^2 * u(x,y) = 0 ,                            (x,y)\in \Omega
    u(x,y) = \sin(\sqrt{k^2/2} * x + \sqrt{k^2/2} * y) ,         (x,y)\in \partial\Omega

"""

#超参数(配置点个数、源点个数、波数)

num_of_col_bd = 5000
num_of_source = 5000
k = torch.tensor(1000, dtype=torch.float64)

#PIKF层

class PIKF_layer(nn.Module):
    def __init__(self, source_nodes: torch.Tensor) -> None:
        super().__init__()
        self.source_nodes = source_nodes

    def kernel_func(self, input: torch.Tensor) -> torch.Tensor:
        a = input[:, None, :] - self.source_nodes[None, :, :]
        r = torch.sqrt((a[..., 0:1]**2 + a[..., 1:2]**2).view(input.shape[0], -1))
        val = bessel_j0(k* r)/(2 * torch.pi)
        return val

    def forward(self, p: torch.Tensor) -> torch.Tensor:

        return self.kernel_func(p)
    
source_nodes = sample_points_on_square(-2.5, 2.5, num_of_source)
pikf_layer = PIKF_layer(source_nodes)
net_PIKFNN = nn.Sequential(
                           pikf_layer,
                           nn.Linear(num_of_source, 1, dtype=torch.float64, bias=False)
                           )

s = Solution(net_PIKFNN)

#真解及边界条件

def solution(p:torch.Tensor) -> torch.Tensor:

    x = p[...,0:1]
    y = p[...,1:2]
    return torch.sin(torch.sqrt(k**2/2) * x + torch.sqrt(k**2/2) * y)

def dirichletBC(p:torch.Tensor) -> torch.Tensor:
    return solution(p)

# 更新网络参数

start_time = time.time()

col_bd = sample_points_on_square(-1, 1, num_of_col_bd)

A = pikf_layer.kernel_func(col_bd).detach().numpy()
b = dirichletBC(col_bd).detach().numpy()
alpha = solve(A, b)
net_PIKFNN[1].weight.data = torch.from_numpy(alpha).T
del alpha 

end_time = time.time()     
time_of_computation = end_time - start_time   
print("计算时间为：", time_of_computation, "秒")

#计算L2相对误差
test_nodes_sampler = ISampler(
    1000, [[-1, 1], [-1, 1]], requires_grad=True)
test_nodes = test_nodes_sampler.run()

L2_error = torch.sqrt(
            torch.sum((s(test_nodes) - solution(test_nodes))**2, dim = 0)\
            /torch.sum(solution(test_nodes)**2, dim = 0)
          )
print(f"L2_error: {L2_error}")

#可视化数值解、真解以及两者偏差

fig_1 = plt.figure()
fig_2 = plt.figure()
fig_3 = plt.figure()

axes = fig_1.add_subplot()
qm = Solution(solution).add_pcolor(axes, box=[-1, 1, -1, 1], nums=[300, 300],cmap = 'tab20')
axes.set_xlabel('x')
axes.set_ylabel('y')
axes.set_title('u')
fig_1.colorbar(qm)

axes = fig_2.add_subplot()
qm = s.add_pcolor(axes, box=[-1, 1, -1, 1], nums=[300, 300],cmap='tab20')
axes.set_xlabel('x')
axes.set_ylabel('y')
axes.set_title('u_PIKFNN')
fig_2.colorbar(qm)

axes = fig_3.add_subplot()
qm = s.diff(solution).add_pcolor(axes, box=[-1, 1, -1, 1], nums=[300, 300])
axes.set_xlabel('x')
axes.set_ylabel('y')
axes.set_title('diff')
fig_3.colorbar(qm)

plt.show()


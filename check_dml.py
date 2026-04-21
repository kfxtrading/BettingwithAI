import torch
import torch_directml as dml

d = dml.device()
print("DirectML device:", d)
print("device_name:", dml.device_name(0))
print("device_count:", dml.device_count())
x = torch.ones(2, 3, device=d)
y = x * 2 + 1
print("tensor on dml:", y.device, "sum:", y.sum().item())

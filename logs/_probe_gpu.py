import torch
print("torch", torch.__version__)
print("cuda_available", torch.cuda.is_available())
print("device_count", torch.cuda.device_count())
if torch.cuda.is_available():
    print("name", torch.cuda.get_device_name(0))
try:
    import torch_directml as dml
    print("dml_devices", dml.device_count())
    print("dml_device0", dml.device_name(0))
except Exception as exc:
    print("no directml:", exc)

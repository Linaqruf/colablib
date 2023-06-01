import subprocess
import sys
from .cprint import cprint

def is_google_colab():
    try:
        import google.colab
        return True
    except:
        return False

def get_python_version():
    try:
        return sys.version
    except Exception as e:
        cprint("Failed to retrieve Python version:", str(e), color="greem")
        return None

def get_torch_version():
    try: 
        import torch
    except ImportError:
        raise ImportError("No torch module found. Please make sure PyTorch is installed.")
        
    try:
        return torch.__version__
    except Exception as e:
        cprint("Failed to retrieve PyTorch version:", str(e), color="greem")
        return None
    
def get_gpu_info(get_gpu_name=False):
    command = ["nvidia-smi", "--query-gpu=gpu_name", "--format=csv"]
    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode == 0:
        gpu_info = result.stdout.strip()
        if get_gpu_name:
            if 'name' in gpu_info:
                return gpu_info[5:]
        return gpu_info
    else:
        error_message = result.stderr.strip()
        if "NVIDIA-SMI has failed" in error_message and "No devices were found" in error_message:
            if is_google_colab():
                from google.colab import runtime
                runtime.unassign()
            raise RuntimeError("No GPU found. Unassigned GPU in Google Colab.")
        else:
            raise RuntimeError(f"Command execution failed with error: {error_message}")

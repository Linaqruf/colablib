import os
import math
import re
import requests
import subprocess
import sys
import time 
from urllib.parse import urlparse, unquote
from ..colored_print import cprint

def is_google_colab():
    """
    Checks if the current environment is Google Colab.

    Returns:
        bool: True if it's Google Colab, False otherwise.
    """
    try:
        import google.colab
        return True
    except ImportError:
        return False

def calculate_elapsed_time(start_time):
    """
    Calculate the elapsed time between a given start time and the current time.

    Args:
        start_time (float): The start time in seconds since the epoch.

    Returns:
        str: A formatted string representing the elapsed time.

    Example:
        >>> calculate_elapsed_time(time.time() - 30)
        '30 sec'
        >>> calculate_elapsed_time(time.time() - 120)
        '2 mins 0 sec'
    """
    end_time = time.time()
    elapsed_time = int(end_time - start_time)

    if elapsed_time < 60:
        return f"{elapsed_time} sec"
    else:
        mins, secs = divmod(elapsed_time, 60)
        return f"{mins} mins {secs} sec"
    
def get_filename(url, user_header=None):
    """
    Extracts the filename from the given URL.

    Args:
        url (str): The URL to extract the filename from.
        user_header (str, optional): The user header. Defaults to None.

    Returns:
        str: The filename.
    """
    headers = {}

    if user_header:
        headers['Authorization'] = user_header

    response = requests.get(url, stream=True, headers=headers)
    response.raise_for_status()

    if 'content-disposition' in response.headers:
        content_disposition = response.headers['content-disposition']
        filename = re.findall('filename="?([^"]+)"?', content_disposition)[0]
    else:
        url_path = urlparse(url).path
        filename = unquote(os.path.basename(url_path))

    return filename

def get_python_version():
    """
    Retrieves the current Python version.

    Returns:
        str: The Python version.
    """
    return sys.version

def get_torch_version():
    """
    Retrieves the current PyTorch version.

    Returns:
        str: The PyTorch version.
    """
    try: 
        import torch
        return torch.__version__
    except ImportError:
        cprint("Failed to retrieve PyTorch version: PyTorch is not installed.", color="flat_red")
        return None

def get_gpu_info(get_gpu_name=False):
    """
    Retrieves the GPU info.

    Args:
        get_gpu_name (bool, optional): Whether to retrieve the GPU name. Default is False.

    Returns:
        str: The GPU info.
    """
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

def convert_size(size_bytes: int) -> str:
    """
    Convert the given size in bytes to a more readable format.

    Args:
        size_bytes (int): The size in bytes.

    Returns:
        str: The size in a more readable format (KB, MB, GB, etc.).
    """
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"

def get_file_size(zip_path: str) -> str:
    """
    Get the size of the file at the given path.

    Args:
        zip_path (str): The path to the file.

    Returns:
        str: The size of the file in a more readable format (KB, MB, GB, etc.).
    """
    if not os.path.isfile(zip_path):
        raise ValueError(f"'{zip_path}' is not a valid file path.")

    initial_size = os.path.getsize(zip_path)
    return convert_size(initial_size)


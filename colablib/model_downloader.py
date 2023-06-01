import subprocess
import gdown
import os
import glob
from pathlib import Path
from .cprint import cprint
from .py_utils import get_filename

hf_token = "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"
user_header = f"Authorization: Bearer {hf_token}"

def get_supported_extensions():
    return tuple([".ckpt", ".safetensors", ".pt", ".pth"])

def parse_args(config):
    args = []

    for k, v in config.items():
        if k.startswith("_"):
            args.append(f"{v}")
        elif isinstance(v, str) and v is not None:
            args.append(f'--{k}={v}')
        elif isinstance(v, bool) and v:
            args.append(f"--{k}")
        elif isinstance(v, float) and not isinstance(v, bool):
            args.append(f"--{k}={v}")
        elif isinstance(v, int) and not isinstance(v, bool):
            args.append(f"--{k}={v}")

    return args

def aria2_download(dir, filename, url, user_header=None):
    aria2_config = {
        "console-log-level"         : "error",
        "summary-interval"          : 10,
        "header"                    : user_header if "huggingface.co" in url else None,
        "continue"                  : True,
        "max-connection-per-server" : 16,
        "min-split-size"            : "1M",
        "split"                     : 16,
        "dir"                       : dir,
        "out"                       : filename,
        "_url"                      : url,
    }
    aria2_args = parse_args(aria2_config)
    subprocess.run(["aria2c", *aria2_args])

def gdown_download(url, dst):
    if "/uc?id/" in url:
        return gdown.download(url, dst + "/", quiet=False)
    elif "/file/d/" in url:
        return gdown.download(url, dst + "/", quiet=False, fuzzy=True)
    elif "/drive/folders/" in url:
        os.chdir(dst)
        return gdown.download_folder(url, quiet=True, use_cookies=False)
    
def get_modelname(url, quiet=True):
    extensions = get_supported_extensions()

    if url.startswith("/content/drive/MyDrive/") or url.endswith(tuple(extensions)):
        filename = os.path.basename(url)
    else:
        filename = get_filename(url)

    if filename.endswith(tuple(extensions)):
        if not quiet:
            cprint(f"Filename obtained: {filename}", color="green")
        return filename
    else:
        if not quiet:
            cprint(f"Failed to obtain filename.", color="green")
        return None
    
def download(url, dst):
    filename    = get_modelname(url, quiet=False)

    if "drive.google.com" in url:
        gdown_download(url, dst)
    elif url.startswith("/content/drive/MyDrive/"):
        filepath = os.path.join(dst, filename)
        Path(filepath).write_bytes(Path(url).read_bytes())
    else:
        if "huggingface.co" in url:
            if "/blob/" in url:
                url = url.replace("/blob/", "/resolve/")
        aria2_download(dst, filename, url)

def get_most_recent_file(directory):
    extensions = get_supported_extensions()
    cprint(f"Getting filename from most recent file...", color="green")
    
    files = glob.glob(os.path.join(directory, "*"))
    if not files:
        return None
    most_recent_file = max(files, key=os.path.getmtime)
    basename = os.path.basename(most_recent_file)

    if basename.endswith(tuple(extensions)):
        cprint(f"Filename obtained: {basename}", color="green")

    return most_recent_file

def get_filepath(url, dst):
    extensions = get_supported_extensions()
    filename = get_modelname(url)
    
    if not filename.endswith(extensions):
        most_recent_file = get_most_recent_file(dst)
        filename = os.path.basename(most_recent_file)

    filepath = os.path.join(dst, filename)

    return filepath

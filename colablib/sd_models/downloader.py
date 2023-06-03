import os
import subprocess
import glob
import gdown
from pathlib import Path
from ..utils.py_utils import get_filename
from ..colored_print import cprint

SUPPORTED_EXTENSIONS = (".ckpt", ".safetensors", ".pt", ".pth")

def parse_args(config):
    """
    Converts a dictionary of arguments into a list for command line usage.

    Args:
        config  (dict) : Dictionary of arguments to be parsed.

    Returns:
        args    (list) : List of command line arguments.
    """
    args = []

    for k, v in config.items():
        if k.startswith("_"):
            args.append(str(v))
        elif v is not None and not isinstance(v, bool):
            args.append(f'--{k}={v}')
        elif isinstance(v, bool) and v:
            args.append(f"--{k}")

    return args

def aria2_download(download_dir, filename, url, quiet=False, user_header=None):
    """
    Downloads a file using the aria2 download manager.

    Args:
        download_dir    (str)           : Directory to download the file to.
        filename        (str)           : The name of the file being downloaded.
        url             (str)           : URL to download the file from.
        user_header     (str, optional) : Optional header to use for the download request. Defaults to None.
    """
    if quiet:
        cprint(f"Starting download of '{filename}'...", color="green")

    aria2_config = {
        "console-log-level"         : "error",
        "summary-interval"          : 10,
        "header"                    : user_header if "huggingface.co" in url else None,
        "continue"                  : True,
        "max-connection-per-server" : 16,
        "min-split-size"            : "1M",
        "split"                     : 16,
        "dir"                       : download_dir,
        "out"                       : filename,
        "_url"                      : url,
    }
    aria2_args = parse_args(aria2_config)
    subprocess.run(["aria2c", *aria2_args])

    if quiet:
        cprint(f"Download of '{filename}' completed.", color="green")

def gdown_download(url, dst, quiet=False):
    """
    Downloads a file from a Google Drive URL using gdown.

    Args:
        url (str): The URL of the file on Google Drive.
        dst (str): The directory to download the file to.

    Returns:
        The output of the gdown download function.
    """
    if not quiet:
        cprint(f"Starting download from {url}...", color="green")

    options = {
        "uc?id"         : {},
        "file/d"        : {"fuzzy"      : True},
        "drive/folders" : {"use_cookies": False},
    }

    for key, kwargs in options.items():
        if key in url:
            output = gdown.download(url, os.path.join(dst, ""), quiet=True, **kwargs)
            cprint(f"Download completed.", color="green")
            return output

    os.chdir(dst)
    output = gdown.download_folder(url, quiet=True, use_cookies=False)

    if not quiet:
        cprint(f"Download completed.", color="green")

    return output

def get_modelname(url, quiet=False):
    """
    Retrieves the model name from a given URL.

    Args:
        url   (str)             : The URL of the model file.
        quiet (bool, optional)  : If True, suppresses output. Defaults to True.

    Returns:
        str or None: The filename of the model file if it ends with a supported extension, otherwise None.
    """
    filename = os.path.basename(url) if url.startswith("/content/drive/MyDrive/") or url.endswith(SUPPORTED_EXTENSIONS) else get_filename(url)

    if filename.endswith(SUPPORTED_EXTENSIONS):
        if not quiet:
            cprint(f"Filename obtained: '{filename}'", color="green")
        return filename

    if not quiet:
        cprint(f"Failed to obtain filename.", color="green")
    return None

def download(url, dst, user_header=None, quiet=False):
    """
    Downloads a file from a given URL to a destination directory.

    Args:
        url         (str)           : The URL of the file to download.
        dst         (str)           : The directory to download the file to.
        user_header (str, optional) : Optional header to use for the download request. Defaults to None.
    """
    filename = get_modelname(url, quiet=False)

    if "drive.google.com" in url:
        gdown_download(url, dst, quiet=quiet)
    elif url.startswith("/content/drive/MyDrive/"):
        if not quiet:
            cprint(f"Copying file '{filename}'...", color="green")
        Path(os.path.join(dst, filename)).write_bytes(Path(url).read_bytes())
        if not quiet:
            cprint(f"Copying completed.", color="green")
    else:
        if "huggingface.co" in url:
            url = url.replace("/blob/", "/resolve/")
        aria2_download(dst, filename, url, user_header=user_header, quiet=quiet)

def get_most_recent_file(directory, quiet=False):
    """
    Gets the most recent file in a given directory.

    Args:
        directory (str) : The directory to search in.

    Returns:
        str or None     : The path to the most recent file, or None if no files are found.
    """
    cprint(f"Getting filename from most recent file...", color="green")

    files = glob.glob(os.path.join(directory, "*"))
    if not files:
        if not quiet:
            cprint("No files found in directory.", color="green")
        return None

    most_recent_file = max(files, key=os.path.getmtime)
    basename = os.path.basename(most_recent_file)

    if basename.endswith(SUPPORTED_EXTENSIONS):
        if not quiet:
            cprint(f"Filename obtained: {basename}", color="green")

    return most_recent_file

def get_filepath(url, dst, quiet=False):
    """
    Returns the filepath of the model for a given URL and destination directory.

    Args:
        url (str)   : The URL of the model.
        dst (str)   : The directory to download the model to.

    Returns:
        str         : The filepath of the model.
    """
    filename = get_modelname(url, quiet=quiet)

    if not filename or not filename.endswith(SUPPORTED_EXTENSIONS):
        most_recent_file = get_most_recent_file(dst, quiet=quiet)
        filename = os.path.basename(most_recent_file)

    return os.path.join(dst, filename)
import os
import subprocess
import glob
import gdown
import time
# from mega import Mega
from tqdm import tqdm
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from ..utils.py_utils import get_filename, calculate_elapsed_time
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

def aria2_download(download_dir: str, filename: str , url: str, quiet: bool=False, user_header: str=None):
    """
    Downloads a file using the aria2 download manager.

    Args:
        download_dir    (str)           : Directory to download the file to.
        filename        (str)           : The name of the file being downloaded.
        url             (str)           : URL to download the file from.
        user_header     (str, optional) : Optional header to use for the download request. Defaults to None.
    """
    if not quiet:
        start_time = time.time()
        cprint(f"Starting download of '{filename}' with aria2c...", color="green")

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
    
    if not quiet:
        elapsed_time = calculate_elapsed_time(start_time)
        cprint(f"Download of '{filename}' completed. Took {elapsed_time}.", color="green")

def gdown_download(url: str, dst: str, quiet: bool=False):
    """
    Downloads a file from a Google Drive URL using gdown.

    Args:
        url (str): The URL of the file on Google Drive.
        dst (str): The directory to download the file to.

    Returns:
        The output of the gdown download function.
    """
    if not quiet:
        start_time = time.time()
        cprint(f"Starting download with gdown...", color="green")

    options = {
        "uc?id"         : {},
        "file/d"        : {"fuzzy"      : True},
        "drive/folders" : {"use_cookies": False},
    }

    for key, kwargs in options.items():
        if key in url:
            output = gdown.download(url, os.path.join(dst, ""), quiet=True, **kwargs)
            if not quiet:
                elapsed_time = calculate_elapsed_time(start_time)
                cprint(f"Download completed. Took {elapsed_time}.", color="green")
            return output

    os.chdir(dst)
    output = gdown.download_folder(url, quiet=True, use_cookies=False)

    if not quiet:
        elapsed_time = calculate_elapsed_time(start_time)
        cprint(f"Download completed. Took {elapsed_time}.", color="green")

    return output

# def mega_download(url: str, dst: str, quiet: bool=False):
#     """
#     Downloads a file from a MEGA URL.

#     Args:
#         url (str): The URL of the file on MEGA.
#         dst (str): The directory to download the file to.
#     """
#     if not quiet:
#         start_time = time.time()
#         cprint(f"Starting download with mega.py...", color="green")

#     mega = Mega()
#     m = mega.login()  # add login credentials if needed
#     file = m.download_url(url, dst)
    
#     if not quiet:
#         elapsed_time = calculate_elapsed_time(start_time)
#         cprint(f"Download completed. Took {elapsed_time}.", color="green")

#     return file

def get_modelname(url: str, quiet: bool=False, user_header: str=None) -> None:
    """
    Retrieves the model name from a given URL.

    Args:
        url   (str)             : The URL of the model file.
        quiet (bool, optional)  : If True, suppresses output. Defaults to True.

    Returns:
        str or None: The filename of the model file if it ends with a supported extension, otherwise None.
    """
    filename = os.path.basename(url) if "drive/MyDrive" in url or url.endswith(SUPPORTED_EXTENSIONS) else get_filename(url, user_header=user_header)

    if filename.endswith(SUPPORTED_EXTENSIONS):
        if not quiet:
            cprint(f"Filename obtained: '{filename}'", color="green")
        return filename

    if not quiet:
        cprint(f"Failed to obtain filename.", color="yellow")

    return None

def download(url: str, dst: str, filename:str= None, user_header: str=None, quiet: bool=False):
    """
    Downloads a file from a given URL to a destination directory.

    Args:
        url         (str)           : The URL of the file to download.
        dst         (str)           : The directory to download the file to.
        user_header (str, optional) : Optional header to use for the download request. Defaults to None.
    """
    if not filename:
        filename = get_modelname(url, quiet=quiet)

    if "drive.google.com" in url:
        gdown_download(url, dst, quiet=quiet)
    elif "drive/MyDrive" in url:
        if not quiet:
            start_time = time.time()
            cprint(f"Copying file '{filename}'...", color="green")
        Path(os.path.join(dst, filename)).write_bytes(Path(url).read_bytes())
        if not quiet:
            elapsed_time = calculate_elapsed_time(start_time)
            cprint(f"Copying completed. Took {elapsed_time}.", color="green")
    else:
        if "huggingface.co" in url:
            url = url.replace("/blob/", "/resolve/")
        aria2_download(dst, filename, url, user_header=user_header, quiet=quiet)

def batch_download(urls: list, dst: str, desc: str = None, user_header: str = None, quiet: bool = False) -> None:
    """
    Downloads multiple files from a list of URLs.

    Args:
        urls: A list of URLs from which to download files.
        dst: The directory to download the files to.
        user_header: Optional header to use for the download request. Defaults to None.
        quiet: If True, suppresses output. Defaults to False.
    """
    if desc is None:
        desc = "Downloading..." 

    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(download, url, dst, user_header=user_header, quiet=True) for url in urls]
        with tqdm(total=len(futures), unit='file', disable=quiet, desc=cprint(desc, color="green", tqdm_desc=True)) as pbar:
            for future in as_completed(futures):
                try:
                    future.result()
                    pbar.update(1)
                except Exception as e:
                    cprint(f"Failed to download file with error: {str(e)}", color="flat_red")

def get_most_recent_file(directory: str, quiet: bool=False):
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
            cprint("No files found in directory.", color="yellow")
        return None

    most_recent_file = max(files, key=os.path.getmtime)
    basename = os.path.basename(most_recent_file)

    if basename.endswith(SUPPORTED_EXTENSIONS):
        if not quiet:
            cprint(f"Filename obtained: {basename}", color="green")

    return most_recent_file

def get_filepath(url: str, dst: str, quiet: bool=False):
    """
    Returns the filepath of the model for a given URL and destination directory.

    Args:
        url (str)   : The URL of the model.
        dst (str)   : The directory to download the model to.

    Returns:
        str         : The filepath of the model.
    """
    filename = get_modelname(url, quiet=True)

    if not filename or not filename.endswith(SUPPORTED_EXTENSIONS):
        most_recent_file = get_most_recent_file(dst, quiet=quiet)
        filename = os.path.basename(most_recent_file)

    return os.path.join(dst, filename)

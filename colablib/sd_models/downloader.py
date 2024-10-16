import os
import subprocess
import glob
import gdown
import time
from tqdm import tqdm
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Optional, List
from pydantic import BaseModel, Field
from urllib.parse import urlparse

from ..utils.py_utils import get_filename, calculate_elapsed_time
from ..colored_print import cprint

SUPPORTED_EXTENSIONS = (".ckpt", ".safetensors", ".pt", ".pth")

class DownloadConfig(BaseModel):
    """
    Configuration class for download operations.

    Attributes:
        token (Optional[str]): API token for authentication.
        headers (Dict[str, str]): Additional headers for the download request.
    """
    token: Optional[str] = Field(None, description="API token for authentication")
    headers: Dict[str, str] = Field(default_factory=dict, description="Additional headers")

    def get_headers(self, url: str) -> Dict[str, str]:
        """
        Get headers for the given URL, including authentication if necessary.

        Args:
            url (str): The URL for which to generate headers.

        Returns:
            Dict[str, str]: Headers to use for the download request.
        """
        headers = self.headers.copy()
        if "huggingface.co" in url and self.token and self.token.startswith("hf_"):
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def get_url(self, url: str) -> str:
        """
        Process the URL, adding authentication tokens if necessary.

        Args:
            url (str): The original URL.

        Returns:
            str: The processed URL with authentication added if needed.

        Raises:
            ValueError: If a token is required but not provided for certain URLs.
        """
        parsed_url = urlparse(url)
        
        if parsed_url.netloc == "huggingface.co":
            return url.replace("/blob/", "/resolve/").replace("?download=true", "") 
        elif parsed_url.netloc == "civitai.com":
            if not self.token:
                raise ValueError("A token is required for downloading from civitai.")
            query = f"ApiKey={self.token}"
            if parsed_url.query:
                return f"{url}&{query}"
            else:
                return f"{url}?{query}"
        return url

def parse_args(config: Dict[str, any]) -> List[str]:
    """
    Convert a dictionary of configuration options into command-line arguments.

    Args:
        config (Dict[str, any]): Configuration dictionary.

    Returns:
        List[str]: List of command-line arguments.
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

def aria2_download(download_dir: str, filename: str, url: str, headers: Dict[str, str] = None, quiet: bool = False):
    """
    Download a file using aria2c.

    Args:
        download_dir (str): Directory to save the downloaded file.
        filename (str): Name of the file to be saved.
        url (str): URL to download from.
        headers (Dict[str, str]): Headers to use for the download request.
        quiet (bool, optional): If True, suppress output. Defaults to False.
    """
    if not quiet:
        start_time = time.time()
        cprint(f"Starting download of '{filename}' with aria2c...", color="green")

    aria2_config = {
        "console-log-level": "error",
        "summary-interval": 10,
        "header": [f"{k}: {v}" for k, v in headers.items()] if headers else [],
        "continue": True,
        "max-connection-per-server": 16,
        "min-split-size": "1M",
        "split": 16,
        "dir": download_dir,
        "out": filename,
        "_url": url,
    }
    aria2_args = parse_args(aria2_config)
    subprocess.run(["aria2c", *aria2_args])
    
    if not quiet:
        elapsed_time = calculate_elapsed_time(start_time)
        cprint(f"Download of '{filename}' completed. Took {elapsed_time}.", color="green")

def gdown_download(url: str, dst: str, quiet: bool = False):
    """
    Download a file from Google Drive using gdown.

    Args:
        url (str): Google Drive URL to download from.
        dst (str): Directory to save the downloaded file.
        quiet (bool, optional): If True, suppress output. Defaults to False.

    Returns:
        str: Path to the downloaded file or folder.
    """
    if not quiet:
        start_time = time.time()
        cprint(f"Starting download with gdown...", color="green")

    options = {
        "uc?id": {},
        "file/d": {"fuzzy": True},
        "drive/folders": {"use_cookies": False},
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

def get_modelname(url: str, quiet: bool = False, headers: Dict[str, str] = None) -> Optional[str]:
    """
    Extract the model name from a given URL.

    Args:
        url (str): URL to extract the model name from.
        quiet (bool, optional): If True, suppress output. Defaults to False.
        headers (Dict[str, str], optional): Headers to use for the request. Defaults to None.

    Returns:
        Optional[str]: The extracted model name, or None if extraction failed.
    """
    filename = os.path.basename(url) if "drive/MyDrive" in url or url.endswith(SUPPORTED_EXTENSIONS) else get_filename(url, user_header=headers)

    if filename.endswith(SUPPORTED_EXTENSIONS):
        if not quiet:
            cprint(f"Filename obtained: '{filename}'", color="green")
        return filename

    if not quiet:
        cprint(f"Failed to obtain filename.", color="yellow")

    return None

def download(url: str, dst: str, config: DownloadConfig, filename: str = None, quiet: bool = False):
    """
    Download a file from the given URL using the appropriate method.

    Args:
        url (str): URL to download from.
        dst (str): Directory to save the downloaded file.
        config (DownloadConfig): Configuration for the download.
        filename (str, optional): Name to save the file as. If None, it will be extracted from the URL. Defaults to None.
        quiet (bool, optional): If True, suppress output. Defaults to False.
    """
    url = config.get_url(url)
    headers = config.get_headers(url)

    if not filename:
        filename = get_modelname(url, quiet=quiet, headers=headers)

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
        aria2_download(dst, filename, url, headers=headers, quiet=quiet)

def batch_download(urls: List[str], dst: str, config: DownloadConfig, desc: str = None, quiet: bool = False) -> None:
    """
    Download multiple files concurrently.

    Args:
        urls (List[str]): List of URLs to download from.
        dst (str): Directory to save the downloaded files.
        config (DownloadConfig): Configuration for the downloads.
        desc (str, optional): Description for the progress bar. Defaults to None.
        quiet (bool, optional): If True, suppress output. Defaults to False.
    """
    if desc is None:
        desc = "Downloading..." 

    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(download, url, dst, config, quiet=True) for url in urls]
        with tqdm(total=len(futures), unit='file', disable=quiet, desc=cprint(desc, color="green", tqdm_desc=True)) as pbar:
            for future in as_completed(futures):
                try:
                    future.result()
                    pbar.update(1)
                except Exception as e:
                    cprint(f"Failed to download file with error: {str(e)}", color="flat_red")

def get_most_recent_file(directory: str, quiet: bool = False):
    """
    Get the most recently modified file in the given directory.

    Args:
        directory (str): Directory to search for files.
        quiet (bool, optional): If True, suppress output. Defaults to False.

    Returns:
        str: Path to the most recent file, or None if no files found.
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

def get_filepath(url: str, dst: str, quiet: bool = False):
    """
    Get the filepath for a model based on the URL and destination directory.

    Args:
        url (str): URL of the model.
        dst (str): Destination directory.
        quiet (bool, optional): If True, suppress output. Defaults to False.

    Returns:
        str: Full filepath for the model.
    """
    filename = get_modelname(url, quiet=True)

    if not filename or not filename.endswith(SUPPORTED_EXTENSIONS):
        most_recent_file = get_most_recent_file(dst, quiet=quiet)
        filename = os.path.basename(most_recent_file)

    return os.path.join(dst, filename)

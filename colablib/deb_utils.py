import os
import zipfile
import subprocess
import requests
import shutil
from .py_utils import get_filename
from tqdm import tqdm
from .cprint import cprint

def ubuntu_deps(url, dst, desc=None):
    """
    Downloads, extracts, and installs .deb files from a given URL.

    Args:
        url (str): The URL to download the .deb files from.
        dst (str): The directory to extract to and install the .deb files from.
    """
    os.makedirs(dst, exist_ok=True)
    filename = get_filename(url)
    response = requests.get(url, stream=True)
    response.raise_for_status()

    with open(filename, "wb") as file:
        for chunk in tqdm(response.iter_content(chunk_size=8192), desc="Downloading"):
            if chunk:
                file.write(chunk)

    with zipfile.ZipFile(filename, "r") as deps:
        deps.extractall(dst)

    if desc is None:
        desc = "installing"
    for file in tqdm(os.listdir(dst), desc=desc):
        if file.endswith(".deb"):
            try:
                subprocess.run(["dpkg", "-i", os.path.join(dst, file)], stdout=subprocess.DEVNULL, check=True)
            except subprocess.CalledProcessError as e:
                cprint(f"Error installing {file}: {e}", color="red")
                raise

    os.remove(filename)
    shutil.rmtree(dst)

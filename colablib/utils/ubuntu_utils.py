import os
import zipfile
import requests
import shutil
from .py_utils import get_filename
from tqdm import tqdm
from ..colored_print import cprint

def ubuntu_deps(url, dst, desc=None):
    """
    Downloads, extracts, and installs .deb files from a given URL.

    Args:
        url (str): The URL to download the .deb files from.
        dst (str): The directory to extract to and install the .deb files from.
    """
    os.makedirs(dst, exist_ok=True)
    filename  = get_filename(url)
    
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    with open(filename, 'wb') as file:
        for chunk in response.iter_content(chunk_size=8192):
            file.write(chunk)

    if filename.endswith(".zip"):
        with zipfile.ZipFile(filename, "r") as deps:
            deps.extractall(dst)

        if desc is None:
            desc = cprint("Installing...", color="green", tqdm_desc=True)

        deb_files = [os.path.join(dst, f) for f in os.listdir(dst) if f.endswith('.deb')]
        for deb_file in tqdm(deb_files, desc=desc):
            os.system(f'dpkg -i {deb_file}')
            
        os.remove(filename)
        shutil.rmtree(dst)

    elif filename.endswith(".deb"):
        deb_file = os.path.join(dst, filename)
        os.system(f'dpkg -i {deb_file}')

def unionfuse(fused_dir: str, source_dir: str, destination_dir: str):
    """
    Performs union fuse operation on the given folder path.

    Args:
        source_dir (str): Path of the source folder.
        destination_dir (str): Path of the destination folder.
        fused_dir (str): Path of the fused folder.

    Raises:
        Exception: If any error occurs during union fuse operation.
    """
    try:
        for directory in [source_dir, fused_dir, destination_dir]:
            os.makedirs(directory, exist_ok=True)

        command = f"unionfs-fuse {destination_dir}=RW:\"{source_dir}\"=RW {fused_dir}"
        
        result = os.system(command)
        
        if result != 0:
            cprint(f"An error occurred while fusing the folders. Command exited with status: {result}", color="flat_red")
            raise Exception("Union Fuse operation failed")
        else:
            cprint("Folder fused successfully!", color='green')
    except Exception as e:
        cprint(f"An error occurred while fusing the folders: {e}", color="flat_red")
        raise e
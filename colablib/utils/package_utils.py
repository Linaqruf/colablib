import subprocess
import os
import zipfile
import rarfile
import shutil
from collections import defaultdict
from ..colored_print import cprint

def extract_package(package_name, target_directory, overwrite=False):
    """
    Extracts a package. The package can be in either tar, lz4, rar, or zip format.

    Args:
        package_name (str): The name of the package file.
        target_directory (str): The directory where the package will be extracted.
        overwrite (bool, optional): Whether to overwrite the directory if it already exists. Defaults to False.

    Raises:
        subprocess.CalledProcessError: If the extraction process fails.

    Returns:
        None
    """

    if not os.path.exists(target_directory):
        os.makedirs(target_directory)

    if package_name.endswith(".tar.lz4"):
        tar_args = ["tar", "-xI", "lz4", "-f", package_name, "--directory", target_directory]
        if overwrite:
            tar_args.append("--overwrite-dir")

        try:
            subprocess.check_output(tar_args, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            cprint(f"Package extraction failed with error: {e.output.decode()}", color="flat_red")
    elif package_name.endswith(".zip"):
        try:
            with zipfile.ZipFile(package_name, 'r') as zip_ref:
                zip_ref.extractall(target_directory)
        except Exception as e:
            cprint(f"Package extraction failed with error: {str(e)}", color="flat_red")
    elif package_name.endswith(".rar"):
        try:
            with rarfile.RarFile(package_name, 'r') as rar_ref:
                rar_ref.extractall(target_directory)
        except Exception as e:
            cprint(f"Package extraction failed with error: {str(e)}", color="flat_red")
    else:
        cprint(f"Package type not supported: {package_name}", color="flat_red")

def nested_zip_extractor(zip_path, extract_to):
    """
    This function extracts files from a zip file, maintaining the nested directory structure.
    
    Args:
    zip_path (str): The path to the zip file to extract.
    extract_to (str): The directory to extract the zip file contents to.
    """
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            dir_map = defaultdict(list)
            for name in zip_ref.namelist():
                if not name.endswith('/'):
                    parts = name.split('/')
                    for i in range(1, len(parts)):
                        dir_map['/'.join(parts[:i])].append(name)

            subfolders = [folder for folder in dir_map.keys() if len(dir_map[folder]) > 0]
            if len(subfolders) == 1:
                extract_to = os.path.join(extract_to, subfolders[0])

            for member in zip_ref.infolist():
                if not member.is_dir():
                    parts = member.filename.split('/')
                    for i in range(len(parts) - 1, 0, -1):
                        directory = '/'.join(parts[:i])
                        if len(dir_map[directory]) > 1 or i == 1:
                            target_path = os.path.join(extract_to, *parts[i-1:])
                            os.makedirs(os.path.dirname(target_path), exist_ok=True)
                            with zip_ref.open(member) as source, open(target_path, 'wb') as target:
                                shutil.copyfileobj(source, target)
                            break

    except FileNotFoundError:
        cprint(f"The file {zip_path} does not exist.", color="flat_red")
    except PermissionError:
        cprint(f"Permission denied for creating directories or files.", color="flat_red")
    except Exception as e:
        cprint(f"An error occurred: {str(e)}", color="flat_red")
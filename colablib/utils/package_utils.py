import subprocess
import os
import zipfile
import rarfile
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
    elif overwrite:
        for root, dirs, files in os.walk(target_directory):
            for file in files:
                os.remove(os.path.join(root, file))
            for dir in dirs:
                os.rmdir(os.path.join(root, dir))

    if package_name.endswith(".tar.lz4"):
        tar_args = ["tar", "-xI", "lz4", "-f", package_name, "--directory", target_directory]
        if overwrite:
            tar_args.append("--overwrite-dir")

        try:
            subprocess.check_output(tar_args, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            cprint(f"Package extraction failed with error: {e.output.decode()}", color="yellow")
    elif package_name.endswith(".zip"):
        try:
            with zipfile.ZipFile(package_name, 'r') as zip_ref:
                zip_ref.extractall(target_directory)
        except Exception as e:
            cprint(f"Package extraction failed with error: {str(e)}", color="yellow")
    elif package_name.endswith(".rar"):
        try:
            with rarfile.RarFile(package_name, 'r') as rar_ref:
                rar_ref.extractall(target_directory)
        except Exception as e:
            cprint(f"Package extraction failed with error: {str(e)}", color="yellow")
    else:
        cprint(f"Package type not supported: {package_name}", color="yellow")

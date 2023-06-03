import subprocess
import sys
import os
import concurrent.futures
from tqdm import tqdm
from urllib.parse import urlparse
from ..colored_print import cprint

def clone_repo(url, cwd=None, directory=None, branch=None, commit_hash=None, recursive=False):
    """
    Clones a Git repository.

    Args:
        url (str): The URL of the Git repository.
        cwd (str, optional): The working directory for the subprocess command. Defaults to None.
        directory (str, optional): The directory where the repository should be cloned to. Defaults to None.
        branch (str, optional): The branch to checkout. Defaults to None.
        commit_hash (str, optional): The commit hash to checkout. Defaults to None.
        recursive (bool, optional): Flag to recursively clone submodules. Defaults to False.
    """
    try:
        parsed_url = urlparse(url).path.split('/')[-1].replace('.git', '')

        if not directory:
            directory = parsed_url

        if cwd is not None:
            if os.path.exists(os.path.join(cwd, parsed_url)):
                cprint(f"Directory {os.path.join(cwd, parsed_url)} already exists.", color="yellow")
                return
        else: 
            if os.path.exists(directory):
                cprint(f"Directory {directory} already exists.", color="yellow")
                return

        cmd = ["git", "clone", url]
        if branch:
            cmd.extend(["-b", branch])
        if recursive:
            cmd.append("--recursive")
        if directory:
            cmd.append(directory)

        result = subprocess.run(cmd, check=True, cwd=cwd)
        if commit_hash and directory:
            subprocess.run(["git", "checkout", commit_hash], cwd=directory, check=True)
    except Exception as e:
        cprint(f"Error while cloning the repository: {e}", color="red")
        sys.exit(1)

def batch_clone(urls, desc=None, cwd=None, directory=None, branch=None, commit_hash=None, recursive=False):
    """
    Clones multiple Git repositories in parallel.

    Args:
        urls (list): The URLs of the Git repositories.
        desc (str, optional): The description to display on the progress bar. Defaults to "Cloning...".
        cwd (str, optional): The working directory for the subprocess command. Defaults to None.
        directory (str, optional): The directory where the repositories should be cloned to. Defaults to None.
        branch (str, optional): The branch to checkout. Defaults to None.
        commit_hash (str, optional): The commit hash to checkout. Defaults to None.
        recursive (bool, optional): Flag to recursively clone submodules. Defaults to False.
    """
    if desc is None:
        desc = cprint("Cloning...", color="green", tqdm_desc=True)

    # Use a ThreadPoolExecutor to clone repositories in parallel
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {executor.submit(clone_repo, url, cwd=cwd, directory=directory, branch=branch, commit_hash=commit_hash, recursive=recursive): url for url in urls}
        for future in tqdm(concurrent.futures.as_completed(futures), total=len(urls), desc=desc):
            try:
                future.result()
            except Exception as e:
                cprint(f"Error while cloning a repository: {e}", color="red")
                sys.exit(1)
        
def validate_repo(directory):
    """
    Validates a Git repository.

    Args:
        directory (str): The directory where the Git repository is located.

    Returns:
        tuple: The repository name, the current commit hash, and the current branch.
    """

    def get_current_commit_hash():
        result = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=directory)
        return result.stdout.strip()

    def get_current_branch():
        result = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, cwd=directory)
        return result.stdout.strip()

    def get_repo_name():
        result = subprocess.run(["git", "config", "--get", "remote.origin.url"], capture_output=True, text=True, cwd=directory)
        output = result.stdout.strip()
        if result.returncode == 0 and output:
            url = output
            repo_name = url.split("/")[-1].split(".")[0]  # Extract the repository name
            username = url.split("/")[-2]  # Extract the username
            return f"{username}/{repo_name}"
        else:
            raise ValueError(f"Failed to get repository name for directory: {directory}")

    current_commit_hash = get_current_commit_hash()
    current_branch = get_current_branch()
    repo_name = get_repo_name()

    return repo_name, current_commit_hash, current_branch

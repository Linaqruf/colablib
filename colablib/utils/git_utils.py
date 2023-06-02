import subprocess
import sys
from ..colored_print import cprint

def clone_repo(url, directory=None, branch=None, commit_hash=None):
    """
    Clones a Git repository.

    Args:
        url (str): The URL of the Git repository.
        directory (str, optional): The directory where the repository should be cloned to. Defaults to None.
        branch (str, optional): The branch to checkout. Defaults to None.
        commit_hash (str, optional): The commit hash to checkout. Defaults to None.
    """
    try:
        cmd = ["git", "clone", url]
        if branch:
            cmd.extend(["-b", branch])
        if directory:
            cmd.append(directory)

        result = subprocess.run(cmd, check=True)
        if commit_hash and directory:
            subprocess.run(["git", "checkout", commit_hash], cwd=directory, check=True)
    except Exception as e:
        cprint(f"Error while cloning the repository: {e}", color="red")
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

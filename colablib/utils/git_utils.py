import subprocess
import sys
import os
import concurrent.futures
from tqdm import tqdm
from urllib.parse import urlparse
from ..colored_print import cprint

def clone_repo(url, cwd=None, directory=None, branch=None, commit_hash=None, recursive=False, quiet=False, batch=False):
    """
    Clones a Git repository.

    Args:
        url         (str)               : The URL of the Git repository.
        cwd         (str, optional)     : The working directory for the subprocess command. Defaults to None.
        directory   (str, optional)     : The directory where the repository should be cloned to. Defaults to None.
        branch      (str, optional)     : The branch to checkout. Defaults to None.
        commit_hash (str, optional)     : The commit hash to checkout. Defaults to None.
        recursive   (bool, optional)    : Flag to recursively clone submodules. Defaults to False.
    """
    try:
        parsed_url = urlparse(url).path.split('/')[-1].replace('.git', '')

        if not directory:
            directory = parsed_url

        if cwd is not None:
            if os.path.exists(os.path.join(cwd, parsed_url)):
                cprint(f"Directory '{parsed_url}' already exists.", color="yellow")
                return
        else: 
            if os.path.exists(directory):
                cprint(f"Directory '{parsed_url}' already exists.", color="yellow")
                return

        cmd = ["git", "clone", url]
        if branch:
            cmd.extend(["-b", branch])
        if recursive:
            cmd.append("--recursive")
        if directory:
            cmd.append(directory)

        result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output_log = result.stdout.decode()
        if "Cloning into" in output_log and "done." in output_log:
            message = f"Cloning '{parsed_url}' was successful."
        else:
            message = f"Cloning '{parsed_url}' failed."

        if not quiet and not batch:
            color = "green" if "Failed" not in message and "Error" not in message else "red"
            cprint(message, color=color)
            
        if commit_hash and directory:
            checkout_repo(directory, commit_hash, quiet=quiet)

    except Exception as e:
        message = f"Error while cloning the repository: {e}"
        if not quiet and not batch:
            color = "red"
            cprint(message, color=color)
        return None

    return message

def checkout_repo(directory, reference, create=False, args="", quiet=False):
    cmd = ["git", "checkout"]
    if create:
        cmd.append("-b")
    cmd.append(reference)
    if args:
        cmd.extend(args.split())
    result = subprocess.run(cmd, cwd=directory, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output_log = result.stdout.decode()
    
    if "Switched to branch" in output_log or "HEAD is now at" in output_log:
        message = f"Checkout successful. You are now at {reference}"
    elif "error: pathspec" in output_log and "did not match any file(s)" in output_log:
        message = f"Checkout failed. Invalid or non-existent reference: {reference}"
    elif "error: Your local changes" in output_log and "would be overwritten by checkout" in output_log:
        message = "Checkout failed. Please commit or stash your changes before switching branches."
    elif "warning: short SHA1" in output_log and "is ambiguous" in output_log:
        message = "Checkout failed. Ambiguous reference: " + reference
    elif "warning: refname" in output_log and "is ambiguous" in output_log:
        message = "Checkout failed. Ambiguous reference: " + reference
    else:
        message = "Checkout failed"

    if not quiet:
        color = "green" if "Failed" not in message and "Error" not in message else "red"
        cprint(message, color=color)
    return message

def update_repo(fetch=False, pull=True, origin=None, cwd=None, args="", quiet=False, batch=False):
    """
    Updates a Git repository using fetch and/or pull.

    Args:
        fetch   (bool, optional)  : Flag to perform a fetch. Defaults to False.
        pull    (bool, optional)  : Flag to perform a pull. Defaults to False.
        origin  (str, optional)   : The remote to update from. Defaults to None.
        cwd     (str, optional)   : The working directory for the subprocess command. Defaults to None.
        args    (str, optional)   : Additional arguments for the git command. Defaults to "".
        quiet   (bool, optional)  : Flag to print update status. Defaults to False.
        batch   (bool, optional)  : Flag for batch verbose output
    Returns:
        str                       : Update status message.
    """
    message = ""

    try:
        repo_name, _, _ = validate_repo(cwd)

        if fetch:
            cmd = ["git", "fetch"]
            if origin:
                cmd.append(origin)
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode != 0:
                message = f"Failed to fetch the repository in {cwd}"

        if pull:
            cmd = ["git", "pull"]
            if args:
                cmd.extend(args.split(" "))
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output_log = result.stdout.decode()
            if "Already up to date." in output_log:
                message = f"No new changes. '{repo_name}' is already up to date."
            elif "Fast-forward" in output_log:
                message = f"Pull successful. '{repo_name}' updated to the latest version"
            elif result.returncode != 0:
                message = f"Failed to pull the repository in '{cwd}'"
        
        if not quiet and not batch:
            color = "green" if "Failed" not in message and "Error" not in message else "red"
            cprint(message, color=color)

    except Exception as e:
        message = f"Error while updating the repository: {e}"
        if not quiet and not batch:
            color = "red"
            cprint(message, color=color)
        return None

    return message

def batch_clone(urls, desc=None, cwd=None, directory=None, branch=None, commit_hash=None, recursive=False, quiet=False):
    """
    Clones multiple Git repositories in parallel.

    Args:
        urls        (list)              : The URLs of the Git repositories.
        desc        (str, optional)     : The description to display on the progress bar. Defaults to "Cloning...".
        cwd         (str, optional)     : The working directory for the subprocess command. Defaults to None.
        directory   (str, optional)     : The directory where the repositories should be cloned to. Defaults to None.
        branch      (str, optional)     : The branch to checkout. Defaults to None.
        commit_hash (str, optional)     : The commit hash to checkout. Defaults to None.
        recursive   (bool, optional)    : Flag to recursively clone submodules. Defaults to False.
    """
    if desc is None:
        desc = cprint("Cloning...", color="green", tqdm_desc=True)

    results = {}  # Store clone status messages

    # Use a ThreadPoolExecutor to clone repositories in parallel
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {executor.submit(clone_repo, url, cwd=cwd, directory=directory, branch=branch, commit_hash=commit_hash, recursive=recursive, quiet=quiet, batch=True): url for url in urls}
        for future in tqdm(concurrent.futures.as_completed(futures), total=len(urls), desc=desc):
            try:
                results[future] = future.result()
            except Exception as e:
                cprint(f"Error while cloning a repository: {e}", color="red")
                return None
            
    if not quiet:
        for future, message in results.items():
            color = "green" if "Failed" not in message and "Error" not in message else "red"
            cprint(" [-] ", message, color=color)

def batch_update(fetch=False, pull=True, origin=None, directory=None, args="", quiet=True):
    """
    Updates multiple Git repositories in parallel using fetch and/or pull.

    Args:
        fetch (bool, optional): Flag to perform a fetch. Defaults to False.
        pull (bool, optional): Flag to perform a pull. Defaults to True.
        origin (str, optional): The remote to update from. Defaults to None.
        directory (str or list, optional): The directory or directories where the repositories are located. Defaults to None.
        args (str, optional): Additional arguments for the git command. Defaults to "".
        quiet (bool, optional): Flag to suppress print update status. Defaults to True.
    """
    if not isinstance(directory, list):
        directory = [os.path.join(directory, name) for name in os.listdir(directory) if os.path.isdir(os.path.join(directory, name))]

    results = {}  # Store update status messages

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {executor.submit(update_repo, fetch=fetch, pull=pull, origin=origin, cwd=cwd, args=args, quiet=quiet, batch=True): cwd for cwd in directory}
        for future in tqdm(concurrent.futures.as_completed(futures), total=len(directory), desc="Updating..."):
            try:
                results[future] = future.result()  # Store update status message
            except Exception as e:
                cprint(f"Error while updating a repository: {e}", color="red")
                return None

    if not quiet:
        for future, message in results.items():
            color = "green" if "Failed" not in message and "Error" not in message else "red"
            cprint(" [-] ", message, color=color)

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


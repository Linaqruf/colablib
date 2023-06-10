import subprocess
import os
import requests
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
            
        if os.path.exists(os.path.join(cwd, parsed_url) if cwd else directory):
            message = f"Directory '{parsed_url}' already exists."
            if not quiet and not batch:
                color = "yellow"
                cprint(message, color=color)
            return message

        cmd = ["git", "clone", url]
        if branch:
            cmd.extend(["-b", branch])
        if recursive:
            cmd.append("--recursive")
        if directory:
            cmd.append(directory)

        result = subprocess.run(cmd, text=True, cwd=cwd, capture_output=True)

        if result.returncode == 0:
            message = f"Cloning '{parsed_url}' was successful."
        else:
            message = f"Cloning '{parsed_url}' failed. Error: {result.stderr}"

        if not quiet and not batch:
            color = "green" if not any(item in message for item in ["Failed", "Error", "failed", "error"]) else "red"
            cprint(message, color=color)
            
        if commit_hash and directory:
            checkout_repo(directory, commit_hash, quiet=quiet, batch=batch)

    except Exception as e:
        message = f"Error while cloning the repository: {e}"
        if not quiet and not batch:
            color = "red"
            cprint(message, color=color)
        return None

    return message

def checkout_repo(directory, reference, create=False, args="", quiet=False, batch=False):
    """
    Checks out a specific reference in a Git repository.
    
    Args:
        directory  (str)   : The directory of the repository.
        reference  (str)   : The branch or commit hash to checkout.
        create     (bool)  : Whether to create a new branch. Defaults to False.
        args       (str)   : Additional arguments for the checkout command. Defaults to "".
        quiet      (bool)  : Whether to suppress the output. Defaults to False.
        batch      (bool)  : Whether this is a batch operation. Defaults to False.
    """
    try:
        cmd = ["git", "checkout"]
        if create:
            cmd.append("-b")
        cmd.append(reference)
        if args:
            cmd.extend(args.split())

        result = subprocess.run(cmd, text=True, cwd=directory, capture_output=True)

        if result.returncode == 0:
            message = f"Checkout successful. You are now at {reference}"
        else:
            message = f"Checkout failed. Error: {result.stderr}"
    except Exception as e:
        message = f"An unexpected error occurred while checking out the repository: {str(e)}"

    if not quiet and not batch:
        color = "red" if "Failed" in message or "Error" in message else "green"
        cprint(message, color=color)

    return message

def patch_repo(url, dir, cwd, path=None, args=None, whitespace_fix=False, quiet=False):
    """
    Function to patch a repo with specified arguments.
    
    Args:
        url (str): URL of the repo.
        dir (str): Directory to download the repo.
        cwd (str): Current working directory.
        args (list, optional): List of arguments for the 'git apply' command.
        whitespace_fix (bool, optional): Whether to apply the '--whitespace=fix' argument.
        
    Returns:
        CompletedProcess: Completed process.
    """
    
    # Check if url, dir and cwd are strings
    if not isinstance(url, str) or not isinstance(dir, str) or not isinstance(cwd, str):
        raise ValueError("'url', 'dir' and 'cwd' must be strings")
    
    # Check if args is a list or None
    if args is not None and not isinstance(args, list):
        raise ValueError("'args' must be a list of strings or None")

    # Check if whitespace_fix is a boolean
    if not isinstance(whitespace_fix, bool):
        raise ValueError("'whitespace_fix' must be a boolean")
    
    os.makedirs(dir, exist_ok=True)

    filename = ""
    
    if url:
        filename = urlparse(url).path.split('/')[-1].replace('.git', '')
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            with open(os.path.join(dir, filename), 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
        except Exception as e:
            if not quiet:
                print(f"Error downloading from {url}. Error: {str(e)}")
            return
    elif path:
        filename = os.path.basename(url)
    
    if not path:
        path = os.path.join(dir, filename)

    cmd = ['git', 'apply']
    if whitespace_fix:
        cmd.append('--whitespace=fix')
    if args:
        cmd.extend(args)
    cmd.append(path)
    
    try:
        return subprocess.run(cmd, cwd=cwd, check=True)
    except subprocess.CalledProcessError as e:
        if not quiet:
            cprint(f"Error applying patch. Error: {str(e)}", color="flat_red")

def reset_repo(directory, commit, hard=False, args="", quiet=False):
    """
    Resets a Git repository to a specific commit.
    
    Args:
        directory (str)  : The directory of the repository.
        commit    (str)  : The commit hash to reset to.
        hard      (bool) : Whether to perform a hard reset. Defaults to False.
        args      (str)  : Additional arguments for the reset command. Defaults to "".
        quiet     (bool) : Whether to suppress the output. Defaults to False.
    """
    try:
        cmd = ["git", "reset"]
        if hard:
            cmd.append("--hard")
        cmd.append(commit)
        if args:
            cmd.extend(args.split())

        result = subprocess.run(cmd, text=True, cwd=directory, capture_output=True)

        if result.returncode == 0:
            message = f"Reset successful. The HEAD is now at {commit}"
        else:
            message = f"Reset failed. Error: {result.stderr}"
    except Exception as e:
        message = f"An unexpected error occurred while resetting the repository: {str(e)}"

    if not quiet:
        color = "red" if "Failed" in message or "Error" in message else "green"
        cprint(message, color=color)

    return message

def update_repo(fetch=False, pull=True, origin=None, cwd=None, args="", quiet=False, batch=False):
    """
    Updates a Git repository by fetching and/or pulling new changes.

    Args:
        fetch   (bool)  : Whether to fetch new changes. Defaults to False.
        pull    (bool)  : Whether to pull new changes. Defaults to True.
        origin  (str)   : The name of the remote repository to fetch from. Defaults to None.
        cwd     (str)   : The working directory for the subprocess command. Defaults to None.
        args    (str)   : Additional arguments for the pull command. Defaults to "".
        quiet   (bool)  : Whether to suppress the output. Defaults to False.
        batch   (bool)  : Whether this is a batch operation. Defaults to False.
    """

    try:
        repo_name, _, _ = validate_repo(cwd)

        message = ""

        if fetch:
            cmd = ["git", "fetch"]
            if origin:
                cmd.append(origin)
            result = subprocess.run(cmd, text=True, cwd=cwd, capture_output=True)

            if result.returncode != 0:
                message = f"Error while fetching the repository in {cwd}: {result.stderr}"

        if pull:
            cmd = ["git", "pull"]
            if args:
                cmd.extend(args.split(" "))
            result = subprocess.run(cmd, text=True, cwd=cwd, capture_output=True)

            if result.returncode != 0:
                message = f"Error while pulling the repository in {cwd}: {result.stderr}"
            elif "Already up to date." in result.stdout:
                # message = f"'{repo_name}' is already up to date."
                pass
            else:
                message = f"'{repo_name}' updated to the latest version"

        if not quiet and not batch:
            color = "green" if not any(item in message for item in ["Failed", "Error", "failed", "error"]) else "red"
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
                cprint(f"Error while cloning a repository: {e}", color="flat_red")
                return None
            
    if not quiet:
        if not any(message for message in results.values()):
                cprint()
        for future, message in results.items():
            if message:
                if "already exists" in message.lower():
                    color = "yellow"
                elif not any(item.lower() in message.lower() for item in ["failed", "error"]):
                    color = "green"
                else:
                    color = "red"
                cprint(" [-]", message, color=color)
        cprint()

def batch_update(fetch=False, pull=True, origin=None, directory=None, args="", quiet=False, desc=None):
    """
    Updates multiple Git repositories in parallel using fetch and/or pull.

    Args:
        fetch       (bool, optional)        : Flag to perform a fetch. Defaults to False.
        pull        (bool, optional)        : Flag to perform a pull. Defaults to True.
        origin      (str, optional)         : The remote to update from. Defaults to None.
        directory   (str or list, optional) : The directory or directories where the repositories are located. Defaults to None.
        args        (str, optional)         : Additional arguments for the git command. Defaults to "".
        quiet       (bool, optional)        : Flag to suppress print update status. Defaults to True.
        desc        (str, optional)         : The description to display on the progress bar. Defaults to "Updating...".
    """
    if not isinstance(directory, list):
        directory = [os.path.join(directory, name) for name in os.listdir(directory) if os.path.isdir(os.path.join(directory, name))]

    if desc is None:
        desc = cprint("Updating...", color="green", tqdm_desc=True)

    results = {}  # Store update status messages

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {executor.submit(update_repo, fetch=fetch, pull=pull, origin=origin, cwd=cwd, args=args, quiet=quiet, batch=True): cwd for cwd in directory}
        for future in tqdm(concurrent.futures.as_completed(futures), total=len(directory), desc=desc):
            try:
                results[future] = future.result()  # Store update status message
            except Exception as e:
                cprint(f"Error while updating a repository: {e}", color="flat_red")
                return None

    if not quiet:
        if not any(message for message in results.values()):
                cprint()
        for future, message in results.items():
            if message:
                if not any(item.lower() in message.lower() for item in ["failed", "error"]):
                    color = "green"
                else:
                    if "already exists" in message.lower():
                        color = "yellow"
                    else:
                        color = "red"
                cprint(f" [-]", message, color=color)

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
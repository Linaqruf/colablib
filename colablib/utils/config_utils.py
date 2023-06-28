import json
import yaml
import xmltodict
import toml
import requests
import fileinput
from ..colored_print import cprint

def determine_file_format(filename):
    """
    Determine the file format based on the filename extension.

    Args:
        filename (str): The filename.

    Returns:
        str: The file format (json, yaml, xml, toml, txt, or css).
    """
    file_extension = filename.lower().split(".")[-1]
    if file_extension in ("json", "yaml", "yml", "xml", "toml", "txt"):
        return file_extension
    else:
        return "txt"

def read_config(filename):
    """
    Read configuration from a file.

    Args:
        filename (str): The path to the configuration file. Can be JSON, YAML, XML, TOML, or TXT.

    Returns:
        dict or str: The configuration read from the file. For TXT files, a string is returned.
    """
    file_format = determine_file_format(filename)

    if file_format == "json":
        with open(filename, "r") as f:
            config = json.load(f)
    elif file_format == "yaml" or file_format == "yml":
        with open(filename, "r") as f:
            config = yaml.safe_load(f)
    elif file_format == "xml":
        with open(filename, "r") as f:
            config = xmltodict.parse(f.read())
    elif file_format == "toml":
        with open(filename, "r") as f:
            config = toml.load(f)
    else:
        with open(filename, 'r') as f:
            config = f.read()

    return config


def write_config(filename, config):
    """
    Write configuration to a file.

    Args:
        filename (str): The path to the configuration file. Can be JSON, YAML, XML, TOML, or TXT.
        config (dict or str): The configuration to write to the file.
    """
    file_format = determine_file_format(filename)

    if file_format == "json":
        with open(filename, "w") as f:
            json.dump(config, f, indent=4)
    elif file_format == "yaml" or file_format == "yml":
        with open(filename, "w") as f:
            yaml.dump(config, f)
    elif file_format == "xml":
        with open(filename, "w") as f:
            xml = xmltodict.unparse(config, pretty=True)
            f.write(xml)
    elif file_format == "toml":
        with open(filename, "w") as f:
            toml.dump(config, f)
    else:
        with open(filename, 'w', encoding="utf-8") as f:
            f.write(config)


def change_line(filename, old_string, new_string):
    """
    Replace a string in a file with another string.

    Args:
        filename (str): The path to the file.
        old_string (str): The string to be replaced.
        new_string (str): The string to replace with.
    """
    with fileinput.input(files=(filename,), inplace=True) as file:
        for line in file:
            print(line.replace(old_string, new_string), end='')

def pastebin_reader(id):
    if "pastebin.com" in id:
        url = id 
        if 'raw' not in url:
                url = url.replace('pastebin.com', 'pastebin.com/raw')
    else:
        url = "https://pastebin.com/raw/" + id
    response = requests.get(url)
    response.raise_for_status() 
    lines = response.text.split('\n')
    return lines
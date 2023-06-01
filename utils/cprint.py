def cprint(*args, color="default", reset=True, tqdm_desc=False):
    """
    Prints colored text in the console.

    Args:
        *args: Text to be printed.
        color (str, optional)       : Text color. Default is "default".
        reset (bool, optional)      : Whether to reset color after printing. Default is True.
        tqdm_desc (bool, optional)  : If used as a description in tqdm. Default is False.

    Returns:
        None
    """
    color_codes = {
        "default"     : "\033[0m",
        "green"       : "\033[0;32m",
        "red"         : "\033[0;31m",
        "bold_green"  : "\033[1;32m",
        "bold_red"    : "\033[1;31m",
    }
    
    if color not in color_codes:
        raise ValueError(f"Invalid color value '{color}'. Available options are: {', '.join(color_codes.keys())}")

    color_start = color_codes[color]
    color_end = color_codes["default"] if reset else ""
    formatted_text = " ".join(str(arg) for arg in args)

    if tqdm_desc:
        return color_start + formatted_text
    else:
        print(color_start + formatted_text + color_end)

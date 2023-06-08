import datetime
import pytz

color_codes = {
    "default"      : "\033[0m",
    "black"        : "\033[0;30m",
    "red"          : "\033[0;31m",
    "green"        : "\033[0;32m",
    "yellow"       : "\033[0;33m",
    "blue"         : "\033[0;34m",
    "purple"       : "\033[0;35m",
    "cyan"         : "\033[0;36m",
    "white"        : "\033[0;37m",
    "flat_red"     : "\033[38;2;204;102;102m",
    "flat_yellow"  : "\033[38;2;255;204;0m",
    "flat_blue"    : "\033[38;2;0;102;204m",
    "flat_purple"  : "\033[38;2;153;51;255m",
    "flat_orange"  : "\033[38;2;255;153;0m",
    "flat_green"   : "\033[38;2;0;204;102m",
    "flat_gray"    : "\033[38;2;128;128;128m",
    "flat_cyan"    : "\033[38;2;0;255;255m",
    "flat_pink"    : "\033[38;2;255;0;255m",
}

style_codes = {
    "normal"      : "\033[0m",
    "bold"        : "\033[1m",
    "italic"      : "\033[3m",
    "underline"   : "\033[4m",
    "blink"       : "\033[5m",
    "inverse"     : "\033[7m",
    "strikethrough": "\033[9m",
}

def cprint(*args, color="default", style="normal", bg_color=None, reset=True, timestamp=False, line=None, tqdm_desc=False, timestamp_format='%Y-%m-%d %H:%M:%S', prefix=None, suffix=None, timezone=None):
    """
    Prints colored text in the console.

    Args:
        *args            : Text to be printed.
        color            : Text color. Default is "default".
        style            : Text style. Default is "normal".
        bg_color         : Background color. Default is None.
        reset            : Whether to reset color after printing. Default is True.
        timestamp        : If set to True, it will add a timestamp in the beginning of the print. Default is False.
        line             : If provided, will print equal number of line before the text. Default is None.
        tqdm_desc        : If used as a description in tqdm. Default is False.
        timestamp_format : The format of the timestamp if timestamp is True. Default is '%Y-%m-%d %H:%M:%S'.
        prefix           : Optional prefix for the text. Default is None.
        suffix           : Optional suffix for the text. Default is None.
        timezone         : The timezone to use for the timestamp. If None, the local timezone will be used.

    Returns:
        None
    """
    if color not in color_codes:
        raise ValueError(f"Invalid color value '{color}'. Available options are: {', '.join(color_codes.keys())}")

    if style not in style_codes:
        raise ValueError(f"Invalid style value '{style}'. Available options are: {', '.join(style_codes.keys())}")

    if bg_color and bg_color not in color_codes:
        raise ValueError(f"Invalid background color value '{bg_color}'. Available options are: {', '.join(color_codes.keys())}")

    color_start = style_codes[style] + color_codes[color]
    if bg_color:
        bg_color_code = "\033[4" + color_codes[bg_color][3:]
        color_start += bg_color_code
    color_end = color_codes["default"] if reset else ""
    formatted_text = " ".join(str(arg) for arg in args)

    if prefix:
        formatted_text = str(prefix) + formatted_text

    if suffix:
        formatted_text = formatted_text + str(suffix)

    if timestamp:
        now = datetime.datetime.now(pytz.timezone(timezone) if timezone else pytz.timezone('UTC'))
        formatted_text = f"[{now.strftime(timestamp_format)}] {formatted_text}"

    if line:
        formatted_text = "\n" * line + formatted_text

    if tqdm_desc:
        return color_start + formatted_text
    else:
        print(color_start + formatted_text + color_end)

def print_line(length, color="default", style="normal", bg_color=None, reset=True):
    """
    Prints a line of equal signs.

    Args:
        length: The length of the line.
        color: Text color. Default is "default".
        style: Text style. Default is "normal".
        bg_color: Background color. Default is None.
        reset: Whether to reset color after printing. Default is True.

    Returns:
        None
    """
    line = "=" * length
    cprint(line, color=color, style=style, bg_color=bg_color, reset=reset)

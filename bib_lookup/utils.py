"""
"""

import re
from enum import Enum
from pathlib import Path
from typing import Any, List, Optional, Union

try:
    from IPython import get_ipython
except ModuleNotFoundError:
    get_ipython = None


__all__ = [
    "is_notebook",
    "default_class_repr",
    "ReprMixin",
    "color_text",
    "md_text",
    "printmd",
    "str2bool",
    "gather_tex_source_files_in_one",
    "NETWORK_ERROR_MESSAGES",
]


def is_notebook() -> bool:
    """Check if the current environment is a notebook (Jupyter or Colab).

    Implementation adapted from [#sa]_.

    Parameters
    ----------
    None

    Returns
    -------
    bool
        Whether the code is running in a notebook

    References
    ----------
    .. [#sa] https://stackoverflow.com/questions/15411967/how-can-i-check-if-code-is-executed-in-the-ipython-notebook

    """
    try:
        shell = get_ipython().__class__
        if shell.__name__ == "ZMQInteractiveShell":
            return True  # Jupyter notebook or qtconsole
        elif "colab" in repr(shell).lower():
            return True  # Google Colab
        elif shell.__name__ == "TerminalInteractiveShell":
            return False  # Terminal running IPython
        else:  # Other type (?)
            return False
    except NameError:  # Probably standard Python interpreter
        return False
    except TypeError:  # get_ipython is None
        return False


def default_class_repr(c: object, align: str = "center", depth: int = 1) -> str:
    """Default string representation of a class.

    Parameters
    ----------
    c : object
        The object to be represented.
    align : str, default "center"
        Alignment of the class arguments.
    depth : int, default 1
        Depth of the class arguments to display.

    Returns
    -------
    str
        The string representation of the class.

    """
    indent = 4 * depth * " "
    closing_indent = 4 * (depth - 1) * " "
    if not hasattr(c, "extra_repr_keys"):
        return repr(c)
    elif len(c.extra_repr_keys()) > 0:
        max_len = max([len(k) for k in c.extra_repr_keys()])
        extra_str = (
            "(\n"
            + ",\n".join(
                [
                    f"""{indent}{k.ljust(max_len, " ") if align.lower() in ["center", "c"] else k} = {default_class_repr(eval(f"c.{k}"),align,depth+1)}"""
                    for k in c.__dir__()
                    if k in c.extra_repr_keys()
                ]
            )
            + f"{closing_indent}\n)"
        )
    else:
        extra_str = ""
    return f"{c.__class__.__name__}{extra_str}"


class ReprMixin(object):
    """Mixin class for enhanced
    :meth:`__repr__` and :meth:`__str__` methods.
    """

    def __repr__(self) -> str:
        return default_class_repr(self)

    __str__ = __repr__

    def extra_repr_keys(self) -> List[str]:
        """Extra keys for :meth:`__repr__` and :meth:`__str__`."""
        return []


# the following text color methods are adapted from `colorama`


class _ANSI_ESCAPE_CODES(Enum):
    """Escape codes for printing color to the terminal."""

    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    GRAY = "\033[37m"
    PURPLE = "\033[35m"
    FAIL = "\033[91m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    """ This color stops the current color sequence. """
    STOP = "\033[0m"


def color_text(text: str, color: Optional[str] = None, method: str = "ansi", **kwargs: Any) -> str:
    """Color the text.

    Parameters
    ----------
    text : str
        The text to be colored.
    color : str, optional
        The color of the text.
        If is None, the text will be printed in the default color.
    method : {"ansi", "html", "file"}, optional
        The method to print the text, by default "ansi".
    kwargs: Any,
        Not used, to be consistent with the methods
        :func:`md_text` and :func:`printmd`.

    Returns
    -------
    str
        The colored text.

    """
    if color is None:
        return text
    if not isinstance(color, (str, tuple)):
        raise TypeError(f"Cannot color text with provided color of type `{type(color)}`")
    if isinstance(color, tuple):
        if len(color) > 1:
            text = color_text(text, color[1:], method)
        color = color[0]

    if method == "html":
        return f"<font color = {color}>{text}</font>"
    elif method == "ansi":
        color = color.lower()
        if color == "green":
            color = _ANSI_ESCAPE_CODES.OKGREEN.value
        elif color == "red":
            color = _ANSI_ESCAPE_CODES.FAIL.value
        elif color == "blue":
            color = _ANSI_ESCAPE_CODES.OKBLUE.value
        elif color == "purple":
            color = _ANSI_ESCAPE_CODES.PURPLE.value
        elif color == "gray":
            color = _ANSI_ESCAPE_CODES.GRAY.value
        elif color == "bold":
            color = _ANSI_ESCAPE_CODES.BOLD.value
        elif color == "underline":
            color = _ANSI_ESCAPE_CODES.UNDERLINE.value
        elif color == "warning":
            color = _ANSI_ESCAPE_CODES.WARNING.value
        else:
            raise ValueError(f"unknown text color `{color}`")

        return color + text + _ANSI_ESCAPE_CODES.STOP.value
    elif method == "file":
        return "[[" + text + "]]"
    else:
        raise ValueError(f"unknown text color method `{method}`")


def md_text(
    text: str,
    color: Optional[str] = None,
    method: str = "md",
    bold: bool = False,
    font_size: Optional[Union[int, str]] = None,
    font_family: Optional[str] = None,
) -> str:
    """Turn the text into markdown.

    Parameters
    ----------
    text : str
        The text to be turned into markdown.
    color : str, optional
        The color of the text.
        If is None, the text will be printed in the default color.
    method : {"html", "md", "markdown"}, default "md"
        Not used, to be consistent with the methods :func:`color_text`.
    bold : bool, default False
        Whether to print the text in bold.
    font_size : int or str, optional
        Font size of the text.
        If is None, the text will be printed in the default font size.
    font_family : str, optional
        Font family of the text.
        If is None, the text will be printed in the default font family.

    Returns
    -------
    str
        The markdown text.

    """
    assert method in ["html", "md", "markdown"], f"unknown method `{method}`"
    color_style = f"color: {color}" if color is not None else ""
    font_family_style = f"font-family: '{font_family}'" if font_family is not None else ""
    font_size_style = f"font-size: {str(font_size)}" if font_size is not None else ""
    span_style = "; ".join([color_style, font_size_style, font_family_style])
    md_str = f"""<span style="{span_style}">{text}</span>"""
    if bold:
        md_str = f"""<strong>{md_str}</strong>"""
    return md_str


def printmd(md_str: str) -> None:
    """Print the markdown text.

    Modified from
    https://stackoverflow.com/questions/23271575/printing-bold-colored-etc-text-in-ipython-qtconsole

    Parameters
    ----------
    md_str : str
        String in the markdown style.

    Returns
    -------
    None

    """
    try:
        from IPython.display import Markdown, display

        display(Markdown(md_str))
    except ModuleNotFoundError:
        print(md_str)


def str2bool(v: Union[str, bool, int, float]) -> bool:
    """Converts a "boolean" value possibly in the format of str to bool.

    Implementation from StackOverflow [#sa]_.

    Parameters
    ----------
    v : str or bool or int or float
        The "boolean" value.

    Returns
    -------
    bool
        `v` in the format of bool.

    References
    ----------
    .. [#sa] https://stackoverflow.com/questions/15008758/parsing-boolean-values-with-argparse

    """
    if isinstance(v, bool):
        b = v
    elif isinstance(v, (int, float)):
        b = bool(v)
    elif v.lower() in ("yes", "true", "t", "y", "1"):
        b = True
    elif v.lower() in ("no", "false", "f", "n", "0"):
        b = False
    else:
        raise ValueError("Boolean value expected.")
    return b


def gather_tex_source_files_in_one(
    entry_file: Union[str, Path],
    write_file: bool = False,
    output_file: Optional[Union[str, Path]] = None,
) -> str:
    """Gathers all the tex source files in one file.

    This function is useful when the entry file contains ``input`` commands
    to include other tex files,
    and when the journal submission system does not support subdirectories.

    Parameters
    ----------
    entry_file : str or pathlib.Path
        The entry file (usually the main.tex file).
    write_file : bool, default False
        Whether to write the tex source into a file.
        If False, the tex source will be returned as a string.
    output_file : str or pathlib.Path, optional
        The output file to write the tex source into.
        If is None and `write_file` is True,
        the output file will be the ``{entry_file.stem}_{in_one}.tex``.

    Returns
    -------
    str
        The tex source if `write_file` is False,
        or the path to the output file if `write_file` is True.

    """
    input_pattern = "[\\w|\\/\\_\\-]+(?:\\.tex)?"
    input_pattern = f"""\\\\input{{(?P<filepath>{input_pattern})}}"""
    root = Path(entry_file).parent
    content = Path(entry_file).read_text()
    while True:
        input_items = []
        for item in re.findall(input_pattern, content):
            for line in content.splitlines():
                if line.strip().startswith("%"):
                    continue
                if f"{{{item}}}" in line:
                    input_items.append(item)
                    break
        if len(input_items) == 0:
            break
        for item in input_items:
            content = content.replace(f"\\input{{{item}}}", (root / item).with_suffix(".tex").read_text())
    if not write_file:
        return content
    if output_file is None:
        output_file = root / f"{Path(entry_file).stem}_in_one.tex"
    if Path(entry_file).resolve() == Path(output_file).resolve():
        raise ValueError("The entry file and the output file are the same, " "which is not allowed for security reasons.")
    if Path(output_file).exists():
        raise FileExistsError("The output file exists. " "If you want to overwrite it, you should delete it manually first.")
    Path(output_file).write_text(content, encoding="utf-8")
    return str(output_file)


NETWORK_ERROR_MESSAGES = """400 Bad Request
401 Unauthorized
402 Payment Required
403 Forbidden
404 Not Found
405 Method Not Allowed
406 Not Acceptable
407 Proxy Authentication Required
408 Request Timeout
409 Conflict
410 Gone
411 Length Required
412 Precondition Failed
413 Payload Too Large
414 URI Too Long
415 Unsupported Media Type
416 Range Not Satisfiable
417 Expectation Failed
418 I'm a teapot
421 Misdirected Request
422 Unprocessable Entity
423 Locked
424 Failed Dependency
425 Too Early
426 Upgrade Required
428 Precondition Required
429 Too Many Requests
431 Request Header Fields Too Large
451 Unavailable For Legal Reasons
500 Internal Server Error
501 Not Implemented
502 Bad Gateway
503 Service Unavailable
504 Gateway Timeout
505 HTTP Version Not Supported
506 Variant Also Negotiates
507 Insufficient Storage
508 Loop Detected
510 Not Extended
511 Network Authentication Required""".splitlines()

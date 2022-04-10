"""
"""

from enum import Enum
from typing import List, Optional, NoReturn, Any, Union

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
]


def is_notebook() -> bool:
    """

    check if the current environment is a notebook (Jupyter or Colab)

    Returns
    -------
    bool,
        whether the code is running in a notebook

    Modified from
    https://stackoverflow.com/questions/15411967/how-can-i-check-if-code-is-executed-in-the-ipython-notebook

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
    """

    Parameters
    ----------
    c: object,
        the object to be represented
    align: str, default "center",
        the alignment of the class arguments
    depth: int, default 1,
        the depth of the class arguments to display

    Returns
    -------
    str,
        the representation of the class

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
    """
    Mixin for enhanced __repr__ and __str__ methods.

    """

    def __repr__(self) -> str:
        return default_class_repr(self)

    __str__ = __repr__

    def extra_repr_keys(self) -> List[str]:
        """ """
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


def color_text(
    text: str, color: Optional[str] = None, method: str = "ansi", **kwargs: Any
) -> str:
    """

    Parameters
    ----------
    text: str,
        the text to be colored
    color: str, optional,
        the color of the text,
        if None, the text will be printed in the default color
    method: str, default "ansi",
        the method to print the text,
        can be "ansi", "html" or "file"
    kwargs: Any,
        not used, to be consistent with the methods `md_text` and `printmd`

    Returns
    -------
    str,
        the colored text

    """
    if color is None:
        return text
    if not isinstance(color, (str, tuple)):
        raise TypeError(f"Cannot color text with provided color of type {type(color)}")
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
            raise ValueError(f"unknown text color {color}")

        return color + text + _ANSI_ESCAPE_CODES.STOP.value
    elif method == "file":
        return "[[" + text + "]]"
    else:
        raise ValueError(f"unknown text color method {method}")


def md_text(
    text: str,
    color: Optional[str] = None,
    method: str = "md",
    bold: bool = False,
    font_size: Optional[Union[int, str]] = None,
    font_family: Optional[str] = None,
) -> str:
    """

    Parameters
    ----------
    text: str,
        the text to be turned into markdown
    color: str, optional,
        the color of the text,
        if None, the text will be printed in the default color
    method: str, default "md",
        not used, to be consistent with the methods `color_text`,
        should be one of "html", "md" or "markdown"
    bold: bool, default False,
        whether to bold the text
    font_size: int or str, optional,
        the font size of the text
        if None, the text will be printed in the default font size
    font_family: str, optional,
        the font family of the text
        if None, the text will be printed in the default font family

    Returns
    -------
    md_str: str,
        the markdown text

    """
    assert method in ["html", "md", "markdown"]
    color_style = f"color: {color}" if color is not None else ""
    font_family_style = (
        f"font-family: '{font_family}'" if font_family is not None else ""
    )
    font_size_style = f"font-size: {str(font_size)}" if font_size is not None else ""
    span_style = "; ".join([color_style, font_size_style, font_family_style])
    md_str = f"""<span style="{span_style}">{text}</span>"""
    if bold:
        md_str = f"""<strong>{md_str}</strong>"""
    return md_str


def printmd(md_str: str) -> NoReturn:
    """

    printing bold, colored, etc., text

    Parameters
    ----------
    md_str: str,
        string in the markdown style

    Modified from
    https://stackoverflow.com/questions/23271575/printing-bold-colored-etc-text-in-ipython-qtconsole

    """
    try:
        from IPython.display import Markdown, display

        display(Markdown(md_str))
    except ModuleNotFoundError:
        print(md_str)

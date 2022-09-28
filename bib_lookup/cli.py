"""
Command-line interface for the bib_lookup package.

"""

import argparse
from pathlib import Path
from typing import Union

try:
    from bib_lookup.bib_lookup import BibLookup
except ImportError:
    # https://gist.github.com/vaultah/d63cb4c86be2774377aa674b009f759a
    import sys

    level = 1
    global __package__
    file = Path(__file__).resolve()
    parent, top = file.parent, file.parents[level]

    sys.path.append(str(top))
    try:
        sys.path.remove(str(parent))
    except ValueError:  # already removed
        pass
    __package__ = ".".join(parent.parts[len(top.parts) :])

    from bib_lookup.bib_lookup import BibLookup


def required_length(nmin: int, nmax: int) -> argparse.Action:
    # https://stackoverflow.com/questions/4194948/python-argparse-is-there-a-way-to-specify-a-range-in-nargs
    class RequiredLength(argparse.Action):
        def __call__(self, parser, args, values, option_string=None):
            if not nmin <= len(values) <= nmax:
                msg = f"""argument "{self.dest}" requires between {nmin} and {nmax} arguments"""
                raise argparse.ArgumentTypeError(msg)
            setattr(args, self.dest, values)

    return RequiredLength


def str2bool(v: Union[str, bool]) -> bool:
    """

    converts a "boolean" value possibly in the format of str to bool

    Parameters
    ----------
    v: str or bool,
        the "boolean" value

    Returns
    -------
    b: bool,
        `v` in the format of bool

    References
    ----------
    https://stackoverflow.com/questions/15008758/parsing-boolean-values-with-argparse

    """
    if isinstance(v, bool):
        b = v
    elif v.lower() in ("yes", "true", "t", "y", "1"):
        b = True
    elif v.lower() in ("no", "false", "f", "n", "0"):
        b = False
    else:
        raise ValueError("Boolean value expected.")
    return b


def main():
    """
    Command-line interface for the bib_lookup package.

    """
    parser = argparse.ArgumentParser(
        description="Look up a BibTeX entry from a DOI identifier, PMID (URL) or arXiv ID (URL)."
    )
    parser.add_argument(
        "identifiers",
        nargs=argparse.ZERO_OR_MORE,
        type=str,
        help="DOI, PMID or arXiv ID (URL) to look up.",
    )
    parser.add_argument(
        "-a",
        "--align",
        type=str,
        default="middle",
        help="Alignment of the output text.",
        choices=["left", "middle", "left-middle"],
    )
    parser.add_argument(
        "-c",
        "--check-file",
        help="Can be boolean or path to a Bib File. Checks the input Bib file or output bib file for errors.",
        dest="check_file",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Output file to write the BibTeX entries to.",
        dest="output_file",
    )
    parser.add_argument(
        "-i",
        "--input",
        type=str,
        help="Input file to read the identifiers (DOI, PMID or arXiv ID (URL)) from.",
        dest="input_file",
    )
    parser.add_argument(
        "--ignore-fields",
        nargs=argparse.ZERO_OR_MORE,
        type=str,
        default=["url"],
        help="List of fields to ignore.",
        dest="ignore_fields",
    )
    parser.add_argument(
        "--email",
        type=str,
        help="Email address to use for the lookup, optional.",
        dest="email",
    )
    parser.add_argument(
        "--ordering",
        type=str,
        nargs=argparse.ZERO_OR_MORE,
        default=["author", "title", "journal", "booktitle"],
        help="Order of the fields in the output.",
        dest="ordering",
    )
    parser.add_argument(
        "--allow-duplicates",
        action="store_true",
        help="allow duplicate entries when writing to file.",
        dest="allow_duplicates",
    )
    parser.add_argument(
        "--arxiv2doi",
        action="store_true",
        help="Convert arXiv ID to DOI to look up.",
        dest="arxiv2doi",
    )

    args = vars(parser.parse_args())

    check_file = args["check_file"]
    if check_file is not None:
        if Path(check_file).is_file() and Path(check_file).suffix == ".bib":
            # check this file, other augments are ignored
            check_file = Path(check_file)
        else:
            check_file = str2bool(check_file)

    bl = BibLookup(
        align=args["align"],
        ignore_fields=args["ignore_fields"],
        output_file=args["output_file"],
        email=args["email"],
        ordering=args["ordering"],
        arxiv2doi=args["arxiv2doi"],
        verbose=0,
    )

    if check_file is not None and isinstance(check_file, Path):
        bl.check_bib_file(check_file)
        return
    else:
        assert (
            len(args["identifiers"]) > 0 or args["input_file"] is not None
        ), "No identifiers given."

    if len(args["identifiers"]) > 0:
        bl(args["identifiers"])
    if args["input_file"] is not None:
        bl(args["input_file"])
    if args["output_file"] is not None:
        bl.save(skip_existing=not args["allow_duplicates"])
        if check_file:
            bl.check_bib_file(bl.output_file)
    else:
        if len(bl) == 0:
            print("No entries found.")
        else:
            bl.print()


if __name__ == "__main__":
    main()

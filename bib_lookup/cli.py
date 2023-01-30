"""
Command-line interface for the bib_lookup package.

"""

import argparse
import warnings
from pathlib import Path
from typing import Union

from bib_lookup.bib_lookup import BibLookup


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
    """Command-line interface for the bib_lookup package."""
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
        type=str2bool,
        default=True,
        help="Convert arXiv ID to DOI to look up.",
        dest="arxiv2doi",
    )
    parser.add_argument(
        "--ignore-errors",
        type=str2bool,
        default=True,
        help="Ignore errors when looking up",
        dest="ignore_errors",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=6,
        help="Ignore errors when looking up",
        dest="timeout",
    )
    parser.add_argument(
        "--format",
        type=str,
        help="Format of the output, can be 'bibtex' or 'text', etc., optional.",
        dest="format",
    )
    parser.add_argument(
        "--style",
        type=str,
        help="Style of the output, valid only when 'format' is 'text', optional.",
        dest="style",
    )
    parser.add_argument(
        "--verbose",
        type=int,
        default=0,
        help="Verbosity level",
        dest="verbose",
    )
    parser.add_argument(
        "--gather",
        type=str,
        help="The entry .tex file to call `utils.gather_tex_source_files_in_one`",
        dest="gather",
    )

    args = vars(parser.parse_args())

    if "gather" in args and args["gather"] is not None:
        from bib_lookup.utils import gather_tex_source_files_in_one

        entry_file = Path(args["gather"]).resolve()

        if not entry_file.is_file() or entry_file.suffix != ".tex":
            print(
                f"File {args['gather']} is not a valid .tex file. Please check and try again."
            )
            return

        if len(args["identifiers"]) > 0 or args["input_file"] is not None:
            warnings.warn(
                "Identifiers and input file are ignored when gathering .tex files.",
                RuntimeWarning,
            )

        try:
            gather_tex_source_files_in_one(args["gather"], write_file=True)
        except FileExistsError:
            print(
                f"Output file for {args['gather']} already exists. "
                "Please remove it first and try again."
            )
        return

    check_file = args["check_file"]
    if check_file is not None:
        if Path(check_file).is_file() and Path(check_file).suffix == ".bib":
            # check this file, other augments are ignored
            check_file = Path(check_file)
        else:
            check_file = str2bool(check_file)

    kwargs = {}
    if args["format"] is not None:
        kwargs["format"] = args["format"]
    if args["style"] is not None:
        kwargs["style"] = args["style"]
    if args["timeout"] is not None:
        kwargs["timeout"] = args["timeout"]
    if args["ignore_errors"] is not None:
        kwargs["ignore_errors"] = args["ignore_errors"]
    if args["verbose"] is not None:
        kwargs["verbose"] = args["verbose"]

    bl = BibLookup(
        align=args["align"],
        ignore_fields=args["ignore_fields"],
        output_file=args["output_file"],
        email=args["email"],
        ordering=args["ordering"],
        arxiv2doi=args["arxiv2doi"],
        **kwargs,
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

"""
Command-line interface for the bib_lookup package.

"""

import argparse

try:
    from bib_lookup.bib_lookup import BibLookup
except ImportError:
    # https://gist.github.com/vaultah/d63cb4c86be2774377aa674b009f759a
    import sys
    from pathlib import Path

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


def main():
    """
    Command-line interface for the bib_lookup package.

    """
    parser = argparse.ArgumentParser(
        description="Look up a BibTeX entry from a DOI identifier, PMID (URL) or arXiv ID (URL)."
    )
    parser.add_argument(
        "identifiers",
        nargs="*",
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
        nargs="*",
        type=str,
        default="url",
        help="List of fields to ignore.",
        dest="ignore_fields",
    )
    parser.add_argument(
        "--email",
        type=str,
        help="Email address to use for the lookup, optional.",
        dest="email",
    )
    args = vars(parser.parse_args())

    assert (
        len(args["identifiers"]) > 0 or args["input_file"] is not None
    ), "No identifiers given."

    bl = BibLookup(
        align=args["align"],
        ignore_fields=args["ignore_fields"],
        output_file=args["output_file"],
        email=args["email"],
        verbose=0,
    )

    if len(args["identifiers"]) > 0:
        bl(args["identifiers"])
    if args["input_file"] is not None:
        bl(args["input_file"])
    if args["output_file"] is not None:
        bl.save()
    else:
        bl.print()


if __name__ == "__main__":
    main()

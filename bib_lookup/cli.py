"""
Command-line interface for the bib_lookup package.

"""

import argparse
import json
import warnings
from pathlib import Path

import yaml

from bib_lookup._const import CONFIG_FILE as _CONFIG_FILE
from bib_lookup._const import DEFAULT_CONFIG as _DEFAULT_CONFIG
from bib_lookup.bib_lookup import BibLookup
from bib_lookup.utils import str2bool
from bib_lookup.version import __version__ as bl_version


def main():
    """Command-line interface for the bib_lookup package."""
    parser = argparse.ArgumentParser(description="Look up a BibTeX entry from a DOI identifier, PMID (URL) or arXiv ID (URL).")
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
        default=None,
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
        default=None,
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
        default=None,
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
        "-s",
        "--simplify-bib",
        type=str,
        help=(
            "The .tex file to simplify corresponding bib file by removing unused entries "
            "and writing to a new file with `_simplified` appended to the original file name."
            "Requires the `input` argument to be the bib file."
        ),
        dest="simplify_bib",
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
    parser.add_argument(
        "--version",
        action="version",
        version=f"bib_lookup {bl_version}",
        help="Show the version number and exit.",
    )
    parser.add_argument(
        "--config",
        type=str,
        help=(
            "Configuration for the bib_lookup package. "
            "Can be path to a json or yaml file, "
            "or a string in KEY=VALUE pairs separated by semicolons "
            "enclosed by double quotes. "
            "Can also be ``show`` to show the current configuration, "
            "or ``reset`` to reset (delete) the user-defined "
            "configuration file if it exists."
        ),
    )

    args = vars(parser.parse_args())

    if args.get("config", None) is not None:
        if args["config"] == "show":
            if not _CONFIG_FILE.is_file():
                print("User-defined configuration file does not exist.")
                print("Using default configurations:")
                print(json.dumps(_DEFAULT_CONFIG, indent=4))
            else:
                user_config = json.loads(_CONFIG_FILE.read_text())
                print("User-defined configurations:")
                print(json.dumps(user_config, indent=4))
                print("The rest default configurations:")
                print(
                    json.dumps(
                        {k: v for k, v in _DEFAULT_CONFIG.items() if k not in user_config},
                        indent=4,
                    )
                )
            return
        elif args["config"] == "reset":
            if _CONFIG_FILE.is_file():
                _CONFIG_FILE.unlink()
                print("User-defined configuration file deleted.")
            else:
                print("User-defined configuration file does not exist. No need to reset.")
            return
        else:
            if "=" in args["config"]:
                config = dict([kv.strip().split("=") for kv in args["config"].split(";")])
            else:
                assert Path(args["config"]).is_file(), (
                    f"Configuration file ``{args['config']}`` does not exist. " "Please check and try again."
                )
                if Path(args["config"]).suffix == ".json":
                    config = json.loads(Path(args["config"]).read_text())
                elif Path(args["config"]).suffix in [".yaml", ".yml"]:
                    config = yaml.safe_load(Path(args["config"]).read_text())
                else:
                    raise ValueError(
                        f"Unknown configuration file type ``{Path(args['config']).suffix}``. "
                        "Only json and yaml files are supported."
                    )
            # discard unknown keys
            unknown_keys = set(config.keys()) - set(_DEFAULT_CONFIG.keys())
            config = {k: v for k, v in config.items() if k in _DEFAULT_CONFIG}
            # parse lists in the config
            for k, v in config.items():
                if isinstance(v, str) and v.startswith("[") and v.endswith("]"):
                    config[k] = [vv.strip() for vv in v.strip("[]").split(",")]
            if len(unknown_keys) > 0:
                verb = "are" if len(unknown_keys) > 1 else "is"
                warnings.warn(
                    f"Unknown configuration keys ``{unknown_keys}`` {verb} discarded.",
                    RuntimeWarning,
                )
            print(f"Setting configurations:\n{json.dumps(config, indent=4)}")
            _CONFIG_FILE.write_text(json.dumps(config, indent=4))
            return

    if args.get("gather", None) is not None:
        from bib_lookup.utils import gather_tex_source_files_in_one

        entry_file = Path(args["gather"]).resolve()

        if not entry_file.is_file() or entry_file.suffix != ".tex":
            print(f"File {args['gather']} is not a valid .tex file. Please check and try again.")
            return

        if len(args["identifiers"]) > 0 or args["input_file"] is not None:
            warnings.warn(
                "Identifiers and input file are ignored when gathering .tex files.",
                RuntimeWarning,
            )

        try:
            gather_tex_source_files_in_one(args["gather"], write_file=True)
        except FileExistsError:
            print(f"Output file for {args['gather']} already exists. " "Please remove it first and try again.")
        return

    if args.get("simplify_bib", None) is not None:
        if args.get("input_file", None) is None:
            print("Please provide the input bib file to simplify.")
            return
        input_file = Path(args["input_file"]).resolve()
        if not input_file.is_file() or input_file.suffix != ".bib":
            print(f"Input bib file {args['input_file']} is not a valid .bib file. Please check and try again.")
            return

        simplified_bib_file = BibLookup.simplify_bib_file(tex_sources=args["simplify_bib"], bib_file=input_file)
        # print(f"Simplified bib file written to {simplified_bib_file}")
        return

    check_file = args["check_file"]
    if check_file is not None:
        if Path(check_file).is_file() and Path(check_file).suffix == ".bib":
            # check this file, other augments are ignored
            check_file = Path(check_file)
        else:
            check_file = str2bool(check_file)

    # fmt: off
    init_args = dict()
    for k in [
        "align", "ignore_fields", "output_file", "email", "ordering",
        "arxiv2doi", "format", "style", "timeout", "ignore_errors", "verbose"
    ]:
        if args[k] is not None:
            init_args[k] = args[k]
    # fmt: on

    bl = BibLookup(**init_args)

    if check_file is not None and isinstance(check_file, Path):
        bl.check_bib_file(check_file)
        return
    else:
        assert len(args["identifiers"]) > 0 or args["input_file"] is not None, "No identifiers given."

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

"""
Command-line interface for the bib_lookup package.

"""

import argparse
import json
import sys
import warnings
from pathlib import Path
from typing import Any, Dict

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

from bib_lookup._const import CONFIG_FILE as _CONFIG_FILE
from bib_lookup._const import DEFAULT_CONFIG as _DEFAULT_CONFIG
from bib_lookup.bib_lookup import BibLookup
from bib_lookup.utils import str2bool
from bib_lookup.version import __version__ as bl_version


def _handle_config(config_arg: str) -> None:
    """Handle configuration commands."""
    if config_arg == "show":
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
    elif config_arg == "reset":
        if _CONFIG_FILE.is_file():
            _CONFIG_FILE.unlink()
            print("User-defined configuration file deleted.")
        else:
            print("User-defined configuration file does not exist. No need to reset.")
        return
    else:
        if "=" in config_arg:
            config = dict([kv.strip().split("=") for kv in config_arg.split(";")])
        else:
            config_path = Path(config_arg)
            assert config_path.is_file(), f"Configuration file ``{config_arg}`` does not exist. Please check and try again."

            if config_path.suffix == ".json":
                config = json.loads(config_path.read_text())
            elif config_path.suffix in [".yaml", ".yml"]:
                if yaml is None:
                    raise ImportError(
                        "PyYAML is required to parse yaml config files. Please install it via `pip install PyYAML`."
                    )
                config = yaml.safe_load(config_path.read_text())
            else:
                raise ValueError(
                    f"Unknown configuration file type ``{config_path.suffix}``. " "Only json and yaml files are supported."
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


def _handle_gather(args: Dict[str, Any]) -> None:
    """Handle the gather command."""
    from bib_lookup.utils import gather_tex_source_files_in_one

    try:
        gather_args = args["gather"]
        if len(gather_args) == 1:
            entry_file = Path(gather_args[0]).resolve()
            output_file = None  # let the function use default naming
        elif len(gather_args) == 2:
            entry_file = Path(gather_args[0]).resolve()
            output_file = Path(gather_args[1]).resolve()
        else:
            print("Error: --gather accepts one or two arguments only.")
            sys.exit(1)

        if entry_file.exists() and (not entry_file.is_file() or entry_file.suffix != ".tex"):
            print(f"Error: File {entry_file} is not a valid .tex file.")
            sys.exit(1)

        if len(args["identifiers"]) > 0 or args["input_file"] is not None:
            warnings.warn(
                "Identifiers and input file are ignored when gathering .tex files.",
                RuntimeWarning,
            )

        gather_tex_source_files_in_one(
            entry_file,
            write_file=True,
            output_file=output_file,
            overwrite=args["overwrite"],
            keep_comments=not args["remove_comments"],
        )
    except FileExistsError as e:
        print(f"Error: {e}".replace("overwrite=True", "--overwrite"))
        print("Use the --overwrite flag to overwrite the existing file.")
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please check the file path and try again.")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")  # pragma: no cover
        sys.exit(1)  # pragma: no cover


def _handle_simplify_bib(args: Dict[str, Any]) -> None:
    """Handle the simplify bib command."""
    if args.get("input_file", None) is not None:
        input_file = Path(args["input_file"]).resolve()
        if not input_file.is_file() or input_file.suffix != ".bib":
            print(f"Input bib file {args['input_file']} is not a valid .bib file. Please check and try again.")
            sys.exit(1)
    else:
        input_file = None
    output_file = args["output_file"]
    output_mode = "w" if args["overwrite"] else "a"

    BibLookup.simplify_bib_file(
        tex_sources=args["simplify_bib"], bib_file=input_file, output_file=output_file, output_mode=output_mode
    )


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
        action="store_true",
        help="Convert arXiv ID to DOI to look up.",
        dest="arxiv2doi",
    )
    parser.add_argument(
        "--ignore-errors",
        action="store_true",
        help="Ignore errors when looking up",
        dest="ignore_errors",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=6,
        help="Timeout for the lookup request. Unit is seconds. Default is 6 seconds.",
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
        nargs="+",  # allow one or two arguments
        help="The entry .tex file to call `utils.gather_tex_source_files_in_one`. "
        "Optionally, you can specify the output file as the second argument.",
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
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite the generated file if it already exists.",
    )
    parser.add_argument(
        "--remove-comments",
        action="store_true",
        help="Remove comments when gathering .tex files (only applicable with --gather).",
        dest="remove_comments",
    )
    args = vars(parser.parse_args())

    if args.get("config", None) is not None:
        _handle_config(args["config"])
        return

    if args.get("gather", None) is not None:
        _handle_gather(args)
        return

    if args.get("simplify_bib", None) is not None:
        _handle_simplify_bib(args)
        return

    check_file = args["check_file"]
    if check_file is not None:
        if Path(check_file).is_file() and Path(check_file).suffix == ".bib":
            # check this file, other arguments are ignored
            check_file = Path(check_file)
        else:
            check_file = str2bool(check_file)

    init_keys = [
        "align",
        "ignore_fields",
        "output_file",
        "email",
        "ordering",
        "arxiv2doi",
        "format",
        "style",
        "timeout",
        "ignore_errors",
        "verbose",
    ]
    init_args = {k: args[k] for k in init_keys if args[k] is not None}

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
            bl.check_bib_file(bl.output_file)  # type: ignore
    else:
        if len(bl) == 0:
            print("No entries found.")
        else:
            bl.print()


if __name__ == "__main__":
    main()  # pragma: no cover

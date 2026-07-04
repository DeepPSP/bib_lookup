"""Constants for the bib_lookup package."""

from pathlib import Path

CACHE_DIR = Path.home() / ".cache" / "bib-lookup"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# user config file
CONFIG_FILE = CACHE_DIR / "config.json"

# default config
DEFAULT_CONFIG = dict(
    align="middle",
    email=None,
    ignore_fields=["url", "abstract"],
    ignore_errors=False,
    timeout=6.0,
    arxiv2doi=True,
    format="bibtex",
    style="apa",
    verbose=0,
    print_result=False,
    ordering=["title", "author", "journal", "booktitle"],
    cache_limit=1e6,
    capitalize_title=False,
    max_names=3,
    gbmedium=None,
)

# Style-specific parameters documentation.
# These parameters are passed to the style class constructor
# when the corresponding style is active, and are recognised
# by the `set` and `--config` commands in addition to the keys
# in DEFAULT_CONFIG above.
STYLE_PARAMETERS = {
    "gbt7714": {
        "gbmedium": {
            "type": "bool_or_none",
            "default": None,
            "description": (
                "Medium type tag for articles in GB/T 7714 style. "
                "True -> [J/OL] (online), False -> [J] (print), "
                "None -> auto-detect based on presence of DOI/URL fields."
            ),
        },
    },
    "ieee": {},
    "apa": {},
    "chicago": {},
}

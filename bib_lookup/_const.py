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
)

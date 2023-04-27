"""Constants for the bib_lookup package."""

from pathlib import Path


CACHE_DIR = Path.home() / ".cache" / "bib-lookup"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

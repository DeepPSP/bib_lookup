"""Constants for the bib_lookup package."""

import os
import tempfile
import warnings
from pathlib import Path
from typing import Optional, Tuple

_CACHE_ROOT_NAME = "bib-lookup"

# Preferred cache root.  This is only a *path*: it is deliberately NOT created
# here (import must never touch the filesystem) and it may be unusable, e.g.
# when HOME is absent, read-only, quota-limited or not owned by the process
# user.  Use :func:`get_cache_dir` for a resolved, usable directory.
CACHE_DIR = Path.home() / ".cache" / _CACHE_ROOT_NAME

# user config file
CONFIG_FILE = CACHE_DIR / "config.json"

# default citation cache paths, used by `CitationMixin` as class-level
# defaults; they are resolved per instance at first use (see
# `citation_mixin.CitationMixin._resolve_cache`)
DEFAULT_CITATION_CACHE_DB = CACHE_DIR / "bib-lookup-cache.db"
DEFAULT_CITATION_CACHE_CSV = CACHE_DIR / "bib-lookup-cache.csv"

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


def _usable_cache_dir(candidate: Path) -> bool:
    """Return True if *candidate* can be created and written to."""
    try:
        candidate.mkdir(parents=True, exist_ok=True)
        # unique probe name: several processes may resolve the cache root
        # concurrently, and a shared probe name would make touch() collide,
        # falsely declaring a usable directory unusable (splitting the cache
        # across per-process temp fallbacks)
        probe = candidate / f".bib-lookup-write-probe-{os.getpid()}"
        probe.touch()
        probe.unlink()
        return True
    except OSError:
        return False


def _resolve_cache_dir() -> Tuple[Optional[Path], bool]:
    """Resolve the cache root directory.

    Returns ``(cache_dir, is_temporary)``; ``cache_dir`` is ``None`` when no
    usable directory exists at all, which disables citation caching.

    Lookup order (first usable candidate wins):

    1. ``BIB_LOOKUP_CACHE_DIR`` environment variable, if set;
    2. ``XDG_CACHE_HOME/bib-lookup``, if ``XDG_CACHE_HOME`` is set;
    3. ``~/.cache/bib-lookup``;
    4. a process-local temporary directory (cache still works inside the
       process but does not persist across runs);
    5. ``None`` -- no usable directory found.
    """
    candidates = []
    env_dir = os.environ.get("BIB_LOOKUP_CACHE_DIR")
    if env_dir:
        candidates.append(Path(env_dir).expanduser())
    xdg_dir = os.environ.get("XDG_CACHE_HOME")
    if xdg_dir:
        candidates.append(Path(xdg_dir).expanduser() / _CACHE_ROOT_NAME)
    candidates.append(CACHE_DIR)
    for candidate in candidates:
        if _usable_cache_dir(candidate):
            return candidate, False
    try:
        # last resort: process-local temporary directory
        return Path(tempfile.mkdtemp(prefix=f"{_CACHE_ROOT_NAME}-")), True
    except OSError:
        return None, False


_UNSET = object()
_CACHE_DIR_RESOLVED: "object | None" = _UNSET


def get_cache_dir() -> Optional[Path]:
    """Return the resolved cache directory, or ``None`` if caching is disabled.

    The directory is created on first use and the result is memoized per
    process.  This function never raises and never runs at import time.
    """
    global _CACHE_DIR_RESOLVED
    if _CACHE_DIR_RESOLVED is _UNSET:
        try:
            cache_dir, is_temporary = _resolve_cache_dir()
        except Exception:  # pragma: no cover -- nothing should raise here
            cache_dir, is_temporary = None, False
        _CACHE_DIR_RESOLVED = cache_dir
        if _CACHE_DIR_RESOLVED is None:
            warnings.warn(
                "bib_lookup: no writable cache directory found; citation caching is disabled",
                RuntimeWarning,
            )
        elif is_temporary:
            warnings.warn(
                f"bib_lookup: using a temporary cache directory "
                f"({_CACHE_DIR_RESOLVED}); the citation cache will not persist "
                f"across runs",
                RuntimeWarning,
            )
    return _CACHE_DIR_RESOLVED  # type: ignore[return-value]

Changelog
=========

All notable changes to this project will be documented in this file.

The format is based on `Keep a
Changelog <https://keepachangelog.com/en/1.1.0/>`__, and this project
adheres to `Semantic
Versioning <https://semver.org/spec/v2.0.0.html>`__.

`Unreleased <https://github.com/DeepPSP/bib_lookup/compare/v0.1.1...HEAD>`__
------------------------------------------------------------------------------------------------

Added
~~~~~

Changed
~~~~~~~

- Add argument `keep_comments` to function `gather_tex_source_files_in_one`
  in `utils` module to control whether to keep comments in the output.

Deprecated
~~~~~~~~~~

Removed
~~~~~~~

Fixed
~~~~~

Security
~~~~~~~~

`0.1.1 <https://github.com/DeepPSP/bib_lookup/compare/v0.1.0...v0.1.1>`__ - 2025-08-28
------------------------------------------------------------------------------------------------

Fixed
~~~~~

- Fix bugs in the utility function `utils.gather_tex_source_files_in_one`: Removed
  problematic regex pattern that caused over-matching of content preceding `\input{}`
  commands. Implemented robust comment exclusion using interval intersection detection
  to prevent processing of commented `\input{}` commands. Added utility functions
  `overlaps()` and `is_intersect()` to accurately determine if matched commands fall
  within comment boundaries.

`0.1.0 <https://github.com/DeepPSP/bib_lookup/compare/v0.0.29...v0.1.0>`__ - 2025-08-18
------------------------------------------------------------------------------------------------

Added
~~~~~

- Add `overwrite` optional argument to function
  `gather_tex_source_files_in_one` in `utils` module.
- Add utility function `capitalize_title` in `utils` module,
  and add it as an option for the streamlit app.

Changed
~~~~~~~

- Add `doi` field to `arXiv` lookup results.
- Enhance the text format lookup results.

Fixed
~~~~~

- Fix layout bugs of the streamlit app.
- Fix bugs in the function `utils.gather_tex_source_files_in_one` when
  `\input{\some_filepath}` and commented `% \input{\some_filepath}` coexist.
- Update the base URL for the PubMed ID lookup service, and change
  post method to get method to fetch the lookup content.
- Fix bugs in the function `utils.gather_tex_source_files_in_one` when
  the `filepath` in `\input{filepath}` contains commands like
  `\currfiledir` or `\currfileabsdir`, or contains characters other than
  alphanumeric characters and `/` (e.g. Chinese characters).

`0.0.29 <https://github.com/DeepPSP/bib_lookup/compare/v0.0.28...v0.0.29>`__ - 2024-08-15
------------------------------------------------------------------------------------------------

Added
~~~~~

- Add support of simplify bib functions for CLI.

Changed
~~~~~~~

- Improve layout the streamlit app.
- Use `bs4` to parse html to text.

Fixed
~~~~~

- Fix errors for parsing complicated bib items.
- Fix potential errors parsing the trailing month.

`0.0.28 <https://github.com/DeepPSP/bib_lookup/compare/v0.0.27...v0.0.28>`__ - 2024-02-28
------------------------------------------------------------------------------------------------

Fixed
~~~~~

- Fix empty lookup result bug `#5 <https://github.com/DeepPSP/bib_lookup/issues/5>`__.
- Fix error parsing bib files in method `_to_bib_item` of `BibLookup` class.

`0.0.27 <https://github.com/DeepPSP/bib_lookup/compare/v0.0.26...v0.0.27>`__ - 2023-12-10
------------------------------------------------------------------------------------------------

Fixed
~~~~~

- Fix bugs in method `_to_bib_item` of `BibLookup` class that
  break its idempotency.

`0.0.26 <https://github.com/DeepPSP/bib_lookup/compare/v0.0.25...v0.0.26>`__ - 2023-11-16
------------------------------------------------------------------------------------------------

Added
~~~~~

- Add streamlit app.
- Add `cache_limit` config as an init parameter for `BibLookup` class.

Changed
~~~~~~~

- Reformat code with `pre-commit`.
- Update docs `conf.py`.

Removed
~~~~~~~

- Remove unused bash scripts.

`0.0.25 <https://github.com/DeepPSP/bib_lookup/compare/v0.0.24...v0.0.25>`__ - 2023-08-16
------------------------------------------------------------------------------------------------

Fixed
~~~~~

- Fix errors in method `_to_bib_item` of `BibLookup` class when
  parsing the url field.

`0.0.24 <https://github.com/DeepPSP/bib_lookup/compare/v0.0.22...v0.0.24>`__ - 2023-08-06
------------------------------------------------------------------------------------------------

Added
~~~~~

- Add support of config file for `bib-lookup`

0.0.23  [YANKED]
------------------------------------------------------------------------------------------------

This release was yanked.

`0.0.22 <https://github.com/DeepPSP/bib_lookup/compare/v0.0.21...v0.0.22>`__ - 2023-01-30
------------------------------------------------------------------------------------------------

Changed
~~~~~~~

- Use `requests.Session` for looking-up the bib items.

`0.0.21 <https://github.com/DeepPSP/bib_lookup/compare/v0.0.20...v0.0.21>`__ - 2023-01-08
------------------------------------------------------------------------------------------------

Changed
~~~~~~~

- Improve the `__eq__` method of `BibItem` class.
- Update CLI so that recently added functions can be used
  with CLI.

`0.0.20 <https://github.com/DeepPSP/bib_lookup/compare/v0.0.19...v0.0.20>`__ - 2022-12-03
------------------------------------------------------------------------------------------------

Changed
~~~~~~~

- Improve the `__eq__` method of `BibItem` class.

`0.0.19 <https://github.com/DeepPSP/bib_lookup/compare/v0.0.18...v0.0.19>`__ - 2022-10-09
------------------------------------------------------------------------------------------------

Added
~~~~~

- Add `CitationMixin` class.

`0.0.18 <https://github.com/DeepPSP/bib_lookup/compare/v0.0.17...v0.0.18>`__ - 2022-09-23
------------------------------------------------------------------------------------------------

Added
~~~~~

- Add support for formats other than bibtex for DOI

`0.0.17 <https://github.com/DeepPSP/bib_lookup/compare/v0.0.16...v0.0.17>`__ - 2022-07-29
------------------------------------------------------------------------------------------------

Fixed
~~~~~

- Fix bugs in function `gather_tex_source_files_in_one`.
- Update the method `read_bib_file` of `BibLookup` class, so that
  no field is ignored when reading a bib file

`0.0.16 <https://github.com/DeepPSP/bib_lookup/compare/v0.0.14...v0.0.16>`__ - 2022-07-19
------------------------------------------------------------------------------------------------

Added
~~~~~

- Add two optional arguments `timeout` and `ignore_errors`
  for `BibLookup` class.

Fixed
~~~~~

- Fix bugs in cases where there are line breaks inside a field.

0.0.15 [YANKED]
------------------------------------------------------------------------------------------------

This release was yanked.

`0.0.14 <https://github.com/DeepPSP/bib_lookup/compare/v0.0.13...v0.0.14>`__ - 2022-06-14
------------------------------------------------------------------------------------------------

Fixed
~~~~~

- Fix errors in the `__call__` method of `BibLookup` class when passing
  a sequence of identifiers with some specific parameters assigned values.

`0.0.13 <https://github.com/DeepPSP/bib_lookup/compare/v0.0.12...v0.0.13>`__ - 2022-06-01
------------------------------------------------------------------------------------------------

Added
~~~~~

- Add demo notebook.
- Add a default `bib_lookuper`.

`0.0.12 <https://github.com/DeepPSP/bib_lookup/compare/v0.0.11...v0.0.12>`__ - 2022-05-10
------------------------------------------------------------------------------------------------

Added
~~~~~

- Add support for `arxiv2doi` in CLI.
- Add helper function `gather_tex_source_files_in_one` in `utils` module.

Changed
~~~~~~~

- Improve handling of network-related errors.

`0.0.11 <https://github.com/DeepPSP/bib_lookup/compare/v0.0.10...v0.0.11>`__ - 2022-04-22
------------------------------------------------------------------------------------------------

Added
~~~~~

- Add helper method `clear_cache` for `BibLookup` class.

Changed
~~~~~~~

- Update the `citation_pattern` in the static method `simplify_bib_file`
  of `BibLookup` class.

`0.0.10 <https://github.com/DeepPSP/bib_lookup/compare/v0.0.9...v0.0.10>`__ - 2022-04-18
------------------------------------------------------------------------------------------------

Added
~~~~~

- Add static method `simplify_bib_file` for `BibLookup` class.

Changed
~~~~~~~

- Improve bib file parsing.
- Enhanced the layout of the string format of the cached lookup results.

`0.0.9 <https://github.com/DeepPSP/bib_lookup/compare/v0.0.8...v0.0.9>`__ - 2022-04-12
------------------------------------------------------------------------------------------------

Added
~~~~~

- Add options for converting from arxiv to doi.

Fixed
~~~~~

- Fix bugs in `__eq__` method of `BibItem` class.
- Correct handling of not found doi items.
- Correct handling of underscores in bib title.

`0.0.8 <https://github.com/DeepPSP/bib_lookup/compare/v0.0.7...v0.0.8>`__ - 2022-04-10
------------------------------------------------------------------------------------------------

Added
~~~~~

- Add zenodo config file.

`0.0.7 <https://github.com/DeepPSP/bib_lookup/compare/v0.0.6...v0.0.7>`__ - 2022-04-10
------------------------------------------------------------------------------------------------

Changed
~~~~~~~

- Enhance printing in jupyter notebooks.

`0.0.6 <https://github.com/DeepPSP/bib_lookup/compare/v0.0.5...v0.0.6>`__ - 2022-04-10
------------------------------------------------------------------------------------------------

Added
~~~~~

- Add `utils` module which contains several utility functions.

`0.0.5 <https://github.com/DeepPSP/bib_lookup/compare/v0.0.4...v0.0.5>`__ - 2022-04-07
------------------------------------------------------------------------------------------------

Added
~~~~~

- Add method `check_bib_file` for `BibLookup` class.

Changed
~~~~~~~

- Enhance `save` method for `BibLookup` class.

`0.0.4 <https://github.com/DeepPSP/bib_lookup/compare/v0.0.3...v0.0.4>`__ - 2022-04-06
------------------------------------------------------------------------------------------------

Added
~~~~~

- Add CLI support for bib-lookup.

`0.0.3 <https://github.com/DeepPSP/bib_lookup/compare/v0.0.2...v0.0.3>`__ - 2022-04-06
------------------------------------------------------------------------------------------------

Added
~~~~~

- Add class `BibItem`.
- Add custom (enhanced) `__repr__` method for the `BibLookup` class.

`0.0.2 <https://github.com/DeepPSP/bib_lookup/compare/v0.0.1...v0.0.2>`__ - 2022-03-31
------------------------------------------------------------------------------------------------

Added
~~~~~

- Add IO functions for saving the lookup results.

`0.0.1 <https://github.com/DeepPSP/bib_lookup/tree/v0.0.1>`__ - 2022-03-31
------------------------------------------------------------------------------------------------

Added
~~~~~

- Add class `BibLookup`.

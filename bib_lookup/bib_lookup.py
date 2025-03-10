"""
A useful tool for looking up Bib entries using DOI, or pubmed ID (or URL), or arXiv ID (or URL).

It is an updated version of
https://github.com/wenh06/utils/blob/master/utils_universal/utils_bib.py

Requirements
------------
- requests
- feedparser
- pandas

"""

import json
import re
import warnings
from collections import OrderedDict
from copy import deepcopy
from pathlib import Path
from string import punctuation
from typing import Dict, List, Optional, Sequence, Tuple, Union

import feedparser
import numpy as np
import requests
from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning

from ._bib import BIB_FIELDS, DF_BIB_ENTRY_TYPES, BibItem
from ._const import CONFIG_FILE as _CONFIG_FILE
from ._const import DEFAULT_CONFIG as _DEFAULT_CONFIG
from .utils import (
    NETWORK_ERROR_MESSAGES,
    ReprMixin,
    color_text,
    gather_tex_source_files_in_one,
    is_notebook,
    md_text,
    printmd,
    str2bool,
)

__all__ = [
    "BibLookup",
    "bib_lookuper",
]


if is_notebook():
    print_func = printmd
    process_text = md_text
    newline = "<br/>"
    whitespace = "&nbsp;"
else:
    print_func = print
    process_text = color_text
    newline = "\n"
    whitespace = " "

warnings.simplefilter("ignore", MarkupResemblesLocatorWarning)


class BibLookup(ReprMixin):
    """The look-up class for Bib entries.

    This package is inspired by [1]_ written in JavaScript. In addition to
    the RESTful API provided by doi.org, arXiv also provides a RESTful API
    as described in [2]_. This package also uses the RESTful API provided
    by these providers to look up Bib entries. For knowledge of the bibtex,
    please refer to [5]_ and [6]_.

    Parameters
    ----------
    align : {"middle", "left", "left-middle", "left_middle"}, optional
        Alignment of the final output,
        by default "middle", case insensitive.
    ignore_fields : str or Sequence[str], optional
        Fields to be ignored in the final output,
        case insensitive, by default ["url", "abstract"].
        If is "none", no field will be ignored.
    output_file : str or pathlib.Path, optional,
        The file to save the lookup results.
        Append mode is used if the file exists.
    email : str, optional
        Email for querying PubMed publications
    kwargs : dict, optional
        Additional key word arguments, including

        - "verbose": int,
          default 0, verbose level for printing.
        - "ordering": sequence of str,
          default ["author", "title", "journal", "booktitle"],
          ordering of the fields in the final output,
          case insensitive.
        - "arxiv2doi": bool,
          default True,
          whether to convert arXiv ID to DOI to look up.
        - "format": str,
          default "bibtex", case insensitive,
          format of the final output,
          only "bibtex" format lookup results will be saved in internal cache.
        - "style": str,
          default "apa", case insensitive,
          style of the final output,
          valid only when "format" is "text".
        - "timeout": float,
          default 6.0,
          timeout for requests.
        - "ignore_errors": bool,
          default False,
          whether to ignore errors.
        - "cache_limit": int or np.inf or None,
          default 1e6,
          maximum number of items in the internal cache.

    Example
    -------
    >>> bl = BibLookup(align="middle")
    >>> res = bl("1707.07183")
    @article{wen2017_1707.07183v2,
       author = {Hao Wen and Chunhui Liu},
        title = {Counting Multiplicities in a Hypersurface over a Number Field},
      journal = {arXiv preprint arXiv:1707.07183v2},
         year = {2017},
        month = {7},
    }
    >>> bl("10.1109/CVPR.2016.90")
    @inproceedings{He_2016,
         author = {Kaiming He and Xiangyu Zhang and Shaoqing Ren and Jian Sun},
          title = {Deep Residual Learning for Image Recognition},
      booktitle = {2016 {IEEE} Conference on Computer Vision and Pattern Recognition ({CVPR})},
            doi = {10.1109/cvpr.2016.90},
           year = {2016},
          month = {6},
      publisher = {{IEEE}},
    }
    >>> bl("10.23919/cinc53138.2021.9662801", align="left-middle")
    @inproceedings{Wen_2021,
      author    = {Hao Wen and Jingsu Kang},
      title     = {Hybrid Arrhythmia Detection on Varying-Dimensional Electrocardiography: Combining Deep Neural Networks and Clinical Rules},
      booktitle = {2021 Computing in Cardiology ({CinC})},
      doi       = {10.23919/cinc53138.2021.9662801},
      year      = {2021},
      month     = {9},
      publisher = {{IEEE}},
    }

    TODO
    ----
    1. ~~add CLI support;~~
    2. use eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi for PubMed, as in [3]_;
    3. try using google scholar api described in [4]_ (unfortunately [4]_ is charged);
    4. ~~use `Flask` to write a simple browser-based UI;~~ (done with `streamlit`)
    5. make `__call__` method asynchronised using `asyncio` and `aiohttp` or `httpx`;

    WARNING
    -------
    Many journals have specific requirements for the Bib entries,
    for example, the title and/or journal (and/or booktitle), etc. should be **capitalized**,
    which could not be done automatically as some abbreviations in title
    should have characters all in the upper case,
    some should have characters all in in the lower case,
    and some others should have mixed cases (e.g. `pFedMe`).
    This should be corrected by the user himself **if necessary**,
    and remember to enclose such fields with **double curly braces**.

    References
    ----------
    .. [1] https://github.com/davidagraf/doi2bib2
    .. [2] https://arxiv.org/help/api
    .. [3] https://github.com/mfcovington/pubmed-lookup/
    .. [4] https://serpapi.com/google-scholar-cite-api
    .. [5] https://www.bibtex.com/
    .. [6] http://tug.ctan.org/info/biblatex-cheatsheet/biblatex-cheatsheet.pdf

    """

    __URL__ = dict(
        doi="https://doi.org/",
        pm="http://www.pubmedcentral.nih.gov/utils/idconv/v1.0/?format=json&ids=",
        arxiv="http://export.arxiv.org/api/query?id_list=",
    )
    __name__ = "BibLookup"

    def __init__(
        self,
        align: Optional[str] = None,
        ignore_fields: Optional[Union[str, Sequence[str]]] = None,
        output_file: Optional[Union[str, Path]] = None,
        email: Optional[str] = None,
        **kwargs,
    ) -> None:
        bl_config = deepcopy(_DEFAULT_CONFIG)
        if _CONFIG_FILE.exists():
            # if config file exists, update current config
            bl_config.update(json.loads(_CONFIG_FILE.read_text()))
        # update current config with user-defined config
        bl_config.update(kwargs)

        self.align = (align or bl_config["align"]).lower()
        assert self.align in [
            "middle",
            "left",
            "left-middle",
            "left_middle",
        ], f"`align` must be one of ['middle', 'left', 'left-middle', 'left_middle'], but got `{self.align}`"
        self.output_file = Path(output_file).resolve() if output_file is not None else None
        if self.output_file is not None:
            assert self.output_file.suffix == ".bib", f"`output_file` must be a .bib file, but got `{self.output_file}`"
            self.output_file.parent.mkdir(parents=True, exist_ok=True)
        self.__cached_lookup_results = OrderedDict()
        self.email = email or bl_config["email"]
        if ignore_fields is None:
            ignore_fields = bl_config["ignore_fields"]
        if isinstance(ignore_fields, str):
            if ignore_fields.lower() == "none":
                self._ignore_fields = []
            else:
                self._ignore_fields = [ignore_fields.lower()]
        else:
            self._ignore_fields = [k.lower() for k in ignore_fields]
        colon = "[\\s]*:[\\s]*"
        # NOTE when applying `re.search`, all strings are converted to lower cases
        # DOI examples:
        # "10.7555/JBR.28.20130191" (a counter example that several bib fields are missing)
        self.__doi_pattern_prefix = "doi[\\s]*:[\\s]*|(?:https?:\\/\\/)?(?:dx\\.)?doi\\.org\\/"
        self.__doi_pattern = f"^(?:{self.__doi_pattern_prefix})?10\\..+\\/.+$"
        # PubMed examples:
        # "22331878" or
        # "http://www.ncbi.nlm.nih.gov/pubmed/22331878"
        self.__pmid_pattern_prefix = f"pmid{colon}|pmcid{colon}"  # and pmcid
        # self.__pmid_pattern = f"^(?:{self.__pmid_pattern_prefix})?(?:\\d+|pmc\\d+(?:\\.\\d+)?)$"
        self.__pmurl_pattern_prefix = (
            "(?:https?:\\/\\/)?(?:pubmed\\.ncbi\\.nlm\\.nih" "\\.gov\\/|www\\.ncbi\\.nlm\\.nih\\.gov\\/pubmed\\/)"
        )
        # self.__pmurl_pattern = f"^(?:{self.__pmurl_pattern_prefix})?(?:\\d+|pmc\\d+(?:\\.\\d+)?)(?:\\/)?$"
        self.__pm_pattern_prefix = f"{self.__pmurl_pattern_prefix}|{self.__pmid_pattern_prefix}"
        self.__pm_pattern = f"^(?:{self.__pm_pattern_prefix})?(?:\\d+|pmc\\d+(?:\\.\\d+)?)(?:\\/)?$"
        # arXiv examples:
        # "arXiv:1501.00001v1", "arXiv:cs/0012022"
        self.__arxiv_pattern_prefix = f"((?:(?:(?:https?:\\/\\/)?arxiv.org\\/)?abs\\/)|(arxiv{colon}))"
        self.__arxiv_pattern = f"^(?:{self.__arxiv_pattern_prefix})?(?:([\\w\\-]+\\/\\d+)|(\\d+\\.\\d+(v(\\d+))?))$"
        # self.__arxiv_pattern_old = f"^(?:{self.__arxiv_pattern_prefix})?[\\w\\-]+\\/\\d+$"
        self.__default_err = "Not Found"
        self.__network_err = "Network Error"
        self.__timeout_err = "Timeout Error"

        self.__header_pattern = "^@(?P<entry_type>\\w+)\\{(?P<label>[^,]+)"

        self.ignore_errors = str2bool(bl_config["ignore_errors"])
        self.timeout = float(bl_config["timeout"])
        self._arxiv2doi = str2bool(bl_config["arxiv2doi"])
        self._format = bl_config["format"].lower()
        if self._format != "bibtex" and not self._arxiv2doi:
            warnings.warn(
                f"format `{self._format}` is supported only when `arxiv2doi` is True. `arxiv2doi` is set to True.",
                RuntimeWarning,
            )
            self._arxiv2doi = True
        self._style = bl_config["style"].lower()
        self.verbose = int(bl_config["verbose"])
        self.print_result = str2bool(bl_config["print_result"])
        self._ordering = bl_config["ordering"]
        self._ordering = [k.lower() for k in self._ordering]
        self._comment_pattern = re.compile(r"^%")
        if isinstance(bl_config["cache_limit"], (int, float, np.generic)):
            self.__cache_limit = bl_config["cache_limit"] if bl_config["cache_limit"] >= 0 else np.inf
        elif bl_config["cache_limit"] is None or bl_config["cache_limit"] in ["None", "none", "inf", "Inf", "INF"]:
            self.__cache_limit = np.inf
        else:
            raise ValueError(
                "`cache_limit` must be a non-negative number or infinity or `None` or `inf`, "
                f"but got `{bl_config['cache_limit']}`"
            )

        self.__field_pattern = f""",\\s*({"|".join(list(BIB_FIELDS))})\\s*=\\s*"""

        self.__info_color = "blue"
        self.__err_color = "red"
        self.__err_fontsize = "large"

        self.__doi_format_headers = {  # from habanero
            "rdf-xml": "application/rdf+xml",
            "turtle": "text/turtle",
            "text": "text/x-bibliography",
            "ris": "application/x-research-info-systems",
            "bibtex": "application/x-bibtex",
            "crossref-xml": "application/vnd.crossref.unixref+xml",
            "datacite-xml": "application/vnd.datacite.datacite+xml",
            "bibentry": "application/x-bibtex",
            "crossref-tdm": "application/vnd.crossref.unixsd+xml",
        }
        assert (
            self._format in self.__doi_format_headers
        ), f"`format` must be one of `{list(self.__doi_format_headers)}`, but got `{self._format}`"

        self.__exceptional_doi_domains = ["cnki"]

        self.session = requests.Session()
        for v in self.__URL__.values():
            self.session.mount(
                v.replace(v.split("/")[-1], ""),
                requests.adapters.HTTPAdapter(pool_connections=20, max_retries=2),
            )

    def __call__(
        self,
        identifier: Union[Path, str, Sequence[str]],
        align: Optional[str] = None,
        ignore_fields: Optional[Union[str, Sequence[str]]] = None,
        label: Optional[Union[str, Sequence[str]]] = None,
        arxiv2doi: Optional[bool] = None,
        print_result: Optional[bool] = None,
        timeout: Optional[float] = None,
        ignore_errors: Optional[bool] = None,
        format: Optional[str] = None,
        style: Optional[str] = None,
        verbose: Optional[int] = None,
    ) -> Union[str, type(None)]:
        """Look up publication(s) and return the result.

        Parameters
        ----------
        identifier : pathlib.Path or str or Sequence[str]
            Identifier of publication(s),
            can be DOI, PMID (or url), PMCID (or url), arXiv id, etc.;
            or path to a file containing identifiers.
        align : str, optional
            Alignment of the final output, case insensitive.
            If specified, `self.align` is ignored.
        ignore_fields : str or Sequence[str], optional
            Fields to be ignored in the final output, case insensitive.
            If specified, `self._ignore_fields` is ignored.
            If is "none", no field will be ignored.
        label : str or Sequence[str], optional
            Label(s) of the publication(s).
            If specified, the label(s) provided by the source is/are ignored.
        arxiv2doi : bool, optional
            Whether to convert arXiv ID to DOI to look up.
            If specified, `self._arxiv2doi` is ignored.
        print_result : bool, optional
            Whether to print the final output.
            if specified, `self.print_result` is ignored.
        timeout : float, optional
            timeout for the network request.
            If specified, `self.timeout` is ignored.
        ignore_errors : bool, optional
            Whether to ignore errors.
            If specified, `self.ignore_errors` is ignored.
        format : str, optional
            Format of the final output.
            If specified, `self._format` is ignored.
        style : str, optional
            Style of the final output.
            If specified, `self._style` is ignored.
        verbose : int, optional
            Verbosity level for printing.
            If specified, `self.verbose` is ignored.

        Returns
        -------
        res : str or None
            The final output in the ``str`` format;
            if `print_result` or `self.print_result` is True,
            the output is printed and ``None`` is returned.

        """
        original_verbose = self.verbose
        if verbose is not None:
            self.verbose = verbose
        print_result = self.print_result if print_result is None else print_result
        ignore_errors = self.ignore_errors if ignore_errors is None else ignore_errors
        format = self._format if format is None else format
        style = self._style if style is None else style
        if isinstance(identifier, Path):
            identifier = [line for line in identifier.read_text().splitlines() if len(line) > 0]
            return self(
                identifier,
                align,
                ignore_fields,
                label,
                arxiv2doi,
                print_result,
                timeout,
                ignore_errors,
                format,
                style,
                verbose,
            )
        if isinstance(identifier, str):
            if Path(identifier).exists():
                return self(
                    Path(identifier),
                    align,
                    ignore_fields,
                    label,
                    arxiv2doi,
                    print_result,
                    timeout,
                    ignore_errors,
                    format,
                    style,
                    verbose,
                )
        elif isinstance(identifier, Sequence):
            assert all(
                [isinstance(i, str) for i in identifier]
            ), f"`identifier` must be a string or a sequence of strings, but got `{identifier}`"
            if label is not None:
                assert (
                    not isinstance(label, str) and len(label) == len(identifier) and all([isinstance(i, str) for i in label])
                ), "`label` must be a sequence of strings of the same length as `identifier`"
            else:
                label = [None] * len(identifier)
            if print_result:
                for idx, item in enumerate(identifier):
                    self(
                        item,
                        align,
                        ignore_fields,
                        label[idx],
                        arxiv2doi,
                        print_result,
                        timeout,
                        ignore_errors,
                        format,
                        style,
                        verbose,
                    )
                return
            else:
                return "\n".join(
                    self(
                        item,
                        align,
                        ignore_fields,
                        label[idx],
                        arxiv2doi,
                        print_result,
                        timeout,
                        ignore_errors,
                        format,
                        style,
                        verbose,
                    )
                    for idx, item in enumerate(identifier)
                ).strip("\n")
        else:
            raise TypeError(f"`identifier` must be a string or a sequence of strings, but got `{identifier}`.")

        category, feed_content, idtf = self._obtain_feed_content(identifier, arxiv2doi, format, style, timeout)
        if category != "doi" and format not in ["bibentry", "bibtex"]:
            warnings.warn(
                f"format `{format}` is not supported for `{category}`, thus ignored.",
                RuntimeWarning,
            )
        if category == "doi":
            res = self._handle_doi(feed_content)
        elif category == "pm":
            res = self._handle_pm(feed_content)
        elif category == "arxiv":
            res = self._handle_arxiv(feed_content)
        elif category == "error" or re.findall("|".join(self.__exceptional_doi_domains), idtf):
            res = self.default_err

        res = self._handle_network_error(res)

        if res not in self.lookup_errors:
            if format in ["bibtex", "bibentry"]:
                try:
                    res = self._to_bib_item(res, idtf, align, ignore_fields, label)
                    self.__cached_lookup_results[identifier] = res
                    if len(self.__cached_lookup_results) > self.__cache_limit:
                        self.__cached_lookup_results.popitem(last=False)
                except Exception:
                    res = self.default_err
            elif format == "text":
                res = BeautifulSoup(res, "html.parser").get_text()

        if self.verbose >= 1:
            if res in self.lookup_errors:
                print_func(process_text(res, self.__err_color, font_size=self.__err_fontsize))
            else:
                print(res)
        self.verbose = original_verbose

        if res in self.lookup_errors and ignore_errors:
            res = ""

        if print_result:
            if res:
                print(res)
            return
        return str(res)

    def _obtain_feed_content(
        self,
        identifier: str,
        arxiv2doi: Optional[bool] = None,
        format: Optional[str] = None,
        style: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> Tuple[str, dict, str]:
        """Obtain feed content using GET or POST method.

        Parameters
        ----------
        identifier : str
            Identifier of a publication,
            can be DOI, PMID (or url), PMCID (or url), arXiv id.
        arxiv2doi : bool, optional
            Whether to convert arXiv ID to DOI to look up.
            If specified, `self._arxiv2doi` is ignored.
        format : str, optional
            Format of the final output.
            If specified, `self._format` is ignored.
        style: str, optional
            Style of the final output.
            If specified, `self._style` is ignored.
        timeout : float, optional
            timeout for the network request.
            If specified, `self.timeout` is ignored.

        Returns
        -------
        category : {"doi", "pm", "arxiv", "error"}
            Category of the identifier,
            or "error" if the identifier is invalid.
        fc : dict
            Feed content for GET or POST method.
        idtf : str
            Simplified identifier of the publication.

        """
        idtf = identifier.lower().strip()
        _arxiv2doi = self._arxiv2doi if arxiv2doi is None else arxiv2doi
        _format = self._format if format is None else format
        _style = self._style if style is None else style
        fc = {"timeout": self.timeout if timeout is None else timeout}
        if re.search(self.doi_pattern, idtf):
            idtf = re.sub(
                self.doi_pattern_prefix,
                "",
                idtf,
            ).strip("/")
            _type = f"{self.__doi_format_headers[_format]}; charset=utf-8"
            if _format == "text":
                _type = f"{_type}; style = {style}"
            headers = {"Accept": _type}
            url = self.__URL__["doi"] + idtf
            fc.update(
                {
                    "url": url,
                    "headers": headers,
                    "allow_redirects": True,
                }
            )
            category = "doi"
        elif re.search(self.pm_pattern, idtf):
            idtf = re.sub(
                self.pm_pattern_prefix,
                "",
                idtf,
            ).strip("/")
            url = self.__URL__["pm"] + idtf
            fc.update(
                {
                    "url": url,
                }
            )
            category = "pm"
        elif re.search(self.arxiv_pattern, idtf):
            idtf = re.sub(
                self.arxiv_pattern_prefix,
                "",
                idtf,
            ).strip("/")
            url = self.__URL__["arxiv"] + idtf
            fc.update(
                {
                    "url": url,
                }
            )
            category = "arxiv"
            # version should be removed from `idtf`
            idtf = re.sub("v\\d+", "", idtf)
            if _arxiv2doi:
                idtf = f"10.48550/arXiv.{idtf}"
                return self._obtain_feed_content(idtf)
        else:
            warnings.warn(
                "unrecognized `indentifier` (none of 'doi', 'pmid', 'pmcid', 'pmurl', 'arxiv').",
                RuntimeWarning,
            )
            category, fc = "error", {}
        if self.verbose > 1:
            print_func(f"category = {process_text(category, self.__info_color)}")
            print_func(f"feed content = {fc}")
            print_func(f"simplified identifier = {process_text(idtf, self.__info_color)}")
        return category, fc, idtf

    def _handle_doi(self, feed_content: dict) -> str:
        """Handle a DOI query using POST method.

        Parameters
        ----------
        feed_content : dict
            The content to feed to POST method.

        Returns
        -------
        res : str
            Decoded query result.

        """
        try:
            r = self.session.post(**feed_content)
            res = r.content.decode("utf-8")
        except requests.Timeout:
            res = self.timeout_err
        except requests.RequestException:
            res = self.network_err
        if self.verbose > 3:
            print_func(f"via `_handle_doi`, fetched content = {res}")
        return res

    def _handle_pm(self, feed_content: dict) -> str:
        """Handle a PubMed query using POST method.

        Parameters
        ----------
        feed_content : dict
            The content to feed to POST method.

        Returns
        -------
        res : str
            Decoded query result.

        """
        try:
            r = self.session.post(**feed_content)
            if self.verbose > 1:
                print_func(r.json())
            mid_res = r.json()["records"][0]
        except requests.Timeout:
            res = self.timeout_err
            return res
        except requests.RequestException:
            res = self.network_err
            return res
        doi = mid_res.get("doi", "")
        if self.verbose > 3:
            print_func(f"doi = {doi}")
        if doi:
            _, feed_content, _ = self._obtain_feed_content(doi, timeout=feed_content.get("timeout", None))
            res = self._handle_doi(feed_content)
        else:
            res = self.default_err
        return res

    def _handle_arxiv(self, feed_content: dict) -> Union[str, Dict[str, str]]:
        """Handle a arXiv query using GET method.

        Parameters
        ----------
        feed_content : dict
            The content to feed to GET method.

        Returns
        -------
        res : dict or str
            Decoded and parsed query result.

        """
        try:
            r = self.session.get(**feed_content)
        except requests.Timeout:
            res = self.timeout_err
            return res
        except requests.RequestException:
            res = self.network_err
            return res
        parsed = feedparser.parse(r.content.decode("utf-8")).entries[0]
        if self.verbose > 3:
            print_func(parsed)
        title = re.sub("[\\s]+", " ", parsed["title"])  # sometimes this field has "\n"
        if title == "Error":
            res = self.default_err
            return res
        arxiv_id = parsed["id"].split("arxiv.org/abs/")[-1]
        year = parsed["published_parsed"].tm_year
        res = {"title": title}
        # it seems that surnames are put in the last position of full names by arXiv
        authors = [item["name"] for item in parsed["authors"]]
        res["author"] = " and ".join(authors)
        res["year"] = year
        res["month"] = parsed["published_parsed"].tm_mon
        res["journal"] = f"arXiv preprint arXiv:{arxiv_id}"
        res["label"] = f"{parsed['authors'][0]['name'].split(' ')[-1].lower()}{year}_{arxiv_id}"
        res["entry_type"] = "article"
        res["doi"] = re.sub("[vV]\\d+$", "", f"10.48550/arXiv.{arxiv_id}")
        return res

    def _handle_network_error(self, res: str) -> str:
        """Handle network error.

        Parameters
        ----------
        res : str
            The query result.

        Returns
        -------
        str
            Error message.

        """
        if "DOI Not Found" in res:
            return self.default_err
        elif any([item in res for item in NETWORK_ERROR_MESSAGES]):
            return self.network_err
        return res

    def _to_bib_item(
        self,
        res: Union[str, Dict[str, str]],
        identifier: Optional[str] = None,
        align: Optional[str] = None,
        ignore_fields: Optional[Union[str, Sequence[str]]] = None,
        label: Optional[str] = None,
    ) -> BibItem:
        """Convert a query result to a :class:`BibItem` instance.

        NOTE that this method is idempotent.

        Parameters
        ----------
        res : str or dict
            Result obtained via GET or POST method,
            or read from a file.
        identifier : str, optional
            Identifier of a publication,
            can be DOI, PMID (or url), PMCID (or url), arXiv id, etc.
            If not provided, "label" from the result will be used as `identifier`.
        align : str, optional
            Alignment of the final output, case insensitive.
            If specified, `self.align` is ignored.
        ignore_fields : str or Sequence[str], optional
            Fields to be ignored in the final output, case insensitive.
            If specified, `self._ignore_fields` is ignored.
            If is "none", no field will be ignored.
        label : str, optional
            Label of the publication.

        Returns
        -------
        bib_item : BibItem
            A :class:`BibItem` instance converted from `res`.

        """
        if ignore_fields is None:
            _ignore_fields = self.ignore_fields
        elif isinstance(ignore_fields, str):
            if ignore_fields.lower() == "none":
                _ignore_fields = []
            else:
                _ignore_fields = [ignore_fields.lower()]
        else:
            _ignore_fields = [k.lower() for k in ignore_fields]
        _align = (align or self.align).lower()
        assert _align in [
            "middle",
            "left",
            "left-middle",
            "left_middle",
        ], f"`align` must be one of ['middle', 'left', 'left-middle', 'left_middle'], but got `{_align}`"
        if isinstance(res, str):
            # normalize `res` so that all white spaces (including "\n") are replaced by a single space
            res = re.sub("\\s+", " ", res)
            # raw text is not split by "\n" but by ", " now
            lines = []
            split_indices = [m.start() for m in re.finditer(self.__field_pattern, res.lower())]
            split_indices.insert(0, 0)
            for idx in range(len(split_indices) - 1):
                lines.append(res[split_indices[idx] : split_indices[idx + 1]])
            lines.append(res[split_indices[-1] :])
            if re.findall(self.__field_pattern, lines[-1].lower()):
                lines.append("}")
            lines = [re.sub("\\}[^\\w]+\\}", "}", line.strip(", ")) for line in lines if len(line.strip(", ")) > 0]
            header_dict = list(re.finditer(self.bib_header_pattern, lines[0]))[0].groupdict()
            field_dict = OrderedDict()
            for line in lines[1:-1]:
                key, *val = line.strip().split("=")  # urls might contain "="
                val = "=".join(val)
                if key.strip().lower() in BIB_FIELDS:
                    # field_dict[key.strip()] = val.strip(", ")
                    field_dict[key.strip()] = val
                else:
                    # line breaks inside a field
                    key = list(field_dict.keys())[-1]
                    field_dict[key] += f" {line.strip()}"
        elif isinstance(res, dict):
            header_dict = {k.strip(): str(v).strip(", ") for k, v in res.items() if k in ["entry_type", "label"]}
            field_dict = OrderedDict(
                {k.strip(): str(v).strip(", ") for k, v in res.items() if k not in ["entry_type", "label"]}
            )

        # replace the "_" in title with "\_"
        if "title" in field_dict:
            field_dict["title"] = field_dict["title"].replace("_", r"\_").replace(r"\\_", r"\_")

        # if label is provided, overwrite the label in the header
        if label:
            assert isinstance(label, str), "`label` must be a string"
            header_dict["label"] = label

        # all field names to lower case,
        # and ignore the fields in the list `_ignore_fields`
        # field_dict = {k.lower(): v.strip('{}", ') for k, v in field_dict.items() if k.lower() not in _ignore_fields}
        # the above treatment might result in errors when the leading or trailing words are enclosed by braces
        # e.g. "{{IDH1} and {IDH2} mutations in postoperative diffuse glioma-associated {epilepsy}}"
        field_dict = {k.lower(): v.strip(", ") for k, v in field_dict.items() if k.lower() not in _ignore_fields}
        # take off at most one pair of double quotes or single quotes or braces at the beginning and the end of the value
        for k, v in field_dict.items():
            # if the field ends with a } but without a leading {, remove the trailing }
            # this resolves the issue with fetched content that ends with, for example, "month=jun }"
            if field_dict[k].endswith("}") and not field_dict[k].startswith("{"):
                field_dict[k] = field_dict[k][:-1].strip()
            tmp_v = re.sub("\\{[^\\{\\}]*\\}", "", v).strip()
            if v.startswith('"') and v.endswith('"'):
                field_dict[k] = v[1:-1]
            elif v.startswith("'") and v.endswith("'"):
                field_dict[k] = v[1:-1]
            elif (tmp_v.startswith("{") and tmp_v.endswith("}")) or len(tmp_v) == 0:
                field_dict[k] = v[1:-1]
            field_dict[k] = BeautifulSoup(field_dict[k], "html.parser").get_text()
            # replace the "&" in field content with "\&"
            field_dict[k] = field_dict[k].replace("&", r"\&").replace(r"\\&", r"\&")

        # re-order the fields according to the list `self.ordering`
        _ordering = self.ordering + [k for k in field_dict if k not in self.ordering]
        _ordering = [k for k in _ordering if k in field_dict]
        field_dict = OrderedDict((k, field_dict[k]) for k in _ordering)

        # to BibItem
        bib_item = BibItem(
            identifier=identifier or header_dict["label"],
            entry_type=header_dict["entry_type"],
            fields=field_dict,
            label=header_dict["label"],
            align=_align,
        )
        return bib_item

    @property
    def doi_pattern(self) -> str:
        return self.__doi_pattern

    @property
    def doi_pattern_prefix(self) -> str:
        return self.__doi_pattern_prefix

    @property
    def arxiv_pattern(self) -> str:
        return self.__arxiv_pattern

    @property
    def arxiv_pattern_prefix(self) -> str:
        return self.__arxiv_pattern_prefix

    @property
    def pm_pattern(self) -> str:
        return self.__pm_pattern

    @property
    def pm_pattern_prefix(self) -> str:
        return self.__pm_pattern_prefix

    @property
    def pubmed_pattern(self) -> str:
        return self.__pm_pattern

    @property
    def pubmed_pattern_prefix(self) -> str:
        return self.__pm_pattern_prefix

    @property
    def bib_header_pattern(self) -> str:
        return self.__header_pattern

    @property
    def default_err(self) -> str:
        return self.__default_err

    @property
    def network_err(self) -> str:
        return self.__network_err

    @property
    def timeout_err(self) -> str:
        return self.__timeout_err

    @property
    def lookup_errors(self) -> List[str]:
        return [self.default_err, self.network_err, self.timeout_err]

    @property
    def ignore_fields(self) -> List[str]:
        return self._ignore_fields

    @property
    def ordering(self) -> List[str]:
        return self._ordering

    @property
    def format(self) -> str:
        return self._format

    @property
    def style(self) -> str:
        return self._style

    @property
    def cache_limit(self) -> Union[int, float]:
        return self.__cache_limit

    def debug(self) -> None:
        self.verbose = 2

    def save(
        self,
        identifiers: Union[int, str, Sequence[str], Sequence[int]] = None,
        output_file: Optional[Union[str, Path]] = None,
        skip_existing: Union[bool, str] = True,
    ) -> None:
        """Save bib items corresponding to the identifiers
        to the output file.

        Parameters
        ----------
        identifiers : int or str or Sequence[str] or Sequence[int], optional
            The bib corresponding to the identifiers are to be saved,
            defaults to all.
        output_file : str or pathlib.Path, optional
            The output file, defaults to `self.output_file`.
            If specified, `self.output_file` is ignored.
        skip_existing : {True, False, "strict"}, default True
            Whether to skip existing bib items in the output file,
            by default True.
            If True or "strict", skip existing bib items in the output file.
            For "strict" comparison of instances of :class:`BibItem`,
            ref. the :meth:`BibItem.__eq__` method.

        WARNING
        -------
        Saved bib items will be removed from the cache.

        """
        _output_file = output_file or self.output_file
        assert _output_file is not None, "`output_file` is not specified"
        _output_file = Path(_output_file).resolve()
        assert _output_file.suffix == ".bib", f"`output_file` must be a .bib file, but got `{_output_file}`"
        _output_file.parent.mkdir(parents=True, exist_ok=True)

        if identifiers is None:
            identifiers = list(self.__cached_lookup_results)
        elif isinstance(identifiers, int):
            identifiers = [self[identifiers]]
        elif isinstance(identifiers, str):
            identifiers = [identifiers]
        elif isinstance(identifiers, Sequence) and all([isinstance(i, int) for i in identifiers]):
            identifiers = [self[i] for i in identifiers]
        assert isinstance(identifiers, Sequence) and all(
            [isinstance(i, str) for i in identifiers]
        ), "`identifiers` must be a string (or an integer) or a sequence of strings (or integers)"
        identifiers = [i for i in identifiers if i in self.__cached_lookup_results]

        # check if the bib item is already existed in the output file
        if skip_existing:
            existing_bib_items = self.read_bib_file(_output_file)
            identifiers = [
                i
                for i in identifiers
                if not any(
                    [
                        self[i].__eq__(
                            bib_item,
                            strict=(isinstance(skip_existing, str) and skip_existing.lower() == "strict"),
                        )
                        for bib_item in existing_bib_items
                    ]
                )
            ]

        if len(identifiers) == 0:
            print_func(
                f"no bib item is saved to `{process_text(str(_output_file), self.__info_color)}` "
                "because all bib items are already existed in the output file, "
                "or the given identifiers are not found in the cache"
            )
            return

        with open(_output_file, "a") as f:
            f.writelines("\n".join([str(self.__cached_lookup_results[i]) for i in identifiers]) + "\n")

        print_func(f"Bib items written to `{process_text(str(_output_file), self.__info_color)}`")

        # remove saved bib items from the cache
        for i in identifiers:
            self.__cached_lookup_results.pop(i)

    def read_bib_file(
        self,
        bib_file: Optional[Union[str, Path]] = None,
        cache: bool = False,
        return_line_numbers: bool = False,
    ) -> Union[List[BibItem], Tuple[List[BibItem], List[int]]]:
        """Read bib file and return a list of bib items.

        Parameters
        ----------
        bib_file : str or pathlib.Path, optional
            The bib file to read, defaults to `self.output_file`.
        cache : bool, default False
            If True, cache the bib items.
        return_line_numbers : bool, default False
            If True, returns a tuple of ``(bib items, line numbers)``.

        Returns
        -------
        bib_items : List[BibItem] or Tuple[List[BibItem], List[int]]
            The list of bib items already existing in the bib file.

        """
        _bib_file = bib_file or self.output_file
        assert _bib_file is not None, "`bib_file` is not specified"
        _bib_file = Path(_bib_file).resolve()
        assert _bib_file.suffix == ".bib", f"`bib_file` must be a .bib file, but got `{_bib_file}`"
        if not _bib_file.exists():
            return []
        bib_items = []
        lines = []
        line_numbers = []
        for idx, line in enumerate(_bib_file.read_text().splitlines()):
            line = line.strip(", ")
            if re.match(self._comment_pattern, line) or len(line) == 0:
                continue
            if line.startswith("@"):
                line_numbers.append(idx)
                if len(lines) > 0:
                    if not re.search("bstctl", lines[0].lower()):
                        # ignore_fields should be set empty
                        # to keep it unchanged
                        bib_item = self._to_bib_item(",\n".join(lines), ignore_fields=[])
                        bib_items.append(bib_item)
                        if cache:
                            self.__cached_lookup_results[bib_item.identifier] = bib_item
                    lines = []
            lines.append(line)
        if len(lines) > 0 and not re.search("bstctl", lines[0].lower()):
            bib_item = self._to_bib_item(",\n".join(lines), ignore_fields=[])
            bib_items.append(bib_item)
            if cache:
                self.__cached_lookup_results[bib_item.identifier] = bib_item
        if return_line_numbers:
            return bib_items, line_numbers
        return bib_items

    def pop(self, identifiers: Union[int, str, Sequence[str], Sequence[int]]) -> None:
        """Remove the bib corresponding to the identifiers
        from the cache.

        Parameters
        ----------
        identifiers : int or str or  Sequence[str] or Sequence[int]
            The identifiers to be removed from the cache.

        Returns
        -------
        None

        """
        if isinstance(identifiers, int):
            identifiers = [self[identifiers]]
        elif isinstance(identifiers, str):
            identifiers = [identifiers]
        elif isinstance(identifiers, Sequence) and all([isinstance(i, int) for i in identifiers]):
            identifiers = [self[i] for i in identifiers]
        assert isinstance(identifiers, Sequence) and all(
            [isinstance(i, str) for i in identifiers]
        ), "`identifiers` must be a string (or an integer) or a sequence of strings (or integers)"
        for i in identifiers:
            self.__cached_lookup_results.pop(i, None)

    def clear_cache(self) -> None:
        """Helper function to clear the cached bib items."""
        for item in list(self):
            self.pop(item)

    def print(self) -> None:
        """Print the bib items in the cache."""
        print(self.get_cache(string_format=True))

    def get_cache(self, string_format: bool = False) -> Union[str, OrderedDict]:
        """Get all bib items in the cache.

        Parameters
        ----------
        string_format : bool, default False
            Whether to return the bib items in string format,
            or the ordered dict of cached instances of :class:`BibItem`.

        Returns
        -------
        str or OrderedDict
            The bib items in string format,
            or the ordered dict of cached instances of :class:`BibItem`.

        """
        if string_format:
            return "\n".join(
                [
                    f"% index: {idx}\n" + f"% identifier: {self[item].identifier}\n" + str(self[item])
                    for idx, item in enumerate(self)
                ]
            )
        else:
            return self.__cached_lookup_results

    def __getitem__(self, index: Union[int, str]) -> str:
        if isinstance(index, int):
            return list(self.__cached_lookup_results)[index]
        elif isinstance(index, str):
            assert index in self.__cached_lookup_results, f"`{index}` not found"
            return self.__cached_lookup_results[index]
        else:
            raise TypeError(f"`index` should be an integer or a string, not `{type(index)}`")

    def __len__(self) -> int:
        return len(self.__cached_lookup_results)

    def extra_repr_keys(self) -> List[str]:
        return ["align", "output_file", "ignore_fields"] + super().extra_repr_keys()

    def check_bib_file(self, bib_file: Union[str, Path]) -> List[int]:
        """Check if the bib items in a bib file are valid,

        This is done
        by checking if they have all the required fields.

        Parameters
        ----------
        bib_file : str or pathlib.Path
            The bib file to check.

        Returns
        -------
        err_lines : List[int]
            The starting line numbers of the invalid bib items.

        """
        _bib_file = Path(bib_file).resolve()
        assert _bib_file.exists() and _bib_file.suffix == ".bib", "Not a valid Bib file"
        bib_items, line_numbers = self.read_bib_file(bib_file=bib_file, cache=False, return_line_numbers=True)
        err_lines = set()
        for ln, bi in zip(line_numbers, bib_items):
            try:
                bi.check_required_fields()
            except AssertionError:
                print_func(
                    f"Bib item \042{process_text(bi.label, self.__err_color, font_size=self.__err_fontsize)}\042{newline}"
                    f"{whitespace * 4}starting from line {ln} is not valid.{newline}"
                    f"{whitespace * 4}Bib item of entry type "
                    f"\042{process_text(bi.entry_type, self.__err_color, font_size=self.__err_fontsize)}\042 "
                    f"should have the following fields:{newline}{whitespace * 4}"
                    + process_text(
                        f"{DF_BIB_ENTRY_TYPES[DF_BIB_ENTRY_TYPES.entry_type == bi.entry_type].iloc[0].required_fields}",
                        self.__info_color,
                    )
                    + newline
                )
                err_lines.add(ln)
        # check for bib items with duplicate labels
        for i, bi in enumerate(bib_items[:-1]):
            for j, bj in enumerate(bib_items[i + 1 :]):
                j += i + 1
                if bi.label == bj.label:
                    ln_i = line_numbers[i]
                    ln_j = line_numbers[j]
                    err_lines.update({ln_i, ln_j})
                    print_func(
                        f"Bib items \042{process_text(bi.label, self.__err_color, font_size=self.__err_fontsize)}\042 "
                        f"starting from line {process_text(str(ln_i), self.__err_color, font_size=self.__err_fontsize)}{newline}"
                        f"{whitespace * 6}and \042{process_text(bi.label, self.__err_color, font_size=self.__err_fontsize)}\042 "
                        f"starting from line {process_text(str(ln_j), self.__err_color, font_size=self.__err_fontsize)} is duplicate."
                        + newline
                    )
        return sorted(err_lines)

    @staticmethod
    def simplify_bib_file(
        tex_sources: Union[Path, str, List[Union[Path, str]]],
        bib_file: Union[Path, str],
        output_file: Optional[Union[Path, str]] = None,
    ) -> str:
        """Simplify a bib file by removing all the bib items
        that are not used in the tex sources.

        Parameters
        ----------
        tex_sources : str or pathlib.Path or List[str] or List[pathlib.Path]
            The tex sources to check.
            If a single tex source file path is given,
            it is considered as the entry file of the tex project,
            and `gather_tex_source_files_in_one` will be called
            to gather all the tex source files for simplification.
        bib_file : str or pathlib.Path
            The bib file to simplify.
        output_file : str or pathlib.Path, optional
            The output file to save the simplified bib file,
            defaults to ``Path(bib_file).stem + "_simplified.bib"``.

        Returns
        -------
        str
            The path of the simplified bib file in string format.

        """
        if isinstance(tex_sources, (str, Path)):
            tex_sources = [tex_sources]
        tex_sources = [Path(tex_source) for tex_source in tex_sources]
        bib_file = Path(bib_file)
        if output_file is None:
            output_file = bib_file.parent / (bib_file.stem + "_simplified.bib")
        else:
            output_file = Path(output_file)
        if output_file.exists():
            raise FileExistsError(f"Output file \042{output_file}\042 already exists")

        ref_bl = BibLookup()
        # bib_items = ref_bl.read_bib_file(bib_file, cache=True)
        ref_bl.read_bib_file(bib_file, cache=True)

        # get the labels of bib items that are cited
        cited_labels = set()
        _punctuation = "".join([s for s in punctuation if s not in "{}"])
        # citation pattern: https://fr.overleaf.com/learn/latex/Natbib_citation_styles
        citation_pattern = (
            "\\\\(?:paren)?cite(?:t|p|t\\*|p\\*|author|year)?(?:(?:\\[.+\\])?)?" f"\\{{(?P<label>[\\w\\s{_punctuation}]+)\\}}"
        )
        for tex_source in tex_sources:
            if tex_source.is_file() and len(tex_sources) == 1:
                for items in re.findall(
                    citation_pattern,
                    gather_tex_source_files_in_one(tex_source, write_file=False),
                ):
                    cited_labels.update([item.strip() for item in items.split(",")])
            elif tex_source.is_file():
                for items in re.findall(citation_pattern, tex_source.read_text()):
                    cited_labels.update([item.strip() for item in items.split(",")])
            else:  # is a directory
                for tex_file in tex_source.rglob("*.tex"):
                    for items in re.findall(citation_pattern, tex_file.read_text()):
                        cited_labels.update([item.strip() for item in items.split(",")])
        cited_identifiers = [idtf for idtf in ref_bl if ref_bl[idtf].label in cited_labels]

        # write to output file
        ref_bl.save(cited_identifiers, output_file)
        return str(output_file)


bib_lookuper = BibLookup(print_result=True)

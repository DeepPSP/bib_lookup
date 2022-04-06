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

import re
import warnings
from pathlib import Path
from collections import OrderedDict
from typing import Union, Optional, Tuple, List, Sequence, Dict, NoReturn

import requests
import feedparser

from ._bib import BibItem  # noqa: F401


__all__ = [
    "BibLookup",
]


class BibLookup(object):
    """finished, continuous improving,

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
    1. add CLI support;
    2. use eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi for PubMed, as in [3];
    3. try using google scholar api described in [4] (unfortunately [4] is charged);
    4. use `Flask` to write a simple browser-based UI;

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
    1. <a name="ref1"></a> https://github.com/davidagraf/doi2bib2
    2. <a name="ref2"></a> https://arxiv.org/help/api
    3. <a name="ref3"></a> https://github.com/mfcovington/pubmed-lookup/
    4. <a name="ref4"></a> https://serpapi.com/google-scholar-cite-api
    5. <a name="ref5"></a> https://www.bibtex.com/
    6. <a name="ref6"></a> http://tug.ctan.org/info/biblatex-cheatsheet/biblatex-cheatsheet.pdf

    """

    __name__ = "BibLookup"

    def __init__(
        self,
        align: str = "middle",
        ignore_fields: Sequence[str] = ["url"],
        output_file: Optional[Union[str, Path]] = None,
        email: Optional[str] = None,
        **kwargs,
    ) -> NoReturn:
        """

        Parameters
        ----------
        align: str, default "middle",
            alignment of the final output, case insensitive,
            can be one of "middle", "left", "left-middle", "left_middle"
        ignore_fields: sequence of str, default ["url"],
            fields to be ignored in the final output,
            case insensitive
        output_file: str or Path, optional,
            the file to save the lookup results,
            append mode is used if the file exists
        email: str, optional,
            email for querying PubMed publications
        kwargs: additional key word arguments, including
            "verbose": int,
                default 0,
            "odering": sequence of str,
                default ["author", "title", "journal", "booktitle"],
                case insensitive,

        """
        self.align = align.lower()
        assert self.align in [
            "middle",
            "left",
            "left-middle",
            "left_middle",
        ], f"align must be one of 'middle', 'left', 'left-middle', 'left_middle', but got {self.align}"
        self.output_file = (
            Path(output_file).resolve() if output_file is not None else None
        )
        if self.output_file is not None:
            assert (
                self.output_file.suffix == ".bib"
            ), f"output_file must be a .bib file, but got {self.output_file}"
            self.output_file.parent.mkdir(parents=True, exist_ok=True)
        self.__cached_lookup_results = OrderedDict()
        self.email = email
        self._ignore_fields = [k.lower() for k in ignore_fields]
        assert self.align in [
            "middle",
            "left",
            "left-middle",
            "left_middle",
        ]
        colon = "[\\s]*:[\\s]*"
        # NOTE when applying `re.search`, all strings are converted to lower cases
        # DOI examples:
        # "10.7555/JBR.28.20130191" (a counter example that several bib fields are missing)
        self.__doi_pattern_prefix = (
            "doi[\\s]*:[\\s]*|(?:https?:\\/\\/)?(?:dx\\.)?doi\\.org\\/"
        )
        self.__doi_pattern = f"^(?:{self.__doi_pattern_prefix})?10\\..+\\/.+$"
        # PubMed examples:
        # "22331878" or
        # "http://www.ncbi.nlm.nih.gov/pubmed/22331878"
        self.__pmid_pattern_prefix = f"pmid{colon}|pmcid{colon}"  # and pmcid
        # self.__pmid_pattern = f"^(?:{self.__pmid_pattern_prefix})?(?:\\d+|pmc\\d+(?:\\.\\d+)?)$"
        self.__pmurl_pattern_prefix = "(?:https?:\\/\\/)?(?:pubmed\\.ncbi\\.nlm\\.nih\\.gov\\/|www\\.ncbi\\.nlm\\.nih\\.gov\\/pubmed\\/)"
        # self.__pmurl_pattern = f"^(?:{self.__pmurl_pattern_prefix})?(?:\\d+|pmc\\d+(?:\\.\\d+)?)(?:\\/)?$"
        self.__pm_pattern_prefix = (
            f"{self.__pmurl_pattern_prefix}|{self.__pmid_pattern_prefix}"
        )
        self.__pm_pattern = (
            f"^(?:{self.__pm_pattern_prefix})?(?:\\d+|pmc\\d+(?:\\.\\d+)?)(?:\\/)?$"
        )
        # arXiv examples:
        # "arXiv:1501.00001v1", "arXiv:cs/0012022"
        self.__arxiv_pattern_prefix = (
            f"((?:(?:(?:https?:\\/\\/)?arxiv.org\\/)?abs\\/)|(arxiv{colon}))"
        )
        self.__arxiv_pattern = f"^(?:{self.__arxiv_pattern_prefix})?(?:([\\w\\-]+\\/\\d+)|(\\d+\\.\\d+(v(\\d+))?))$"
        # self.__arxiv_pattern_old = f"^(?:{self.__arxiv_pattern_prefix})?[\\w\\-]+\\/\\d+$"
        self.__default_err = "Not Found"
        self.__header_pattern = "^@(?P<entry_type>\\w+)\\{(?P<label>[^,]+)"

        self.verbose = kwargs.get("verbose", 0)
        self._ordering = kwargs.get(
            "ordering", ["author", "title", "journal", "booktitle"]
        )
        self._ordering = [k.lower() for k in self._ordering]

    def __call__(
        self, identifier: Union[Path, str, Sequence[str]], align: Optional[str] = None
    ) -> str:
        """

        Parameters
        ----------
        identifier: Path or str or sequence of str,
            identifier of a publication,
            can be DOI, PMID (or url), PMCID (or url), arXiv id, etc.
        align: str, optional,
            alignment of the final output, case insensitive,
            if specified, `self.align` is ignored

        Returns
        -------
        res: str,
            the final output in the `str` format

        """
        if isinstance(identifier, Path):
            identifier = [
                line for line in identifier.read_text().splitlines() if len(line) > 0
            ]
            return self(identifier, align)
        if isinstance(identifier, str):
            if Path(identifier).exists():
                return self(Path(identifier), align)
        elif isinstance(identifier, Sequence):
            assert all(
                [isinstance(i, str) for i in identifier]
            ), f"identifier must be a string or a sequence of strings, but got {identifier}"
            return "\n".join(self(item, align) for item in identifier)
        else:
            raise TypeError(
                f"identifier must be a string or a sequence of strings, but got {identifier}"
            )

        category, feed_content, idtf = self._obtain_feed_content(identifier)
        if category == "doi":
            res = self._handle_doi(feed_content)
        elif category == "pm":
            res = self._handle_pm(feed_content)
        elif category == "arxiv":
            res = self._handle_arxiv(feed_content)
        elif category == "error":
            res = self.default_err

        if res != self.default_err:
            res = self._to_bib_item(idtf, res, align)
            self.__cached_lookup_results[identifier] = res

        if self.verbose >= 1:
            print(res)

        return str(res)

    def _obtain_feed_content(self, identifier: str) -> Tuple[str, dict, str]:
        """

        Parameters
        ----------
        identifier: str,
            identifier of a publication,
            can be DOI, PMID (or url), PMCID (or url), arXiv id,

        Returns
        -------
        category: str,
            one of "doi", "pm", "arxiv"
        fc: dict,
            feed content to GET or POST
        idtf: str,
            simplified identifier of the publication,

        """
        idtf = identifier.lower().strip()
        if re.search(self.doi_pattern, idtf):
            idtf = re.sub(
                self.doi_pattern_prefix,
                "",
                idtf,
            ).strip("/")
            url = "https://doi.org/" + idtf
            fc = {
                "url": url,
                "headers": {"Accept": "application/x-bibtex; charset=utf-8"},
            }
            category = "doi"
        elif re.search(self.pm_pattern, idtf):
            idtf = re.sub(
                self.pm_pattern_prefix,
                "",
                idtf,
            ).strip("/")
            url = (
                "http://www.pubmedcentral.nih.gov/utils/idconv/v1.0/?format=json&ids="
                + idtf
            )
            fc = {
                "url": url,
            }
            category = "pm"
        elif re.search(self.arxiv_pattern, idtf):
            idtf = re.sub(
                self.arxiv_pattern_prefix,
                "",
                idtf,
            ).strip("/")
            url = "http://export.arxiv.org/api/query?id_list=" + idtf
            fc = {
                "url": url,
            }
            category = "arxiv"
        else:
            warnings.warn(
                "unrecognized indentifier (none of doi, pmid, pmcid, pmurl, arxiv)"
            )
            category, fc = "error", {}
        if self.verbose > 1:
            print(f"category = {category}")
            print(f"feed content = {fc}")
            print(f"simplified identifier = {idtf}")
        return category, fc, idtf

    def _handle_doi(self, feed_content: dict) -> str:
        """

        handle a DOI query using POST

        Parameters
        ----------
        feed_content: dict,
            the content to feed to POST

        Returns
        -------
        res: str,
            decoded query result

        """
        r = requests.post(**feed_content)
        res = r.content.decode("utf-8")
        if self.verbose > 1:
            print(res)
        return res

    def _handle_pm(self, feed_content: dict) -> str:
        """

        handle a PubMed query using POST

        Parameters
        ----------
        feed_content: dict,
            the content to feed to POST

        Returns
        -------
        res: str,
            decoded query result

        """
        r = requests.post(**feed_content)
        if self.verbose > 1:
            print(r.json())
        mid_res = r.json()["records"][0]
        doi = mid_res.get("doi", "")
        if self.verbose > 1:
            print(f"doi = {doi}")
        if doi:
            _, feed_content, _ = self._obtain_feed_content(doi)
            res = self._handle_doi(feed_content)
        else:
            res = self.default_err
        return res

    def _handle_arxiv(self, feed_content: dict) -> Union[str, Dict[str, str]]:
        """

        handle a arXiv query using GET

        Parameters
        ----------
        feed_content: dict,
            the content to feed to GET

        Returns
        -------
        res: dict,
            decoded and parsed query result

        """
        r = requests.get(**feed_content)
        parsed = feedparser.parse(r.content.decode("utf-8")).entries[0]
        if self.verbose > 1:
            print(parsed)
        title = re.sub("[\\s]+", " ", parsed["title"])  # sometimes this field has "\n"
        if title == "Error":
            res = self.default_err
            return res
        arxiv_id = parsed["id"].split("arxiv.org/abs/")[-1]
        year = parsed["published_parsed"].tm_year
        res = {"title": title}
        # authors = []
        # for item in parsed["authors"]:
        #     a = item["name"].split(" ")
        #     if len(a) > 1:
        #         a[-2] = a[-2] + ","
        #     authors.append(" ".join(a))
        # it seems that surnames are put in the last position of full names by arXiv
        authors = [item["name"] for item in parsed["authors"]]
        res["author"] = " and ".join(authors)
        res["year"] = year
        res["month"] = parsed["published_parsed"].tm_mon
        res["journal"] = f"arXiv preprint arXiv:{arxiv_id}"
        res[
            "label"
        ] = f"{parsed['authors'][0]['name'].split(' ')[-1].lower()}{year}_{arxiv_id}"
        res["entry_type"] = "article"
        return res

    def _to_bib_item(
        self,
        identifier: str,
        res: Union[str, Dict[str, str]],
        align: Optional[str] = None,
    ) -> BibItem:
        """

        Parameters
        ----------
        identifier: str,
            identifier of a publication,
            can be DOI, PMID (or url), PMCID (or url), arXiv id, etc.
        res: str or dict,
            result obtained via GET or POST
        align: str, optional,
            alignment of the final output, case insensitive,
            if specified, `self.align` is ignored

        Returns
        -------
        bib_item: BibItem,
            a BibItem instance converted from `res`

        """
        _align = (align or self.align).lower()
        assert _align in [
            "middle",
            "left",
            "left-middle",
            "left_middle",
        ], f"align must be one of 'middle', 'left', 'left-middle', 'left_middle', but got {_align}"
        if isinstance(res, str):
            lines = [line.strip() for line in res.split("\n") if len(line.strip()) > 0]
            header_dict = list(re.finditer(self.bib_header_pattern, lines[0]))[
                0
            ].groupdict()
            field_dict = OrderedDict()
            for line in lines[1:-1]:
                key, val = line.strip().split("=")
                field_dict[key.strip()] = val.strip(", ")
        elif isinstance(res, dict):
            header_dict = {
                k.strip(): str(v).strip(", ")
                for k, v in res.items()
                if k in ["entry_type", "label"]
            }
            field_dict = OrderedDict(
                {
                    k.strip(): str(v).strip(", ")
                    for k, v in res.items()
                    if k not in ["entry_type", "label"]
                }
            )

        # all field names to lower case,
        # and ignore the fields in the list `self.ignore_fields`
        field_dict = {
            k.lower(): v
            for k, v in field_dict.items()
            if k.lower() not in self.ignore_fields
        }

        # re-order the fields according to the list `self.ordering`
        _ordering = self.ordering + [k for k in field_dict if k not in self.ordering]
        _ordering = [k for k in _ordering if k in field_dict]
        field_dict = OrderedDict((k, field_dict[k]) for k in _ordering)

        # to BibItem
        bib_item = BibItem(
            identifier=identifier,
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
    def ignore_fields(self) -> List[str]:
        return self._ignore_fields

    @property
    def ordering(self) -> List[str]:
        return self._ordering

    def debug(self) -> NoReturn:
        self.verbose = 2

    def save(
        self,
        identifiers: Union[int, str, Sequence[str], Sequence[int]] = None,
        output_file: Optional[Union[str, Path]] = None,
    ) -> NoReturn:
        """

        save bib items corresponding to the identifiers to the output file.

        Parameters
        ----------
        identifiers: int or str or sequence of int or sequence of str, optional,
            the bib corresponding to the identifiers are to be saved,
            defaults to all
        output_file: str or Path, optional,
            the output file, defaults to `self.output_file`
            if specified, `self.output_file` is ignored

        WARNING
        -------
        saved bib items will be removed from the cache

        """
        _output_file = output_file or self.output_file
        assert _output_file is not None, "output_file is not specified"
        _output_file = Path(_output_file).resolve()
        assert (
            _output_file.suffix == ".bib"
        ), f"output_file must be a .bib file, but got {_output_file}"
        _output_file.parent.mkdir(parents=True, exist_ok=True)

        if identifiers is None:
            identifiers = list(self.__cached_lookup_results)
        elif isinstance(identifiers, int):
            identifiers = [self[identifiers]]
        elif isinstance(identifiers, str):
            identifiers = [identifiers]
        elif isinstance(identifiers, Sequence) and all(
            [isinstance(i, int) for i in identifiers]
        ):
            identifiers = [self[i] for i in identifiers]
        assert isinstance(identifiers, Sequence) and all(
            [isinstance(i, str) for i in identifiers]
        ), "identifiers must be a string (or an integer) or a sequence of strings (or integers)"
        identifiers = [i for i in identifiers if i in self.__cached_lookup_results]

        with open(_output_file, "a") as f:
            f.writelines(
                "\n".join([str(self.__cached_lookup_results[i]) for i in identifiers])
                + "\n"
            )

        print(f"Bib items written to {str(_output_file)}")

        # remove saved bib items from the cache
        for i in identifiers:
            self.__cached_lookup_results.pop(i)

    def pop(
        self, identifiers: Union[int, str, Sequence[str], Sequence[int]]
    ) -> NoReturn:
        """

        remove the bib corresponding to the identifiers from the cache

        Parameters
        ----------
        identifiers: int or str or sequence of int or sequence of str,
            the identifiers to be removed from the cache

        """
        if isinstance(identifiers, int):
            identifiers = [self[identifiers]]
        elif isinstance(identifiers, str):
            identifiers = [identifiers]
        elif isinstance(identifiers, Sequence) and all(
            [isinstance(i, int) for i in identifiers]
        ):
            identifiers = [self[i] for i in identifiers]
        assert isinstance(identifiers, Sequence) and all(
            [isinstance(i, str) for i in identifiers]
        ), "identifiers must be a string (or an integer) or a sequence of strings (or integers)"
        for i in identifiers:
            self.__cached_lookup_results.pop(i, None)

    def print(self) -> NoReturn:
        """

        print the bib items in the cache

        """
        print(self.get_cache(string_format=True))

    def get_cache(self, string_format: bool = False) -> Union[str, OrderedDict]:
        """

        get all bib items in the cache

        Parameters
        ----------
        string_format: bool, default False,
            whether to return the bib items in string format,
            or the ordered dict of cached instances of BibItem

        Returns
        -------
        str or OrderedDict:
            the bib items in string format,
            or the ordered dict of cached instances of BibItem

        """
        if string_format:
            return "\n".join([str(self[item]) for item in self])
        else:
            return self.__cached_lookup_results

    def __getitem__(self, index: Union[int, str]) -> str:
        if isinstance(index, int):
            return list(self.__cached_lookup_results)[index]
        elif isinstance(index, str):
            assert index in self.__cached_lookup_results, f"{index} not found"
            return self.__cached_lookup_results[index]
        else:
            raise ValueError(
                f"index should be an integer or a string, not {type(index)}"
            )

    def __len__(self) -> int:
        return len(self.__cached_lookup_results)

    def __repr__(self) -> str:
        attrs = ["align", "output_file", "_ignore_fields"]
        max_len = max([len(a.strip("_")) for a in attrs])
        if self.align == "middle":
            args = [
                f"""  {" " * (max_len-len(k.strip("_")))}{k.strip("_")} = {self.__getattribute__(k)}"""
                for k in attrs
            ]
        elif self.align == "left":
            args = [f"""  {k.strip("_")} = {self.__getattribute__(k)}""" for k in attrs]
        else:
            args = [
                f"""  {k.strip("_")}{" " * (max_len-len(k.strip("_")))} = {self.__getattribute__(k)}"""
                for k in attrs
            ]
        newline = "\n"
        return f"""{self.__name__}({newline}{f",{newline}".join(args)}{newline})"""

    __str__ = __repr__

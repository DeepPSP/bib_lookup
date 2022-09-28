"""
the database of bibtex entry types and field names, collected from
http://tug.ctan.org/info/biblatex-cheatsheet/biblatex-cheatsheet.pdf
and from https://www.openoffice.org/bibliographic/bibtex-defs.html

"""

import calendar
import re
from time import strptime
from collections import OrderedDict
from typing import Optional, Union, Sequence

import pandas as pd


class BibItem(object):
    """
    A class representing a bibtex item (entry)
    """

    __name__ = "BibItem"

    def __init__(
        self,
        identifier: str,
        entry_type: str,
        fields: OrderedDict,
        label: Optional[str] = None,
        align: str = "middle",
        check_fields: bool = False,
    ) -> None:
        """
        Parameters
        ----------
        identifier : str,
            the unique identifier of the bibtex entry,
            can be DOI, URL, arXiv ID, or any other unique identifier
        entry_type : str,
            the type of the bibtex entry,
            can be one of the items in `BIB_ENTRY_TYPES`
        fields : OrderedDict,
            the fields of the bibtex entry,
            can be one of the items in `BIB_FIELDS`
        label : str, optional,
            the label of the bibtex entry,
            can be any string
        align: str, default "middle",
            the alignment of the fields for string representation,
            can be one of "middle", "left", "left-middle", "left_middle",
            case insensitive
        check_fields: bool, default False,
            whether to check if the bib item contains all required fields,

        """
        self.__identifier = identifier
        self.__entry_type = entry_type.lower()
        assert (
            self.entry_type in BIB_ENTRY_TYPES
        ), f"{self.entry_type} is not a valid entry type"
        self.__fields = fields
        assert isinstance(
            self.__fields, OrderedDict
        ), f"fields must be OrderedDict, but got {type(self.__fields)}"
        self.__double_braces_flags = dict()
        self.__normalize_fields(check_fields)
        self.__label = label  # TODO: consider how to add label when it's None
        if self.label is None:
            self.__label = self.identifier
        self.align = align
        assert self.align in [
            "middle",
            "left",
            "left-middle",
            "left_middle",
        ], f"align must be one of 'middle', 'left', 'left-middle', 'left_middle', but got {self.align}"

    @property
    def identifier(self) -> str:
        return self.__identifier

    @property
    def entry_type(self) -> str:
        return self.__entry_type

    @property
    def fields(self) -> OrderedDict:
        return self.__fields

    @property
    def label(self) -> str:
        return self.__label

    def __normalize_fields(self, check_fields: bool = False) -> None:
        """
        convert month to number if applicable,
        remove redundant curly braces
        convert all field names to lower case

        Parameters
        ----------
        check_fields: bool, default False,
            whether to check if the bib item contains all required fields,

        """
        field_dict = OrderedDict()
        for k, v in self.fields.items():
            # field names to lower case
            k = k.strip().lower()
            # assert k in BIB_FIELDS, f"{k} is not a valid field name"
            # remove redundant curly braces and commas
            v = str(v).strip(" ,")  # DO NOT strip "{}"
            self.__double_braces_flags[k] = False
            braces_count = 0
            while all([v.startswith("{"), v.endswith("}")]) or all(
                [v.startswith('"'), v.endswith('"')]
            ):
                v = v[1:-1]
                braces_count += 1
            if braces_count >= 2:
                self.__double_braces_flags[k] = True
            # convert month to number if applicable
            if k.lower().strip() == "month" and v.capitalize() in calendar.month_abbr:
                v = strptime(v, "%b").tm_mon
            field_dict[k] = v
        self.__fields = field_dict
        if check_fields:
            self.check_required_fields()
        for k, v in self.fields.items():
            self.__setattr__(k, v)

    def check_required_fields(self) -> None:
        required_fields = DF_BIB_ENTRY_TYPES[
            DF_BIB_ENTRY_TYPES["entry_type"] == self.entry_type
        ].iloc[0]["required_fields"]
        for item in required_fields:
            # "xx|yy" means "xx or yy"
            # "xx+|yy" means "xx and/or yy"
            check_num = sum([rf in self.__fields for rf in re.findall("\\w+", item)])
            if re.search("\\+", item):
                assert check_num in [
                    1,
                    2,
                ], f"required field(s) \042{item}\042 is (are) missing"
            else:
                assert check_num == 1, f"required field \042{item}\042 is missing"

    def __str__(self) -> str:
        header = f"@{self.entry_type}{{{self.label},"
        field_dict = OrderedDict()
        for idx, (k, v) in enumerate(self.fields.items()):
            field_dict[k] = f"{{{v}}}"
            if self.__double_braces_flags[k]:
                field_dict[k] = f"{{{field_dict[k]}}}"
            if idx < len(self.fields) - 1:
                field_dict[k] += ","
        # align the fields
        max_key_len = max([len(k) for k in field_dict.keys()])
        if self.align == "middle":
            lines = (
                [header]
                + [
                    f"{' '*(2+max_key_len-len(k))}{k} = {v}"
                    for k, v in field_dict.items()
                ]
                + ["}"]
            )
        elif self.align == "left":
            lines = (
                [header] + [f"{' '*2}{k} = {v}" for k, v in field_dict.items()] + ["}"]
            )
        elif self.align in [
            "left-middle",
            "left_middle",
        ]:
            lines = (
                [header]
                + [
                    f"{' '*2}{k}{' '*(1+max_key_len-len(k))}= {v}"
                    for k, v in field_dict.items()
                ]
                + ["}"]
            )
        return "\n".join(lines)

    __repr__ = __str__

    def help(self, entries_or_fields: Union[str, Sequence[str]]) -> None:
        """ """
        if isinstance(entries_or_fields, str):
            entries_or_fields = [entries_or_fields]
        assert isinstance(
            entries_or_fields, Sequence
        ), f"entries_or_fields must be a sequence, but got {type(entries_or_fields)}"
        newline = "\n"
        for e in entries_or_fields:
            assert (
                e in BIB_ENTRY_TYPES or e in BIB_FIELDS
            ), f"{e} is not a valid entry type or field name"
            print(
                f"{e}:{newline}    {BIB_ENTRY_TYPES[e] if e in BIB_ENTRY_TYPES else BIB_FIELDS[e]}{newline}"
            )

    def __eq__(self, other: "BibItem", strict: bool = False) -> bool:
        """
        Parameters
        ----------
        other : BibItem
            the other BibItem to compare with
        strict : bool, default False
            whether to compare the fields strictly,
            if False, only entry_type and label will be compared;
            if True, entry_type, title, first author will be compared

        Examples
        --------
        >>> from copy import deepcopy
        >>> from bib_lookup import BibLookup
        >>> bl = BibLookup()
        >>> bl(""10.1109/CVPR.2016.90");
        >>> bl[bl[0]]
        @inproceedings{He_2016,
             author = {Kaiming He and Xiangyu Zhang and Shaoqing Ren and Jian Sun},
              title = {Deep Residual Learning for Image Recognition},
          booktitle = {2016 {IEEE} Conference on Computer Vision and Pattern Recognition ({CVPR})},
                doi = {10.1109/cvpr.2016.90},
               year = {2016},
              month = {6},
          publisher = {{IEEE}}
        }
        >>> bib_item = deepcopy(bl[bl[0]])
        >>> bib_item._BibItem__label = "haha"
        >>> bib_item
        @inproceedings{haha,
             author = {Kaiming He and Xiangyu Zhang and Shaoqing Ren and Jian Sun},
              title = {Deep Residual Learning for Image Recognition},
          booktitle = {2016 {IEEE} Conference on Computer Vision and Pattern Recognition ({CVPR})},
                doi = {10.1109/cvpr.2016.90},
               year = {2016},
              month = {6},
          publisher = {{IEEE}}
        }
        >>> bib_item == bl[bl[0]]
        False
        >>> bib_item.__eq__(bl[bl[0]], strict=True)
        True

        """
        if type(other) != type(self):
            return False
        if self.entry_type != other.entry_type:
            return False
        if not strict:
            if self.label != other.label:
                return False
            else:
                return True
        check_again = 2  # "title" and "author"
        if sum([hasattr(self, "title"), hasattr(other, "title")]) == 1:
            return False
        if hasattr(self, "title") and hasattr(other, "title"):
            title = re.sub(
                "\\s+", " ", re.sub("[^\\w\\s]", " ", self.title).lower().strip()
            )
            other_title = re.sub(
                "\\s+", " ", re.sub("[^\\w\\s]", " ", other.title).lower().strip()
            )
            if title != other_title:
                return False
        else:
            check_again -= 1
        if sum([hasattr(self, "author"), hasattr(other, "author")]) == 1:
            return False
        if hasattr(self, "author") and hasattr(other, "author"):
            first_author = list(
                filter(
                    lambda s: len(re.sub("[^\\w]", "", s)) > 1,
                    self.author.split("and")[0].strip().split(),
                )
            )[-1]
            other_first_author = list(
                filter(
                    lambda s: len(re.sub("[^\\w]", "", s)) > 1,
                    other.author.split("and")[0].strip().split(),
                )
            )[-1]
            if first_author != other_first_author:
                return False
        else:
            check_again -= 1
        if check_again == 0:
            if self.label != other.label:
                return False
        return True


BIB_ENTRY_TYPES = {
    # Material from journals, magazines & newspapers:
    "article": "journal, magazine or newspaper article",
    "periodical": "whole issue of a periodical",
    "suppperiodical": "supplemental material in periodical",
    # Material from single-authored or co-authored books:
    "inbook": "book part with own title",
    "suppbook": "supplemental material in book",
    "bookinbook": "originally published as standalone book",
    "book": "single-volume book by author(s) of whole",
    "mvbook": "multi-volume book",
    # Material from edited anthologies:
    "incollection": "contribution to anthology",
    "suppcollection": "supplemental material in anthology",
    "collection": "single-volume edited anthology",
    "mvcollection": "multi-volume collection",
    # Material from conference proceedings:
    "inproceedings": "article in conference proceedings",
    "proceedings": "single-volume conference proceedings",
    "mvproceedings": "multi-volume conference proceedings",
    # Material from works of reference:
    "inreference": "article in a reference work",
    "reference": "single-volume work of reference",
    "mvreference": "multi-volume reference work",
    # Material from technical & institutional publications:
    "manual": "technical or other documentation",
    "report": "institutional report or white paper",
    "patent": "patent or patent request",
    "thesis": "work completed to fulfil degree requirement",
    "phdthesis": "ph.D. thesis",
    "mastersthesis": "M.A. thesis",
    # Material from online, informal & other sources:
    "online": "inherently online source",
    "booklet": "informally published book",
    "unpublished": "work not formally published",
    "misc": "last resort (check manual first!)",
    "software": "software",
    # Special entries for database management:
    "set": "(static) entry ‘set’",
    "xdata": "data-container (cannot be cited)",
}

DF_BIB_ENTRY_TYPES = pd.DataFrame(
    [(k, v) for k, v in BIB_ENTRY_TYPES.items()], columns=["entry_type", "description"]
)
# fmt: off
_required_fields = {
    # https://www.openoffice.org/bibliographic/bibtex-defs.html
    # https://www.andy-roberts.net/res/writing/latex/bibentries.pdf
    "article": ["author", "title", "journal", "year"],
    "book": ["author|editor", "title", "publisher", "year"],
    "booklet": ["title"],
    "inbook": ["author|editor", "title", "chapter+|pages", "publisher", "year"],
    "incollection": ["author", "title", "booktitle", "publisher", "year"],
    "inproceedings": ["author", "title", "booktitle", "year"],
    "conference": ["author", "title", "booktitle", "year"],
    "manual": ["title"],
    "mastersthesis": ["author", "title", "school", "year"],
    "misc": [],
    "phdthesis": ["author", "title", "school", "year"],
    "proceedings": ["title", "year"],
    "techreport": ["author", "title", "institution", "year"],
    "unpublished": ["author", "title", "note"],
}
_optional_fields = {
    # https://www.openoffice.org/bibliographic/bibtex-defs.html
    # https://www.andy-roberts.net/res/writing/latex/bibentries.pdf
    "article": ["volume", "number", "pages", "month", "note"],
    "book": ["volume|number", "series", "address", "edition", "month", "note"],
    "booklet": ["author", "howpublished", "address", "month", "year", "note"],
    "inbook": ["volume|number", "series", "type", "address", "edition", "month", "note"],
    "incollection": ["editor", "volume|number", "series", "type", "chapter", "pages", "address", "edition", "month", "note"],
    "inproceedings": ["editor", "volume|number", "series", "pages", "address", "month", "organization", "publisher", "note"],
    "conference": ["editor", "volume|number", "series", "pages", "address", "month", "organization", "publisher", "note"],
    "manual": ["author", "organization", "address", "edition", "month", "year", "note"],
    "mastersthesis": ["type", "address", "month", "note"],
    "misc": ["author", "title", "howpublished", "month", "year", "note"],
    "phdthesis": ["type", "address", "month", "note"],
    "proceedings": ["editor", "volume|number", "series", "address", "month", "publisher", "organization", "note"],
    "techreport": ["type", "number", "address", "month", "note"],
    "unpublished": ["month", "year"],
}
# fmt: on
DF_BIB_ENTRY_TYPES["required_fields"] = DF_BIB_ENTRY_TYPES.entry_type.apply(
    lambda x: _required_fields.get(x, [])
)
DF_BIB_ENTRY_TYPES["optional_fields"] = DF_BIB_ENTRY_TYPES.entry_type.apply(
    lambda x: _optional_fields.get(x, [])
)


BIB_FIELDS = {
    # individuals
    "author": "author(s) of title, authortype specifies kind",
    "bookauthor": "author(s) of booktitle",
    "editor": "editor(s), editortype specifies role",
    "editora/b/c": "secondary editor(s), editora/b/ctype for roles",
    "editora": "secondary editor(s), editora/b/ctype for roles",
    "editorb": "secondary editor(s), editora/b/ctype for roles",
    "editorc": "secondary editor(s), editora/b/ctype for roles",
    "afterword": "author(s) of afterword",
    "annotator": "author(s) of annotations",
    "commentator": "author(s) of commentary",
    "forward": "author(s) of forward",
    "introduction": "author(s) of introduction",
    "translator": "translator(s) of (book)title",
    "holder": "of patent",
    # organizations
    "institution": "university or similar",
    "organization": "manual/website publisher or event sponsor",
    "publisher": "publisher(s)",
    "school": "the name of the school where a thesis was written",
    "journal": "journal name",
    # titles
    "title": "title",
    "indextitle": "if different from title",
    "booktitle": "title of book",
    "maintitle": "title of multi-volume book",
    "journaltitle": "or journals",
    "issuetitle": "title of journal special issue",
    "eventtitle": "title of conference or event",
    "reprinttitle": "title of a reprint of the work",
    "series": "publication series",
    # volumes & versions
    "volume": "volume of journal or multi-volume book",
    "number": "numbered issue of journal or book in series",
    "part": "number of physical part of logical volume",
    "issue": "non-number issue of journal",
    "volumes": "number of volumes for multi-volume work",
    "chapter": "a chapter (or section or whatever) number",
    "edition": "as 〈integer〉 rather than ordinal",
    "version": "revision number for software or manual",
    "pubstate": "publication state",
    # pages
    "numpages": "number of pages",
    "pages": "page list or range",
    "pagetotal": "total number of pages",
    "(book)pagination": "pagination format of (book)title",
    # dates
    "date": "publication date as 〈yyyy-mm-dd〉",
    "eventdate": "conference or event date as 〈yyyy-mm-dd〉",
    "urldate": "access date for url as 〈yyyy-mm-dd〉",
    "year": "year of publication",
    "month": "month of publication",
    # places
    "location": "or address, where published",
    "address": "place of publication",
    "venue": "of event",
    # digital
    "url": "URL",
    "doi": "Digital Object Identifier",
    "eid": "electronic identifier of @article",
    "eprint": "archive-specific electronic identifier",
    "eprinttype": "type of identifier, eprintclass for further details",
    # types
    "type": "of @manual, @patent, @report or @thesis",
    "entrysubtype": "for finer-grained specification of type",
    # misc.
    "addendum": "miscellaneous data printed at end of entry",
    "note": "miscellaneous data printed within entry",
    "howpublished": "non-standard publication details",
    "articleno": "article number",
    "copyright": "Copyright notice",
    # international standards
    "isan": "International Standard Audiovisual Number",
    "isbn": "International Standard Book Number",
    "ismn": "International Standard Music Number",
    "isrn": "International Standard Technical Report Number",
    "issn": "International Standard Serial Number",
    "iswc": "International Standard Work Code",
    # labels
    "label": "fall-back label",
    "shorthand": "special designator, overrides label in citations",
    "shorthandintro": "override default introduction of shorthand",
    # unclassified
    "language": "language of work",
    "abstract": "record of work’s abstract",
    "annotation": "for annotated bibliographies",
    "file": "local link",
    "library": "library name, call number or similar",
    # Special fields for non-printable data:
    "execute": "arbitrary TEX code",
    "keywords": "separated list of keywords",
    "options": "per-entry options",
    "ids": "citation key aliases",
    "related": "another entry key, relatedoptions for options",
    "relatedtype": "relationship identifier for related",
    "relatedstring": "override value of relatedtype",
    "entryset": "list of entry keys in @set",
    "crossref": "another entry key",
    "xref": "another entry key",
    "xdata": "entry key for @xdata container",
    "langid": "babel/polyglossia language identifier",
    "langidopts": "polyglossia options for langid",
    "gender": "gender of author or editor",
    "presort": "modify sorting",
    "sortkey": "sort key, overrides everything except presort",
    "sortname": "replaces author or editor when sorting",
    "sortshorthand": "sortkey if entry has shorthand",
    "sorttitle": "replaces title when sorting",
    "indexsorttitle": "replaces title when sorting index",
    "sortyear": "replaces year (from date) when sorting",
    # arXiv
    "arxivid": "arXiv identifier",
    "archiveprefix": "arXiv Prefix",
    "primaryclass": "primary class, e.g. cs.CV",
}

DF_BIB_FIELDS = pd.DataFrame(
    [(k, v) for k, v in BIB_FIELDS.items()], columns=["field", "description"]
)

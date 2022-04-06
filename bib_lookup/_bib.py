"""
the database of bibtex entry types and field names, collected from
http://tug.ctan.org/info/biblatex-cheatsheet/biblatex-cheatsheet.pdf

"""

import calendar
from time import strptime
from collections import OrderedDict
from typing import NoReturn, Optional, Union, Sequence

import pandas as pd


class BibItem(object):
    """ """

    __name__ = "BibItem"

    def __init__(
        self,
        identifier: str,
        entry_type: str,
        fields: OrderedDict,
        label: Optional[str] = None,
        align: str = "middle",
    ) -> NoReturn:
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
        self.__normalize_fields()
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

    def __normalize_fields(self) -> NoReturn:
        """
        convert month to number if applicable,
        remove redundant curly braces
        convert all field names to lower case
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
        for k, v in self.fields.items():
            self.__setattr__(k, v)

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

    def help(self, entries_or_fields: Union[str, Sequence[str]]) -> NoReturn:
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
    # Material from online, informal & other sources:
    "online": "inherently online source",
    "booklet": "informally published book",
    "unpublished": "work not formally published",
    "misc": "last resort (check manual first!)",
    # Special entries for database management:
    "set": "(static) entry ‘set’",
    "xdata": "data-container (cannot be cited)",
}

DF_BIB_ENTRY_TYPES = pd.DataFrame(
    [(k, v) for k, v in BIB_ENTRY_TYPES.items()], columns=["entry_type", "description"]
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
    "edition": "as 〈integer〉 rather than ordinal",
    "version": "revision number for software or manual",
    "pubstate": "publication state",
    # pages
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
}

DF_BIB_FIELDS = pd.DataFrame(
    [(k, v) for k, v in BIB_FIELDS.items()], columns=["field", "description"]
)

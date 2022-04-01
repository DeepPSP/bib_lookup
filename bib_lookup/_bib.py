"""
the database of bibtex entry types and field names, collected from
http://tug.ctan.org/info/biblatex-cheatsheet/biblatex-cheatsheet.pdf

"""

from collections import OrderedDict

import pandas as pd


class BibItem(OrderedDict):
    """
    NOT finished yet
    """

    __name__ = "BibItem"


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
    "authors": "author(s) of title, authortype specifies kind",
    "bookauthor": "author(s) of booktitle",
    "editors": "editor(s), editortype specifies role",
    "editora/b/c": "secondary editor(s), editora/b/ctype for roles",
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

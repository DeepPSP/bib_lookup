"""
Custom Pybtex style for Chicago (Notes and Bibliography).
Simplified implementation focusing on Article, Book, and InProceedings.
"""

from typing import Any, Callable, Union

from pybtex.database import Entry, Person
from pybtex.style.formatting.unsrt import Style as UnsrtStyle
from pybtex.style.template import (
    Node,
    field,
    join,
    node,
    optional,
    optional_field,
    sentence,
    tag,
    words,
)


class ChicagoNames(Node):
    def __init__(self, role: str, formatter: Callable[[Person, bool], str], limit: int = 10):
        self.role = role
        self.formatter = formatter
        self.limit = limit

    def format_data(self, data: Union[dict, Entry]) -> str:
        if isinstance(data, dict) and "entry" in data:
            data = data["entry"]

        if not hasattr(data, "persons") or self.role not in data.persons:
            return ""

        persons = data.persons[self.role]
        if not persons:
            return ""

        num_persons = len(persons)

        # Chicago 17th: For 1-10 authors, list all.
        # If more than 10, list first 7 then et al.

        if num_persons <= self.limit:
            formatted_persons = []
            for i, person in enumerate(persons):
                formatted_persons.append(self.formatter(person, first_author=(i == 0)))

            if len(formatted_persons) == 1:
                return formatted_persons[0]
            elif len(formatted_persons) == 2:
                return f"{formatted_persons[0]}, and {formatted_persons[1]}"
            else:
                return ", ".join(formatted_persons[:-1]) + f", and {formatted_persons[-1]}"
        else:
            # Truncated case
            persons_to_format = persons[:7]
            formatted_persons = []
            for i, person in enumerate(persons_to_format):
                formatted_persons.append(self.formatter(person, first_author=(i == 0)))

            return ", ".join(formatted_persons) + ", et al"


@node
def chicago_pages(children: Node, data: Union[dict, Entry]) -> str:
    if isinstance(data, dict) and "entry" in data:
        data = data["entry"]
    if not hasattr(data, "fields"):
        return ""
    pages = data.fields.get("pages", "")
    if not pages:
        return ""
    return pages.replace("--", "–")


@node
def chicago_date(children: Node, data: Union[dict, Entry]) -> str:
    if isinstance(data, dict) and "entry" in data:
        data = data["entry"]
    if not hasattr(data, "fields"):
        return ""
    month = data.fields.get("month", "")
    year = data.fields.get("year", "")
    if month and year:
        # Full month name for Chicago
        MONTH_MAP: dict[str, str] = {
            "1": "January",
            "01": "January",
            "2": "February",
            "02": "February",
            "3": "March",
            "03": "March",
            "4": "April",
            "04": "April",
            "5": "May",
            "05": "May",
            "6": "June",
            "06": "June",
            "7": "July",
            "07": "July",
            "8": "August",
            "08": "August",
            "9": "September",
            "09": "September",
            "10": "October",
            "11": "November",
            "12": "December",
            "january": "January",
            "february": "February",
            "march": "March",
            "april": "April",
            "may": "May",
            "june": "June",
            "july": "July",
            "august": "August",
            "september": "September",
            "october": "October",
            "november": "November",
            "december": "December",
        }
        month_full = MONTH_MAP.get(str(month).lower(), str(month).capitalize())
        return f"({month_full} {year})"
    elif year:
        return f"({year})"
    return ""


class ChicagoStyle(UnsrtStyle):
    def __init__(self, max_names: int = 10, **kwargs: Any):
        super().__init__(**kwargs)
        self.max_names = max_names

    def format_names(self, role: str, as_sentence: bool = True) -> Union[Node, sentence]:
        formatted_names = ChicagoNames(role, self._format_person, limit=self.max_names)
        if as_sentence:
            return sentence[formatted_names]
        else:
            return formatted_names

    def _format_person(self, person: Person, first_author: bool = True) -> str:
        """Format a single person."""
        first = " ".join(person.first_names + person.middle_names)
        last = " ".join(person.prelast_names + person.last_names)
        if person.lineage_names:
            last += ", " + " ".join(person.lineage_names)
        if first_author:
            return f"{last}, {first}"
        else:
            return f"{first} {last}"

    def format_label(self, entry: Entry) -> str:
        return ""

    def get_article_template(self, e: Entry) -> Node:
        # Author. "Title." Journal Volume (Month Year): Pages. https://doi.org/...
        template = join(sep=". ")[
            self.format_names("author", as_sentence=False),
            join(sep="")["“", field("title"), ".”"],
        ]

        journal_info = join(sep=" ")[
            tag("em")[field("journal")],
            join(sep="")[
                optional_field("volume"),
                optional[join(sep="")[", no. ", field("number")]],
                " ",
                chicago_date,
                optional[join(sep="", last_sep="")[": ", chicago_pages]],
            ],
        ]
        template = join(sep=" ")[template, journal_info]
        # Add ISSN if present
        if "issn" in e.fields:
            template = join(sep=". ")[template, join["ISSN: ", field("issn")]]
        if "doi" in e.fields:
            doi = e.fields["doi"]
            if not doi.startswith("http"):
                doi = f"https://doi.org/{doi}"
            template = join(sep=". ")[template, doi]
        if "url" in e.fields:
            # Add URL even if DOI is present (per expected output)
            template = join(sep=". ")[template, field("url")]
        return sentence[template]

    def get_book_template(self, e: Entry) -> Node:
        template = join(sep=". ")[
            self.format_names("author", as_sentence=False),
            tag("em")[field("title")],
            join(sep=": ")[optional_field("address"), field("publisher")],
            field("year"),
        ]
        if "doi" in e.fields:
            doi = e.fields["doi"]
            if not doi.startswith("http"):
                doi = f"https://doi.org/{doi}"
            template = join(sep=". ")[template, doi]
        return sentence[template]

    def get_inproceedings_template(self, e: Entry) -> Node:
        template = join(sep=". ")[
            self.format_names("author", as_sentence=False),
            join(sep="")["“", field("title"), ".”"],
            words["In", tag("em")[field("booktitle")]],
            join(sep=": ")[optional_field("address"), field("publisher")],
            field("year"),
            optional[chicago_pages],
        ]
        if "doi" in e.fields:
            doi = e.fields["doi"]
            if not doi.startswith("http"):
                doi = f"https://doi.org/{doi}"
            template = join(sep=". ")[template, doi]
        return sentence[template]

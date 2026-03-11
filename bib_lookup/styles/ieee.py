"""
Custom Pybtex style for IEEE.
Simplified implementation focusing on Article, Book, and InProceedings.
"""

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


class IEEENames(Node):
    def __init__(self, role, formatter, limit=6):
        self.role = role
        self.formatter = formatter
        self.limit = limit

    def format_data(self, data):
        if isinstance(data, dict) and "entry" in data:
            data = data["entry"]

        if not hasattr(data, "persons") or self.role not in data.persons:
            return ""

        persons = data.persons[self.role]
        if not persons:
            return ""

        use_et_al = False
        if len(persons) > self.limit:
            persons_to_format = persons[:1]
            use_et_al = True
        else:
            persons_to_format = persons

        formatted_persons = [self.formatter(person) for person in persons_to_format]

        if len(formatted_persons) == 1:
            result = formatted_persons[0]
        elif len(formatted_persons) == 2:
            result = f"{formatted_persons[0]} and {formatted_persons[1]}"
        else:
            result = ", ".join(formatted_persons[:-1]) + f", and {formatted_persons[-1]}"

        if use_et_al:
            result += " et al."

        return result


@node
def ieee_pages(children, data):
    """Format pages as p. or pp."""
    if isinstance(data, dict) and "entry" in data:
        data = data["entry"]
    pages = data.fields.get("pages", "")
    if not pages:
        return ""
    # If pages contains range (- or --)
    if "-" in pages or "," in pages:
        return f"pp. {pages.replace('--', '–')}"
    else:
        return f"p. {pages}"


@node
def ieee_month(children, data):
    """Abbreviate months according to IEEE."""
    MONTH_MAP = {
        "january": "Jan.",
        "february": "Feb.",
        "march": "Mar.",
        "april": "Apr.",
        "may": "May",
        "june": "June",
        "july": "July",
        "august": "Aug.",
        "september": "Sept.",
        "october": "Oct.",
        "november": "Nov.",
        "december": "Dec.",
        "jan": "Jan.",
        "feb": "Feb.",
        "mar": "Mar.",
        "apr": "Apr.",
        "jun": "June",
        "jul": "July",
        "aug": "Aug.",
        "sep": "Sept.",
        "oct": "Oct.",
        "nov": "Nov.",
        "dec": "Dec.",
    }
    if isinstance(data, dict) and "entry" in data:
        data = data["entry"]
    month = data.fields.get("month", "")
    if not month:
        return ""
    return MONTH_MAP.get(month.lower(), month)


class IEEEStyle(UnsrtStyle):
    def __init__(self, max_names=6, **kwargs):
        super().__init__(**kwargs)
        self.max_names = max_names

    def format_names(self, role, as_sentence=True):
        formatted_names = IEEENames(role, self._format_person, limit=self.max_names)
        if as_sentence:
            return sentence[formatted_names]
        else:
            return formatted_names

    def _format_person(self, person):
        """Format a single person as 'F. M. Last'."""
        initials = []
        for names_list in [person.first_names, person.middle_names]:
            for name in names_list:
                if name:
                    initials.append(f"{name[0]}.")

        initials_str = " ".join(initials)

        last_name = " ".join(person.prelast_names + person.last_names)
        if person.lineage_names:
            last_name += ", " + " ".join(person.lineage_names)

        if initials_str:
            return f"{initials_str} {last_name}"
        return last_name

    def get_article_template(self, e):
        # [1] F. M. Last, "Title," Journal, vol. X, no. Y, pp. Z-W, Month Year.
        template = join(sep=", ")[
            self.format_names("author", as_sentence=False),
            join(sep=" ")[join(sep="")['"', field("title"), ',"'], tag("em")[field("journal")]],
            optional[words["vol.", field("volume")]],
            optional[words["no.", field("number")]],
            optional[ieee_pages],
            join(sep=" ")[ieee_month, field("year")],
        ]
        if "doi" in e.fields:
            template = join(sep=", ")[template, join["doi: ", field("doi")]]
        return sentence[template]

    def get_book_template(self, e):
        template = join(sep=", ")[
            self.format_names("author", as_sentence=False),
            tag("em")[field("title")],
            join(sep=": ")[optional_field("address"), field("publisher")],
            field("year"),
        ]
        if "doi" in e.fields:
            template = join(sep=", ")[template, join["doi: ", field("doi")]]
        return sentence[template]

    def get_inproceedings_template(self, e):
        template = join(sep=", ")[
            self.format_names("author", as_sentence=False),
            join(sep=" ")[join(sep="")['"', field("title"), ',"'], words["in", tag("em")[field("booktitle")]]],
            field("year"),
            optional[ieee_pages],
        ]
        if "doi" in e.fields:
            template = join(sep=", ")[template, join["doi: ", field("doi")]]
        return sentence[template]

    def get_phdthesis_template(self, e):
        template = join(sep=", ")[
            self.format_names("author", as_sentence=False),
            join(sep="")['"', field("title"), ',"'],
            "Ph.D. dissertation",
            field("school"),
            optional_field("address"),
            field("year"),
        ]
        return sentence[template]

    def get_mastersthesis_template(self, e):
        template = join(sep=", ")[
            self.format_names("author", as_sentence=False),
            join(sep="")['"', field("title"), ',"'],
            "M.S. thesis",
            field("school"),
            optional_field("address"),
            field("year"),
        ]
        return sentence[template]

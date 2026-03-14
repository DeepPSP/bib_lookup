"""
Custom Pybtex style for APA (7th Edition).
Simplified implementation focusing on Article, Book, and InProceedings.
"""

from pybtex.style.formatting.unsrt import Style as UnsrtStyle
from pybtex.style.template import (
    Node,
    field,
    join,
    optional,
    optional_field,
    sentence,
    tag,
)


class APANames(Node):
    def __init__(self, role, formatter, limit=20):
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

        num_persons = len(persons)

        if num_persons <= 1:
            return self.formatter(persons[0])

        display_limit = self.limit
        if num_persons <= display_limit:
            # APA 7th: For 2-20 authors, use ampersand before the last author.
            formatted_persons = [self.formatter(p) for p in persons]
            return ", ".join(formatted_persons[:-1]) + ", & " + formatted_persons[-1]
        else:
            # APA 7th: For 21+ authors, list first 19, ellipsis, then last author.
            idx = max(1, display_limit - 1)
            first_part = [self.formatter(p) for p in persons[:idx]]
            last_one = self.formatter(persons[-1])
            return ", ".join(first_part) + ", ... " + last_one


class APAStyle(UnsrtStyle):
    def __init__(self, max_names=20, **kwargs):
        super().__init__(**kwargs)
        self.max_names = max_names

    def format_names(self, role, as_sentence=True):
        formatted_names = APANames(role, self._format_person, limit=self.max_names)
        if as_sentence:
            return sentence[formatted_names]
        else:
            return formatted_names

    def _format_person(self, person):
        """Format a single person as 'Last, F. M.'."""
        last_name = " ".join(person.prelast_names + person.last_names)
        if person.lineage_names:
            last_name += ", " + " ".join(person.lineage_names)

        initials = []
        for names_list in [person.first_names, person.middle_names]:
            for name in names_list:
                if name:
                    initial = name[0].strip(".")
                    initials.append(f"{initial}.")

        initials_str = " ".join(initials)

        if initials_str:
            return f"{last_name}, {initials_str}"
        return last_name

    def format_label(self, entry):
        return ""

    def get_article_template(self, e):
        # Last, F. M. (Year). Title. Journal, Volume(Issue), Pages.
        template = join[
            self.format_names("author", as_sentence=False),
            " ",
            join(sep="", last_sep="")[
                "(",
                optional_field("year"),
                ").",
            ],
            " ",
            optional_field("title"),
            ". ",
            tag("em")[optional_field("journal")],
            optional[
                join(sep="")[
                    ", ",
                    tag("em")[optional_field("volume")],
                ]
            ],
            optional[
                join(sep="", last_sep="")[
                    "(",
                    field("number"),
                    ")",
                ]
            ],
            optional[join(sep="", last_sep="")[", ", optional_field("pages")]],
            ".",
        ]
        if "doi" in e.fields:
            template = join(sep=" ")[template, join["https://doi.org/", field("doi")]]
        elif "url" in e.fields:
            template = join(sep=" ")[template, field("url")]
        return template

    def get_book_template(self, e):
        template = join[
            self.format_names("author", as_sentence=False),
            " ",
            join(sep="", last_sep="")[
                "(",
                optional_field("year"),
                ").",
            ],
            " ",
            tag("em")[optional_field("title")],
            ". ",
            optional_field("publisher"),
            ".",
        ]
        if "doi" in e.fields:
            template = join(sep=" ")[template, join["https://doi.org/", field("doi")]]
        return template

    def get_inproceedings_template(self, e):
        template = join[
            self.format_names("author", as_sentence=False),
            " ",
            join(sep="", last_sep="")[
                "(",
                optional_field("year"),
                ").",
            ],
            " ",
            optional_field("title"),
            ". In ",
            tag("em")[optional_field("booktitle")],
            optional[join(sep="", last_sep="")[" (pp. ", optional_field("pages"), ")"]],
            ".",
        ]
        if "doi" in e.fields:
            template = join(sep=" ")[template, join["https://doi.org/", field("doi")]]
        return template

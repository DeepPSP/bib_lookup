"""
Custom Pybtex style for GB/T 7714-2015.
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
)


class GBTNames(Node):
    def __init__(self, role, formatter, limit=3):
        if not isinstance(limit, int) or limit < 1:
            raise ValueError(f"`limit` must be an integer >= 1, but got `{limit}`")
        self.role = role
        self.formatter = formatter
        self.limit = limit

    def format_data(self, data):
        # Handle both Entry object and Context dict
        if isinstance(data, dict) and "entry" in data:
            data = data["entry"]

        if not hasattr(data, "persons"):
            return ""

        if self.role not in data.persons:
            return ""

        persons = data.persons[self.role]
        formatted_persons = []

        # Truncate to limit
        limit = self.limit
        use_et_al = False
        if len(persons) > limit:
            persons_to_format = persons[:limit]
            use_et_al = True
        else:
            persons_to_format = persons

        for person in persons_to_format:
            formatted_persons.append(self.formatter(person))

        # Join with comma
        result = ", ".join(formatted_persons)

        if use_et_al:
            result += ", et al"

        return result


class GBT7714Style(UnsrtStyle):
    def __init__(self, label_style=None, name_style=None, sorting_style=None, max_names=3, **kwargs):
        sorting_style = "none"
        super().__init__(label_style, name_style, sorting_style, **kwargs)
        self.max_names = max_names

    def format_names(self, role, as_sentence=True):
        formatted_names = GBTNames(role, self._format_person, limit=self.max_names)
        if as_sentence:
            return sentence[formatted_names]
        else:
            return formatted_names

    def _format_person(self, person):
        prelast = " ".join(person.prelast_names)
        last = " ".join(person.last_names)
        lineage = " ".join(person.lineage_names)
        parts = []
        if prelast:
            parts.append(prelast)
        if last:
            parts.append(last)
        if lineage:
            parts.append(lineage.replace(".", ""))
        surname = " ".join(parts).upper()  # GB/T 7714 requires uppercase surnames
        initials_list = []
        for names_list in [person.first_names, person.middle_names]:
            for name in names_list:
                if name:
                    initials_list.append(name[0].upper())  # Uppercase initials
        initials = " ".join(initials_list)
        return f"{surname} {initials}".strip()

    def get_article_template(self, e):
        # Use [J/OL] for online articles (with DOI or URL), [J] for print
        medium_tag = "[J/OL]" if ("doi" in e.fields or "url" in e.fields) else "[J]"
        template = join(sep=". ")[
            self.format_names("author", as_sentence=False),
            join[field("title"), medium_tag],
            join(sep=", ")[
                field("journal"),
                field("year"),
                join(sep=": ")[
                    join[optional_field("volume"), optional["(", field("number"), ")"]],
                    field("pages"),
                ],
            ],
        ]
        if "url" in e.fields:
            template = join(sep=". ")[template, field("url")]
        if "doi" in e.fields:
            template = join(sep=". ")[template, join["DOI: ", field("doi")]]
        return sentence[template]

    def get_book_template(self, e):
        template = join(sep=". ")[
            self.format_names("author", as_sentence=False),
            join[field("title"), "[M]"],
            join(sep=", ")[
                join(sep=": ")[optional_field("address"), field("publisher")],
                field("year"),
            ],
        ]
        if "doi" in e.fields:
            template = join(sep=". ")[template, join["DOI: ", field("doi")]]
        return sentence[template]

    def get_inproceedings_template(self, e):
        template = join(sep=". ")[
            self.format_names("author", as_sentence=False),
            join(sep=" // ")[join[field("title"), "[C]"], field("booktitle")],
            join(sep=", ")[
                join(sep=": ")[optional_field("address"), field("publisher")],
                join(sep=": ")[field("year"), field("pages")],
            ],
        ]
        if "doi" in e.fields:
            template = join(sep=". ")[template, join["DOI: ", field("doi")]]
        return sentence[template]

    def get_phdthesis_template(self, e):
        template = join(sep=". ")[
            self.format_names("author", as_sentence=False),
            join[field("title"), "[D]"],
            join(sep=", ")[
                join(sep=": ")[optional_field("address"), field("school")],
                field("year"),
            ],
        ]
        if "doi" in e.fields:
            template = join(sep=". ")[template, join["DOI: ", field("doi")]]
        return sentence[template]

    def get_mastersthesis_template(self, e):
        return self.get_phdthesis_template(e)

    def get_techreport_template(self, e):
        template = join(sep=". ")[
            self.format_names("author", as_sentence=False),
            join[field("title"), "[R]"],
            join(sep=", ")[
                join(sep=": ")[optional_field("address"), field("institution")],
                field("year"),
            ],
        ]
        if "doi" in e.fields:
            template = join(sep=". ")[template, join["DOI: ", field("doi")]]
        return sentence[template]

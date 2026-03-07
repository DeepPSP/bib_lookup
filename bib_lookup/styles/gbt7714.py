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
        # GB/T 7714 uses numeric labels [1]
        # Names are formatted as "Family Name First Name" (no comma) usually, or "Family Name, First Name"
        # Standard GB/T 7714-2015: "Author. Title[M]. Publisher, Year."
        # Names: "Last F M" (uppercase)

        # We use 'lastfirst' plugin as a base, but we might need uppercase
        sorting_style = "none"  # Default to no sorting (citation order)
        super().__init__(label_style, name_style, sorting_style, **kwargs)
        self.max_names = max_names

    def format_names(self, role, as_sentence=True):
        # GB/T 7714: Names are separated by commas, ending with dot if sentence
        # Max 3 authors, then "et al." (or "等" for Chinese)
        # We use a custom Node to handle truncation and formatting
        formatted_names = GBTNames(role, self._format_person, limit=self.max_names)

        if as_sentence:
            return sentence[formatted_names]
        else:
            return formatted_names

    def _format_person(self, person):
        """Format a single person as 'Surname FirstInitial MiddleInitial' (e.g. 'Lai Y', 'Knuth D E')."""
        # Surname with prelast (von)
        prelast = " ".join(person.prelast_names)
        last = " ".join(person.last_names)
        if prelast:
            surname = f"{prelast} {last}"
        else:
            surname = last

        # First and Middle Initials (no dot)
        initials_list = []
        for names_list in [person.first_names, person.middle_names]:
            for name in names_list:
                if name:
                    initials_list.append(name[0])

        initials = " ".join(initials_list)

        name_str = f"{surname} {initials}".strip()
        return name_str

    def get_article_template(self, e):
        # [1] AUTHOR. Title[J]. Journal, Year, Volume(Issue): Pages.
        template = join(sep=". ")[
            self.format_names("author", as_sentence=False),
            join[field("title"), "[J]"],
            join(sep=", ")[
                field("journal"),
                field("year"),
                join(sep=": ")[
                    join[optional_field("volume"), optional["(", field("number"), ")"]],
                    optional[field("pages")],
                ],
            ],
        ]
        if "doi" in e.fields:
            template = join(sep=". ")[template, join["DOI: ", field("doi")]]
        return sentence[template]

    def get_book_template(self, e):
        # [2] AUTHOR. Title[M]. Address: Publisher, Year.
        template = join(sep=". ")[
            self.format_names("author", as_sentence=False),
            join[field("title"), "[M]"],
            join(sep=", ")[
                join(sep=": ")[
                    optional_field("address"),
                    field("publisher"),
                ],
                field("year"),
            ],
        ]
        if "doi" in e.fields:
            template = join(sep=". ")[template, join["DOI: ", field("doi")]]
        return sentence[template]

    def get_inproceedings_template(self, e):
        # [3] AUTHOR. Title[C] // Booktitle. Address: Publisher, Year: Pages.
        template = join(sep=". ")[
            self.format_names("author", as_sentence=False),
            join(sep=" // ")[join[field("title"), "[C]"], field("booktitle")],
            join(sep=", ")[
                join(sep=": ")[
                    optional_field("address"),
                    field("publisher"),
                ],
                join(sep=": ")[
                    field("year"),
                    optional[field("pages")],
                ],
            ],
        ]
        if "doi" in e.fields:
            template = join(sep=". ")[template, join["DOI: ", field("doi")]]
        return sentence[template]

    def get_phdthesis_template(self, e):
        # [4] AUTHOR. Title[D]. Address: School, Year.
        template = join(sep=". ")[
            self.format_names("author", as_sentence=False),
            join[field("title"), "[D]"],
            join(sep=", ")[
                join(sep=": ")[
                    optional_field("address"),
                    field("school"),
                ],
                field("year"),
            ],
        ]
        if "doi" in e.fields:
            template = join(sep=". ")[template, join["DOI: ", field("doi")]]
        return sentence[template]

    def get_mastersthesis_template(self, e):
        return self.get_phdthesis_template(e)

    def get_techreport_template(self, e):
        # [5] AUTHOR. Title[R]. Address: Institution, Year.
        template = join(sep=". ")[
            self.format_names("author", as_sentence=False),
            join[field("title"), "[R]"],
            join(sep=", ")[
                join(sep=": ")[
                    optional_field("address"),
                    field("institution"),
                ],
                field("year"),
            ],
        ]
        if "doi" in e.fields:
            template = join(sep=". ")[template, join["DOI: ", field("doi")]]
        return sentence[template]

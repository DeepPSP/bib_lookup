"""
Custom Pybtex style for GB/T 7714-2015.
Simplified implementation focusing on Article, Book, and InProceedings.
"""

from pybtex.plugin import find_plugin
from pybtex.style.formatting.unsrt import Style as UnsrtStyle
from pybtex.style.template import (
    field,
    join,
    names,
    optional,
    optional_field,
    sentence,
)


class GBT7714Style(UnsrtStyle):
    def __init__(self, label_style=None, name_style=None, sorting_style=None, **kwargs):
        # GB/T 7714 uses numeric labels [1]
        # Names are formatted as "Family Name First Name" (no comma) usually, or "Family Name, First Name"
        # Standard GB/T 7714-2015: "Author. Title[M]. Publisher, Year."
        # Names: "Last F M" (uppercase)

        # We use 'lastfirst' plugin as a base, but we might need uppercase
        name_style = find_plugin("pybtex.style.names", "lastfirst")
        sorting_style = "none"  # Default to no sorting (citation order)
        super().__init__(label_style, name_style, sorting_style, **kwargs)

    def format_names(self, role, as_sentence=True):
        # GB/T 7714: Names are separated by commas, ending with dot if sentence
        # Max 3 authors, then "et al." (or "等" for Chinese)
        # We simplify here: list all authors separated by comma
        formatted_names = names(role, sep=", ", sep2=", ", last_sep=", ")

        # TODO: uppercase names? GB/T 7714 often requires uppercase last name
        # But pybtex name formatting is complex. Let's rely on standard formatting for now.

        if as_sentence:
            return sentence[formatted_names]
        else:
            return formatted_names

    def get_article_template(self, e):
        # [1] AUTHOR. Title[J]. Journal, Year, Volume(Issue): Pages.
        return join(sep=". ")[
            self.format_names("author", as_sentence=False),
            join[field("title"), "[J]"],
            join(sep=", ")[
                field("journal"),
                field("year"),
                join[field("volume"), optional["(", field("number"), ")"]],
                optional[field("pages")],
            ],
        ]

    def get_book_template(self, e):
        # [2] AUTHOR. Title[M]. Address: Publisher, Year.
        return join(sep=". ")[
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

    def get_inproceedings_template(self, e):
        # [3] AUTHOR. Title[C] // Booktitle. Address: Publisher, Year: Pages.
        return join(sep=". ")[
            self.format_names("author", as_sentence=False),
            join(sep=" // ")[join[field("title"), "[C]"], field("booktitle")],
            join(sep=", ")[
                join(sep=": ")[
                    optional_field("address"),
                    field("publisher"),
                ],
                field("year"),
                optional[field("pages")],
            ],
        ]

    def get_phdthesis_template(self, e):
        # [4] AUTHOR. Title[D]. Address: School, Year.
        return join(sep=". ")[
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

    def get_mastersthesis_template(self, e):
        return self.get_phdthesis_template(e)

    def get_techreport_template(self, e):
        # [5] AUTHOR. Title[R]. Address: Institution, Year.
        return join(sep=". ")[
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

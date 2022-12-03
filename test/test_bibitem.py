"""
"""

import itertools
from collections import OrderedDict

import pytest

from bib_lookup._bib import BibItem, BIB_ENTRY_TYPES, BIB_FIELDS


class TestBibItem:

    identifier = "10.1088/1361-6579/ac9451"
    entry_type = "article"
    fields = OrderedDict(
        title="A Novel Deep Learning Package for Electrocardiography Research",
        author="Hao Wen and Jingsu Kang",
        journal="Physiological Measurement",
        year=2022,
        month=11,
        publisher="IOP Publishing",
        volume=43,
        number=11,
        pages=115006,
    )

    bibitem = BibItem(
        identifier=identifier,
        entry_type=entry_type,
        fields=fields,
        label="xxx",
    )

    def test_eq(self):
        grid = itertools.product(
            [None, "10.1088/1361-6579/ac9451", "torch_ecg_paper"],  # label
            ["middle", "left", "left-middle", "left_middle"],  # align
            [True, False],  # check_fields
        )

        for label, align, check_fields in grid:
            bibitem_1 = BibItem(
                identifier=self.identifier,
                entry_type=self.entry_type,
                fields=self.fields,
                label=label,
                align=align,
                check_fields=check_fields,
            )
            print(bibitem_1)
            assert bibitem_1 == bibitem_1
            assert bibitem_1 != self.bibitem
            assert self.bibitem != bibitem_1
            assert bibitem_1.__eq__(self.bibitem, strict=True)
            assert self.bibitem.__eq__(bibitem_1, strict=True)

        for field in ["title", "author", "journal"]:
            tmp = self.fields.copy()
            tmp.pop(field)
            bibitem_1 = BibItem(
                identifier=self.identifier,
                entry_type=self.entry_type,
                fields=tmp,
                label="xxx",
            )
            assert bibitem_1 == self.bibitem
            assert self.bibitem == bibitem_1
            assert not bibitem_1.__eq__(self.bibitem, strict=True)
            assert not self.bibitem.__eq__(bibitem_1, strict=True)

        for field in [
            "year",
            "month",
            "publisher",
            "volume",
            "number",
            "pages",
        ]:
            tmp = self.fields.copy()
            tmp.pop(field)
            bibitem_1 = BibItem(
                identifier=self.identifier,
                entry_type=self.entry_type,
                fields=tmp,
                label="xxx",
            )
            assert bibitem_1 == self.bibitem
            assert self.bibitem == bibitem_1
            assert bibitem_1.__eq__(self.bibitem, strict=True)
            assert self.bibitem.__eq__(bibitem_1, strict=True)

        with pytest.raises(
            AssertionError, match="`self.strict_eq_fields` must be a subset of `.+`"
        ):
            bibitem_1 = BibItem(
                identifier=self.identifier,
                entry_type=self.entry_type,
                fields=tmp,
                label="xxx",
                strict_eq_fields=["year"],
            )
            bibitem_1.__eq__(self.bibitem, strict=True)

        with pytest.raises(
            AssertionError, match="`other.strict_eq_fields` must be a subset of `.+`"
        ):
            bibitem_1 = BibItem(
                identifier=self.identifier,
                entry_type=self.entry_type,
                fields=tmp,
                label="xxx",
                strict_eq_fields=["year"],
            )
            self.bibitem.__eq__(bibitem_1, strict=True)

        with pytest.warns(
            RuntimeWarning,
            match="`strict_eq_fields` are not the same in the two BibItems",
        ):
            bibitem_1 = BibItem(
                identifier=self.identifier,
                entry_type=self.entry_type,
                fields=tmp,
                label="xxx",
                strict_eq_fields=["title", "author"],
            )
            bibitem_1.__eq__(self.bibitem, strict=True)
            self.bibitem.__eq__(bibitem_1, strict=True)

    def test_help(self):
        for item in itertools.chain(BIB_ENTRY_TYPES, BIB_FIELDS):
            BibItem.help(item)
            self.bibitem.help(item)

    def test_errors(self):
        with pytest.raises(AssertionError, match="`xxx` is not a valid entry type"):
            BibItem(identifier=self.identifier, entry_type="xxx", fields=self.fields)

        with pytest.raises(
            AssertionError, match="`fields` must be `OrderedDict`, but got `.+`"
        ):
            BibItem(
                identifier=self.identifier,
                entry_type=self.entry_type,
                fields=dict(self.fields),
            )

        with pytest.raises(
            AssertionError,
            match="`align` must be one of \\['middle', 'left', 'left-middle', 'left_middle'\\], but got `xxx`",
        ):
            BibItem(
                identifier=self.identifier,
                entry_type=self.entry_type,
                fields=self.fields,
                align="xxx",
            )

        with pytest.raises(
            AssertionError, match="required field \042.+\042 is missing"
        ):
            tmp = self.fields.copy()
            tmp.pop("title")
            tmp.pop("author")
            BibItem(
                identifier=self.identifier,
                entry_type=self.entry_type,
                fields=tmp,
                check_fields=True,
            )

        with pytest.raises(
            AssertionError,
            match="required field\\(s\\) \042.+\042 is \\(are\\) missing",
        ):
            tmp = self.fields.copy()
            tmp.pop("title")
            tmp.pop("author")
            BibItem(
                identifier=self.identifier,
                entry_type="book",
                fields=tmp,
                check_fields=True,
            )

        with pytest.raises(
            AssertionError,
            match="`entries_or_fields` must be of type `str` or a sequence, but got `.+`",
        ):
            BibItem.help(1)

        with pytest.raises(
            AssertionError, match="`xxx` is not a valid entry type or field name"
        ):
            BibItem.help("xxx")

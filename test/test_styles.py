import pytest
from pybtex.database import Entry, Person

from bib_lookup.styles.apa import APANames, APAStyle
from bib_lookup.styles.chicago import ChicagoNames, ChicagoStyle, chicago_date, chicago_pages
from bib_lookup.styles.gbt7714 import GBT7714Style, GBTNames
from bib_lookup.styles.ieee import IEEENames, IEEEStyle, ieee_month, ieee_pages

EXAMPLES = [
    {
        "entry": """
@article{qi2021kemre,
      title = {{KeMRE: Knowledge-Enhanced Medical Relation Extraction for Chinese Medicine Instructions}},
     author = {Tao Qi and Shan Qiu and Xiaoqian Shen and Haopu Chen and Shuai Yang and Hao Wen and Ya Zhang and Yuanqing Wu and Yongfeng Huang},
    journal = {{Journal of Biomedical Informatics}},
        doi = {10.1016/j.jbi.2021.103834},
       year = {2021},
      month = {8},
  publisher = {{Elsevier BV}},
     volume = {120},
      pages = {103834}
}""",
        "apa": """Qi, T., Qiu, S., Shen, X., Chen, H., Yang, S., Wen, H., Zhang, Y., Wu, Y., & Huang, Y. (2021). KeMRE: Knowledge-Enhanced Medical Relation Extraction for Chinese Medicine Instructions. Journal of Biomedical Informatics, 120, 103834. https://doi.org/10.1016/j.jbi.2021.103834""",
        "ieee": """Tao Qi et al. “KeMRE: Knowledge-Enhanced Medical Relation Extraction for Chinese Medicine Instructions”. In: Journal of Biomedical Informatics 120 (Aug. 2021), p. 103834. doi: 10.1016/j.jbi.2021.103834.""",
        "gbt7714": """QI T, QIU S, SHEN X, et al. KeMRE: Knowledge-Enhanced Medical Relation Extraction for Chinese Medicine Instructions[J/OL]. Journal of Biomedical Informatics, 2021, 120: 103834. DOI: 10.1016/j.jbi.2021.103834.""",
        "chicago": """Qi, Tao, Shan Qiu, Xiaoqian Shen, Haopu Chen, Shuai Yang, Hao Wen, Ya Zhang, Yuanqing Wu, and Yongfeng Huang. “KeMRE: Knowledge-Enhanced Medical Relation Extraction for Chinese Medicine Instructions.” Journal of Biomedical Informatics 120 (August 2021): 103834. https://doi.org/10.1016/j.jbi.2021.103834.""",
    },
]


def _r(node, entry, style=None):
    context = {"entry": entry, "bib_data": None, "style": style}
    return str(node.format_data(context)).strip()


def test_styles_coverage_100():
    def ctx(entry):
        return {"entry": entry}

    class NoP:
        pass

    p1 = Person(first="A", last="B")
    e_full = Entry(
        "a",
        fields={
            "title": "T",
            "journal": "J",
            "year": "2021",
            "doi": "10.1",
            "publisher": "P",
            "booktitle": "BT",
            "school": "S",
            "institution": "I",
            "volume": "1",
            "number": "2",
            "pages": "10",
            "address": "A",
        },
        persons={"author": [p1, p1, p1, p1, p1]},
    )

    # 1. GBT7714
    style_gbt = GBT7714Style()
    gn = GBTNames("author", str)
    assert gn.format_data(ctx(Entry("a"))) == ""  # Line 34
    assert gn.format_data({"entry": Entry("a")}) == ""  # Line 20
    assert gn.format_data(NoP()) == ""  # Line 31
    assert style_gbt.format_names("author", as_sentence=False).format_data(ctx(e_full))  # Line 69
    assert "T" in _r(style_gbt.get_inproceedings_template(e_full), e_full, style_gbt)  # Line 146
    for m in [
        style_gbt.get_article_template,
        style_gbt.get_book_template,
        style_gbt.get_phdthesis_template,
        style_gbt.get_techreport_template,
    ]:
        assert m(e_full)

    # 2. IEEE
    style_ieee = IEEEStyle()
    in_names = IEEENames("author", str)
    assert in_names.format_data(Entry("a")) == ""  # Line 35
    assert in_names.format_data(NoP()) == ""  # Line 39
    e2 = Entry("a", persons={"author": [p1, p1]})
    assert "and" in in_names.format_data(ctx(e2))  # Line 51
    assert "p. 5" in _r(ieee_pages, Entry("a", fields={"pages": "5"}))  # Line 73
    assert "DOI" in _r(style_ieee.get_phdthesis_template(e_full), e_full, style_ieee)  # Lines 131-132, 138, 141
    assert style_ieee.format_names("author", as_sentence=False).format_data(ctx(e_full))  # Line 105
    for m in [style_ieee.get_article_template, style_ieee.get_book_template, style_ieee.get_inproceedings_template]:
        assert m(e_full)

    # 3. APA
    style_apa = APAStyle()
    an = APANames("author", str)
    assert an.format_data(Entry("a")) == ""  # Line 34
    assert an.format_data(NoP()) == ""  # Line 39
    apa_style_names_check = str(
        an.format_data(ctx(Entry("a", persons={"author": [Person(str(i)) for i in range(21)]})))
    )  # Line 48-51 (21+ authors)
    assert "..." in apa_style_names_check
    assert style_apa.format_names("author", as_sentence=False).format_data(ctx(e_full))  # Line 62
    assert "L, Jr." in style_apa._format_person(Person(last="L", lineage="Jr."))  # Line 70
    assert "https" not in _r(
        style_apa.get_article_template(Entry("a", fields={"title": "T", "year": "2021", "journal": "J"})),
        Entry("a", fields={"title": "T", "year": "2021", "journal": "J"}),
        style_apa,
    )  # Line 83
    assert "T" in _r(
        style_apa.get_book_template(Entry("b", fields={"title": "T", "year": "2021", "publisher": "P"})),
        Entry("b", fields={"title": "T", "year": "2021", "publisher": "P"}),
        style_apa,
    )  # Line 86
    assert "BT" in _r(style_apa.get_inproceedings_template(e_full), e_full, style_apa)  # Line 113

    # 4. Chicago
    style_chi = ChicagoStyle()
    cn = ChicagoNames("author", lambda p, first_author=False: "N")
    assert cn.format_data(Entry("a")) == ""  # Line 34
    assert cn.format_data(NoP()) == ""  # Line 44
    assert "and" in str(cn.format_data(ctx(e2)))  # Line 55-60
    cn_long = ChicagoNames("author", lambda p, first_author=False: "N")
    e11 = Entry("a", persons={"author": [Person(str(i)) for i in range(11)]})
    assert "et al" in cn_long.format_data(ctx(e11))  # Line 63
    assert style_chi.format_names("author", as_sentence=False).format_data(ctx(e_full))  # Line 77
    assert style_chi.format_label(e2) == ""  # Line 89
    assert "" == _r(chicago_date, Entry("a"))  # Line 100
    assert "https" not in _r(
        style_chi.get_article_template(Entry("a", fields={"title": "T", "journal": "J", "year": "2021"})),
        Entry("a", fields={"title": "T", "journal": "J", "year": "2021"}),
        style_chi,
    )  # Line 109


def test_misc():
    with pytest.raises(ValueError):
        GBTNames("author", str, limit=0)
    from bib_lookup import BibLookup

    assert BibLookup(verbose=0).max_names == 3
    for node in [ieee_pages, ieee_month, chicago_pages, chicago_date]:
        assert str(node.format_data({})) == ""

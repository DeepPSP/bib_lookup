import io

from pybtex.backends.plaintext import Backend as TextBackend
from pybtex.database import parse_string

from bib_lookup import BibLookup
from bib_lookup.styles.gbt7714 import GBT7714Style


def _format_bibtex_string(bib_str: str) -> str:
    bib_data = parse_string(bib_str, bib_format="bibtex")
    custom_style = GBT7714Style()
    formatted_entries = custom_style.format_entries(bib_data.entries.values())

    backend = TextBackend()
    output = io.StringIO()

    for entry in formatted_entries:
        backend.write_to_stream([entry], output)

    return output.getvalue().strip()


def test_gbt7714_style(monkeypatch):
    bl = BibLookup(verbose=0, max_names=3)

    class MockResponse:
        status_code = 200
        content = b"""@article{Yao_2020,
          title = {Multi-class Arrhythmia detection from 12-lead varied-length ECG using Attention-based Time-Incremental Convolutional Neural Network},
          author = {Yao, Qihang and Wang, Ruxin and Fan, Xiaomao and Liu, Jikui and Li, Ye},
          journal = {Information Fusion},
          volume = {53},
          issn = {1566-2535},
          doi = {10.1016/j.inffus.2019.06.024},
          pages = {174--182},
          year = {2020},
          publisher = {Elsevier BV}
        }"""

    monkeypatch.setattr(bl.session, "get", lambda *args, **kwargs: MockResponse())

    # Using a known DOI: 10.1016/j.inffus.2019.06.024
    res = bl("10.1016/j.inffus.2019.06.024", format="text", style="gbt7714")
    print(f"\nGBT7714 Output:\n{res}")

    # Verify name formatting (Last Name + Initial)
    # GBT7714 style abbreviates first names and removes punctuation: "Yao Q"
    assert "Yao Q" in res
    # Verify "et al" (more than 3 authors)
    assert "et al" in res
    assert "[J]" in res
    assert "Information Fusion" in res
    assert "2020" in res
    # Verify colon separator for pages in Article
    assert "53: 174" in res
    # Verify DOI is present
    assert "DOI: 10.1016/j.inffus.2019.06.024" in res
    # Verify period at end
    assert res.endswith(".")


def test_gbt7714_book():
    bib_str = """
    @book{test_book,
        author = {Knuth, Donald E.},
        title = {The Art of Computer Programming},
        publisher = {Addison-Wesley},
        year = {1968},
        address = {Reading, Mass.}
    }
    """
    res = _format_bibtex_string(bib_str)
    # Expected: Knuth D E. The Art of Computer Programming[M]. Reading, Mass.: Addison-Wesley, 1968.
    assert "Knuth D E" in res
    assert "The Art of Computer Programming[M]" in res
    assert "Reading, Mass.: Addison-Wesley, 1968" in res


def test_gbt7714_inproceedings():
    bib_str = """
    @inproceedings{test_inproc,
        author = {Vaswani, Ashish and others},
        title = {Attention is All You Need},
        booktitle = {Advances in Neural Information Processing Systems},
        year = {2017},
        pages = {5998--6008},
        publisher = {Curran Associates, Inc.},
        address = {Long Beach, CA, USA}
    }
    """
    res = _format_bibtex_string(bib_str)
    # Expected: Vaswani A, et al. Attention is All You Need[C] // Advances in Neural Information Processing Systems. Long Beach, CA, USA: Curran Associates, Inc., 2017: 5998–6008.
    assert "Attention is All You Need[C] // Advances in Neural Information Processing Systems" in res
    assert "Long Beach, CA, USA: Curran Associates, Inc., 2017" in res
    # Verify colon separator for pages in InProceedings: Year: Pages
    assert "2017: 5998" in res


def test_gbt7714_phdthesis():
    bib_str = """
    @phdthesis{test_phd,
        author = {Shannon, Claude E.},
        title = {A Symbolic Analysis of Relay and Switching Circuits},
        school = {Massachusetts Institute of Technology},
        year = {1940},
        address = {Cambridge, MA}
    }
    """
    res = _format_bibtex_string(bib_str)
    # Expected: Shannon C E. A Symbolic Analysis of Relay and Switching Circuits[D]. Cambridge, MA: Massachusetts Institute of Technology, 1940.
    assert "Shannon C E" in res
    assert "A Symbolic Analysis of Relay and Switching Circuits[D]" in res


def test_gbt7714_techreport():
    bib_str = """
    @techreport{test_report,
        author = {Page, Lawrence and Brin, Sergey},
        title = {The PageRank Citation Ranking: Bringing Order to the Web},
        institution = {Stanford Digital Library Technologies Project},
        year = {1998},
        address = {Stanford, CA}
    }
    """
    res = _format_bibtex_string(bib_str)
    # Expected: Page L, Brin S. The PageRank Citation Ranking: Bringing Order to the Web[R]. Stanford, CA: Stanford Digital Library Technologies Project, 1998.
    assert "The PageRank Citation Ranking: Bringing Order to the Web[R]" in res
    assert "Stanford, CA: Stanford Digital Library Technologies Project, 1998" in res


def test_gbt7714_mastersthesis():
    bib_str = """
    @mastersthesis{test_master,
        author = {Doe, John},
        title = {My Master Thesis},
        school = {Some University},
        year = {2023},
        address = {Some City}
    }
    """
    res = _format_bibtex_string(bib_str)
    assert "My Master Thesis[D]" in res
    assert "Some City: Some University, 2023" in res


def test_gbt7714_misc():
    bib_str = """
    @misc{test_misc,
        author = {Nobody, N.},
        title = {Something Miscellaneous},
        year = {2024}
    }
    """
    res = _format_bibtex_string(bib_str)
    # UnsrtStyle misc template uses format_names with defaults (as_sentence=True)
    # Should use GBT format: Nobody N
    assert "Nobody N" in res
    # Pybtex might lowercase the title in standard styles
    assert "Something miscellaneous" in res.replace("Miscellaneous", "miscellaneous")


def test_gbt7714_max_names():
    # Test configurable max_names
    bib_str = """
    @article{test_max_names,
        author = {A, A and B, B and C, C and D, D and E, E},
        title = {Test Max Names},
        journal = {Test Journal},
        year = {2024}
    }
    """

    # Default is 3
    # Check manual instantiation of style
    style = GBT7714Style(max_names=3)
    db = parse_string(bib_str, bib_format="bibtex")
    formatted_entries = list(style.format_entries(db.entries.values()))
    backend = TextBackend()
    output = io.StringIO()
    backend.write_to_stream(formatted_entries, output)
    res = output.getvalue().strip()
    # Should have 3 names + et al
    assert "A A, B B, C C, et al" in res

    # Change to 4
    style = GBT7714Style(max_names=4)
    formatted_entries = list(style.format_entries(db.entries.values()))
    output = io.StringIO()
    backend.write_to_stream(formatted_entries, output)
    res = output.getvalue().strip()
    # Should have 4 names + et al
    assert "A A, B B, C C, D D, et al" in res

    # Change to 10
    style = GBT7714Style(max_names=10)
    formatted_entries = list(style.format_entries(db.entries.values()))
    output = io.StringIO()
    backend.write_to_stream(formatted_entries, output)
    res = output.getvalue().strip()
    # Should have all names, no et al
    assert "A A, B B, C C, D D, E E" in res
    assert "et al" not in res


def test_bib_lookup_max_names(monkeypatch):
    # Test BibLookup integration
    bl = BibLookup(verbose=0, max_names=2)

    class MockResponse:
        status_code = 200
        content = b"""@article{Test,
          title = {Test},
          author = {A, A and B, B and C, C},
          journal = {J},
          year = {2020}
        }"""

    monkeypatch.setattr(bl.session, "get", lambda *args, **kwargs: MockResponse())

    res = bl("10.1016/test", format="text", style="gbt7714")
    # With max_names=2 and 3 authors, should have 2 names + et al
    assert "A A, B B, et al" in res


def test_gbt7714_coverage_edge_cases():
    """Test edge cases for 100% coverage in gbt7714.py"""

    # Test GBTNames directly for defensive checks
    from bib_lookup.styles.gbt7714 import GBTNames

    # Mock formatter
    # formatter = lambda x: str(x)
    node = GBTNames("author", str)

    # Test: data has no 'persons' attribute
    class DummyData:
        pass

    assert node.format_data(DummyData()) == ""

    # Test: role not in persons
    from pybtex.database import Entry

    entry_no_author = Entry("article")
    # Entry has .persons attribute (defaultdict), but 'author' won't be in it if not added
    # Actually pybtex.database.Entry.persons is a CaseInsensitiveOrderedDict inside a generic container?
    # Let's just verify behavior with an empty entry
    assert node.format_data(entry_no_author) == ""

    # Test 'von' part in names
    bib_von = """
    @article{test_von,
        author = {van Rossum, Guido},
        title = {Python},
        journal = {Journal of Programming Languages},
        year = {1991}
    }
    """
    res = _format_bibtex_string(bib_von)
    # Expected: van Rossum G
    assert "van Rossum G" in res

    # Test DOI in various types

    # Book with DOI
    bib_book_doi = """
    @book{test_book_doi,
        author = {Knuth, D. E.},
        title = {The Art of Computer Programming},
        publisher = {Addison-Wesley},
        year = {1968},
        doi = {10.1000/book_doi}
    }
    """
    res = _format_bibtex_string(bib_book_doi)
    assert "DOI: 10.1000/book_doi" in res

    # InProceedings with DOI
    bib_inproc_doi = """
    @inproceedings{test_inproc_doi,
        author = {Vaswani, A.},
        title = {Attention},
        booktitle = {NIPS},
        publisher = {Curran Associates},
        year = {2017},
        doi = {10.1000/inproc_doi}
    }
    """
    res = _format_bibtex_string(bib_inproc_doi)
    assert "DOI: 10.1000/inproc_doi" in res

    # PhdThesis with DOI
    bib_phd_doi = """
    @phdthesis{test_phd_doi,
        author = {Shannon, C.},
        title = {Information Theory},
        school = {MIT},
        year = {1940},
        doi = {10.1000/phd_doi}
    }
    """
    res = _format_bibtex_string(bib_phd_doi)
    assert "DOI: 10.1000/phd_doi" in res

    # TechReport with DOI
    bib_tech_doi = """
    @techreport{test_tech_doi,
        author = {Page, L.},
        title = {PageRank},
        institution = {Stanford},
        year = {1998},
        doi = {10.1000/tech_doi}
    }
    """
    res = _format_bibtex_string(bib_tech_doi)
    assert "DOI: 10.1000/tech_doi" in res

    # 4. Test Lineage
    bib_lineage = """
    @article{test_lineage,
        author = {King, Jr., Martin Luther and Gates, III, William H.},
        title = {I Have a Dream},
        year = {1963},
        journal = {Journal of Lineage}
    }
    """
    res = _format_bibtex_string(bib_lineage)
    # Expected: King Jr M L, Gates III W H (dots stripped)
    assert "King Jr M L" in res
    assert "Gates III W H" in res

    # 5. Test Invalid max_names
    import pytest

    with pytest.raises(ValueError, match="must be an integer >= 1"):
        GBTNames("author", str, limit=0)

    with pytest.raises(ValueError, match="must be an integer >= 1"):
        GBTNames("author", str, limit=-1)

    with pytest.raises(ValueError, match="must be an integer >= 1"):
        GBTNames("author", str, limit="3")

    # Test BibLookup validation
    with pytest.raises(ValueError, match="must be an integer >= 1"):
        BibLookup(max_names=0)

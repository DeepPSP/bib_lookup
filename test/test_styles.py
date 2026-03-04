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


def test_gbt7714_style():
    bl = BibLookup(verbose=0)
    # Using a known DOI: 10.1016/j.inffus.2019.06.024
    res = bl("10.1016/j.inffus.2019.06.024", format="text", style="gbt7714")
    print(f"\nGBT7714 Output:\n{res}")

    assert "Yao, Qihang" in res
    # Check for [J] which is specific to GBT7714 for articles
    assert "[J]" in res
    assert "Information Fusion" in res
    assert "2020" in res
    # Verify colon separator for pages in Article
    # Volume 53, Pages 174-182 -> "53: 174"
    assert "53: 174" in res


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
    # Expected: Knuth, Donald E.. The Art of Computer Programming[M]. Reading, Mass.: Addison-Wesley, 1968.
    assert "Knuth, Donald E." in res
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
    # Expected: Vaswani, Ashish, others. Attention is All You Need[C] // Advances in Neural Information Processing Systems. Long Beach, CA, USA: Curran Associates, Inc., 2017: 5998–6008.
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
    # Expected: Shannon, Claude E.. A Symbolic Analysis of Relay and Switching Circuits[D]. Cambridge, MA: Massachusetts Institute of Technology, 1940.
    assert "A Symbolic Analysis of Relay and Switching Circuits[D]" in res
    assert "Cambridge, MA: Massachusetts Institute of Technology, 1940" in res


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
    # Expected: Page, Lawrence, Brin, Sergey. The PageRank Citation Ranking: Bringing Order to the Web[R]. Stanford, CA: Stanford Digital Library Technologies Project, 1998.
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
    assert "Nobody, N." in res
    # Pybtex might lowercase the title in standard styles
    assert "Something miscellaneous" in res.replace("Miscellaneous", "miscellaneous")

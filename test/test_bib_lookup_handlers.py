import types
from types import SimpleNamespace

import requests

from bib_lookup.bib_lookup import NETWORK_ERROR_MESSAGES, BibLookup


# Helper response classes
class FakeResp:
    def __init__(self, content: bytes = b"", text: str = "", json_obj=None, status_code: int = 200, headers: dict = {}):
        self.content = content
        self.text = text
        self._json = json_obj
        self.status_code = status_code
        self.headers = headers

    def json(self):
        if self._json is None:
            raise ValueError("no json")
        return self._json


def test_handle_doi_timeout(monkeypatch):
    bl = BibLookup()

    # fake post raises Timeout
    def fake_get(**kwargs):
        raise requests.Timeout("timeout")

    monkeypatch.setattr(bl.session, "get", fake_get, raising=True)

    res = bl._handle_doi({"url": "http://example"})  # feed_content can be any kwargs
    assert res == bl.timeout_err


def test_handle_doi_request_exception(monkeypatch):
    bl = BibLookup()

    def fake_get(**kwargs):
        raise requests.RequestException("net")

    monkeypatch.setattr(bl.session, "get", fake_get, raising=True)

    res = bl._handle_doi({"url": "http://example"})
    assert res == bl.network_err


def test_handle_doi_success(monkeypatch):
    bl = BibLookup()

    # return content bytes that decode to "OK"
    def fake_get(**kwargs):
        return FakeResp(content=b"OK")

    monkeypatch.setattr(bl.session, "get", fake_get, raising=True)

    res = bl._handle_doi({"url": "http://example", "headers": {"Accept": "application/x-bibtex"}})
    # If content starts with @, it returns immediately
    # But here content is just "OK", which doesn't start with @
    # So it proceeds to fallback
    # However, "http://example" does NOT contain "doi.org", so fallback is skipped
    # And it returns "OK"
    assert res == "OK"


def test_handle_pm_timeout(monkeypatch):
    bl = BibLookup()

    def fake_get(**kwargs):
        raise requests.Timeout()

    monkeypatch.setattr(bl.session, "get", fake_get, raising=True)

    res = bl._handle_pm({"url": "http://example"})
    assert res == bl.timeout_err


def test_handle_pm_request_exception(monkeypatch):
    bl = BibLookup()

    def fake_get(**kwargs):
        raise requests.RequestException()

    monkeypatch.setattr(bl.session, "get", fake_get, raising=True)

    res = bl._handle_pm({"url": "http://example"})
    assert res == bl.network_err


def test_handle_pm_no_doi(monkeypatch):
    bl = BibLookup()
    # r.json returns records[0] without doi
    fake_json = {"records": [{}]}

    def fake_get(**kwargs):
        return FakeResp(json_obj=fake_json, text="{}")

    monkeypatch.setattr(bl.session, "get", fake_get, raising=True)

    res = bl._handle_pm({"url": "http://example"})
    assert res == bl.default_err


def test_handle_pm_with_doi_calls_handle_doi(monkeypatch):
    bl = BibLookup()
    # r.json returns doi present
    fake_json = {"records": [{"doi": "10.1234/abc"}]}

    def fake_get(**kwargs):
        return FakeResp(json_obj=fake_json, text="{}")

    monkeypatch.setattr(bl.session, "get", fake_get, raising=True)

    # monkeypatch _obtain_feed_content to return feed_content for _handle_doi
    def fake_obtain_feed_content(doi, timeout=None):
        return (None, {"url": "http://doi-res"}, None)

    monkeypatch.setattr(bl, "_obtain_feed_content", fake_obtain_feed_content, raising=True)

    # monkeypatch _handle_doi to return sentinel
    monkeypatch.setattr(bl, "_handle_doi", lambda feed_content: "DOI-RESULT", raising=True)

    res = bl._handle_pm({"url": "http://example"})
    assert res == "DOI-RESULT"


def test_handle_arxiv_timeout_and_request_exc(monkeypatch):
    bl = BibLookup()

    def fake_get_t(**kwargs):
        raise requests.Timeout()

    monkeypatch.setattr(bl.session, "get", fake_get_t, raising=True)
    assert bl._handle_arxiv({"url": "http://a"}) == bl.timeout_err

    def fake_get_r(**kwargs):
        raise requests.RequestException()

    monkeypatch.setattr(bl.session, "get", fake_get_r, raising=True)
    assert bl._handle_arxiv({"url": "http://a"}) == bl.network_err


def test_handle_arxiv_title_error(monkeypatch):
    bl = BibLookup()
    # build parsed object with title == "Error"
    parsed = {
        "title": "Error",
        "id": "http://arxiv.org/abs/1234",
        "published_parsed": SimpleNamespace(tm_year=2020, tm_mon=1),
        "authors": [{"name": "Alice"}],
    }
    # monkeypatch session.get to return content (ignored by our feedparser patch)
    monkeypatch.setattr(bl.session, "get", lambda **kw: FakeResp(content=b"<xml/>"), raising=True)
    # monkeypatch feedparser.parse to return .entries with parsed
    import feedparser

    monkeypatch.setattr(feedparser, "parse", lambda content: types.SimpleNamespace(entries=[parsed]), raising=True)

    res = bl._handle_arxiv({"url": "http://example"})
    assert res == bl.default_err


def test_handle_arxiv_success(monkeypatch):
    bl = BibLookup()
    parsed = {
        "title": "A Good Paper",
        "id": "http://arxiv.org/abs/2101.00001v2",
        "published_parsed": SimpleNamespace(tm_year=2021, tm_mon=7),
        "authors": [{"name": "Jane Doe"}, {"name": "John Q Public"}],
    }
    monkeypatch.setattr(bl.session, "get", lambda **kw: FakeResp(content=b"<xml/>"), raising=True)
    import feedparser

    monkeypatch.setattr(feedparser, "parse", lambda content: types.SimpleNamespace(entries=[parsed]), raising=True)

    res = bl._handle_arxiv({"url": "http://example"})
    # check returned dict structure and some fields
    assert isinstance(res, dict)
    assert res["title"] == "A Good Paper"
    assert res["year"] == 2021
    assert "author" in res and "Jane Doe" in res["author"]
    assert res["doi"].startswith("10.48550/arXiv.")


def test_handle_network_error_variants():
    bl = BibLookup()
    # DOI Not Found -> default_err
    assert bl._handle_network_error("DOI Not Found") == bl.default_err

    # contains any NETWORK_ERROR_MESSAGES -> network_err
    # pick first known message from NETWORK_ERROR_MESSAGES
    msg = NETWORK_ERROR_MESSAGES[0] if NETWORK_ERROR_MESSAGES else "Service Unavailable"
    assert bl._handle_network_error(msg) == bl.network_err

    # unrelated string -> unchanged
    s = "some normal response"
    assert bl._handle_network_error(s) == s

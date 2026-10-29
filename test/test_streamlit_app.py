"""Tests for the Streamlit web app (`streamlit_app.py`), using the official
Streamlit AppTest framework.

`BibLookup.__call__` is stubbed so no test touches the network; the tests
assert the app's reactive behavior: lookups triggered by pressing enter,
config changes re-rendering from the session cache without a new network
call, and results persisting across script re-runs.
"""

import pytest

pytest.importorskip("streamlit.testing")

from streamlit.testing.v1 import AppTest  # noqa: E402

from bib_lookup.bib_lookup import BibLookup  # noqa: E402

APP_PATH = __file__.rsplit("/", 2)[0] + "/streamlit_app.py"

CANNED_BIBTEX = "@article{X_2020,\n  title = {Test Title},\n  journal = {J},\n  year = {2020}\n}"
LOOKUP_ERRORS = ["Not Found", "Network Error", "Timeout Error", "Format Error", "Parse Error"]
REDIRECT_MESSAGE = f"{BibLookup.__REDIRECT_FLAG__} Automatic lookup failed. Please visit: https://example.org/paper"


@pytest.fixture()
def stubbed_app(monkeypatch):
    """Stub the network-facing methods of BibLookup and return an AppTest."""
    calls = []

    def fake_call(self, identifier, **kwargs):
        calls.append(identifier)
        return fake_call.result

    def fake_to_bib_item(self, res, **kwargs):
        return f"RENDERED({kwargs.get('align')}, {kwargs.get('capitalize_title')})"

    fake_call.result = CANNED_BIBTEX
    monkeypatch.setattr(BibLookup, "__call__", fake_call)
    monkeypatch.setattr(BibLookup, "_to_bib_item", fake_to_bib_item)
    monkeypatch.setattr(BibLookup, "lookup_errors", property(lambda self: LOOKUP_ERRORS))

    at = AppTest.from_file(APP_PATH, default_timeout=60)
    at.run()
    assert not at.exception
    at.calls = calls  # expose the stub call log on the AppTest object
    at.fake_call = fake_call  # expose the stub result for per-test tweaking
    return at


def test_enter_triggers_lookup_without_button(stubbed_app):
    at = stubbed_app
    at.text_input[0].set_value("10.1234/abc").run()
    assert at.calls == ["10.1234/abc"]
    assert len(at.code) == 1
    assert CANNED_BIBTEX in at.code[0].value


def test_align_change_rerenders_from_cache(stubbed_app):
    at = stubbed_app
    at.text_input[0].set_value("10.1234/abc").run()
    n_calls = len(at.calls)

    at.sidebar.selectbox[0].set_value("left").run()  # alignment
    assert len(at.calls) == n_calls, "align change must not trigger a new lookup"
    assert "RENDERED(left, False)" in at.code[0].value

    at.sidebar.checkbox[1].set_value(True).run()  # capitalize title
    assert len(at.calls) == n_calls, "capitalize change must not trigger a new lookup"
    assert "RENDERED(left, True)" in at.code[0].value


def test_format_round_trip_reuses_cache(stubbed_app):
    at = stubbed_app
    at.text_input[0].set_value("10.1234/abc").run()
    n_calls = len(at.calls)

    at.sidebar.selectbox[1].set_value("text").run()  # bibtex -> text: new query
    assert len(at.calls) == n_calls + 1
    assert at.code[0].value == CANNED_BIBTEX

    at.sidebar.selectbox[1].set_value("bibtex").run()  # text -> bibtex: cached
    assert len(at.calls) == n_calls + 1, "returning to bibtex must reuse the cache"
    # the cached bibtex entry is re-rendered locally via `_to_bib_item`
    assert at.code[0].value == "RENDERED(middle, False)"


def test_result_persists_across_plain_rerun(stubbed_app):
    at = stubbed_app
    at.text_input[0].set_value("10.1234/abc").run()
    at.run()  # e.g. websocket reconnect: plain re-run without any widget change
    assert len(at.code) == 1, "result must survive a plain script re-run"
    assert len(at.calls) == 1


def test_clearing_input_clears_result(stubbed_app):
    at = stubbed_app
    at.text_input[0].set_value("10.1234/abc").run()
    at.text_input[0].set_value("").run()
    assert len(at.code) == 0
    assert at.session_state["last_render"] is None


def test_redirect_result(stubbed_app):
    at = stubbed_app
    at.fake_call.result = REDIRECT_MESSAGE
    at.text_input[0].set_value("10.9999/china-doi").run()
    assert at.session_state["last_render"]["status"] == "redirect"
    assert at.session_state["last_render"]["url"] == "https://example.org/paper"
    assert len(at.warning) == 1


def test_lookup_error_result(stubbed_app, monkeypatch):
    at = stubbed_app
    monkeypatch.setattr(BibLookup, "__call__", lambda self, identifier, **kw: "Not Found")
    at.run()  # re-run with the failing stub
    at.text_input[0].set_value("10.1234/missing").run()
    assert at.session_state["last_render"]["status"] == "error"
    assert "Lookup Failed: Not Found" in at.error[0].value


def test_lookup_exception_result(stubbed_app, monkeypatch):
    at = stubbed_app

    def boom(self, identifier, **kw):
        raise RuntimeError("boom")

    monkeypatch.setattr(BibLookup, "__call__", boom)
    at.run()
    at.text_input[0].set_value("10.1234/abc").run()
    assert at.session_state["last_render"]["status"] == "error"
    assert "Error: boom" in at.error[0].value

import streamlit as st

from bib_lookup import BibLookup, __version__

st.set_page_config(
    page_title="Bib Lookup",
    page_icon=":books:",
    layout="centered",
)


@st.cache_resource
def get_bib_lookuper():
    return BibLookup(verbose=0)


# the marker that follows the resolvable URL in BibLookup's redirect message
REDIRECT_URL_MARKER = "visit: "


def current_config():
    return {
        "doi": st.session_state.get("input_doi", "").strip(),
        "arxiv2doi": st.session_state.get("arxiv2doi", True),
        "align": st.session_state.get("align", "middle"),
        "fmt": st.session_state.get("fmt", "bibtex"),
        "capitalize_title": st.session_state.get("capitalize_title", False),
    }


def cache_key(cfg):
    return f"{cfg['doi']}||{cfg['arxiv2doi']}||{cfg['fmt']}"


def render_success(container, text: str) -> None:
    container.code(text, language="latex", line_numbers=False)


def render_redirect(container, url: str) -> None:
    container.warning("⚠️ This DOI cannot be resolved to BibTeX automatically (ChinaDOI/CNKI).")
    container.link_button("👉 Click to visit Article Page", url)


def do_lookup():
    """Perform (or re-render) the lookup and store the result in the session state.

    The result is kept in ``st.session_state["last_render"]`` instead of being
    written to widgets directly, so it survives script re-runs (e.g. websocket
    reconnects) and is re-displayed without another lookup.
    """
    cfg = current_config()
    render = None
    if cfg["doi"]:
        history = st.session_state.setdefault("history", {})
        slot = history.get(cache_key(cfg))
        if slot is not None:
            # cache hit: no network call; a cached bibtex entry can be
            # re-rendered locally with the current align / capitalize settings
            if cfg["fmt"] == "bibtex":
                bib = str(bl._to_bib_item(slot, align=cfg["align"], capitalize_title=cfg["capitalize_title"]))
            else:
                bib = slot
            render = {"status": "success", "text": bib}
        else:
            try:
                bib = bl(
                    cfg["doi"],
                    arxiv2doi=cfg["arxiv2doi"],
                    format=cfg["fmt"],
                    align=cfg["align"],
                    capitalize_title=cfg["capitalize_title"],
                )
            except Exception as e:
                render = {"status": "error", "text": f"Error: {e}"}
            else:
                if bib and bib.startswith(BibLookup.__REDIRECT_FLAG__):
                    render = {"status": "redirect", "url": bib.split(REDIRECT_URL_MARKER)[-1].strip()}
                elif bib in bl.lookup_errors:
                    render = {"status": "error", "text": f"Lookup Failed: {bib}"}
                else:
                    history[cache_key(cfg)] = bib
                    render = {"status": "success", "text": bib}
    st.session_state["last_render"] = render
    st.session_state["confirmed_doi"] = False


bl = get_bib_lookuper()


st.title("Bib Lookup 🔍")

# show the version number on the sidebar
st.sidebar.markdown(f"version: {__version__}")

# configurations on the sidebar

st.sidebar.title("Configurations")
# select the style of alignment
st.sidebar.selectbox(
    label="Alignment",
    options=["middle", "left", "left-middle"],
    index=0,
    key="align",
    on_change=lambda: st.session_state.update({"confirmed_doi": True}),
)
# select the format of the output
st.sidebar.selectbox(
    label="Format",
    options=["bibtex", "text", "rdf-xml", "turtle", "ris", "crossref-xml", "datacite-xml", "crossref-tdm", "bibentry"],
    index=0,
    key="fmt",
    on_change=lambda: st.session_state.update({"confirmed_doi": True}),
)
# toggle arxiv2doi to be on or off
st.sidebar.checkbox(
    label="arXiv ID to DOI",
    value=True,
    key="arxiv2doi",
    on_change=lambda: st.session_state.update({"confirmed_doi": True}),
)
# toggle capitalize_title to be on or off
st.sidebar.checkbox(
    label="Capitalize title",
    value=False,
    key="capitalize_title",
    on_change=lambda: st.session_state.update({"confirmed_doi": True}),
)
# link to issue tracker on GitHub
st.sidebar.divider()
st.sidebar.markdown("**:red[🛠️ Report an issue]**")
c1, c2 = st.sidebar.columns(2)
c1.link_button("GitHub", "https://github.com/DeepPSP/bib_lookup/issues", use_container_width=True)
c2.link_button("Gitee", "https://gitee.com/deep-psp/bib_lookup/issues", use_container_width=True)


col_input, col_btn = st.columns([4, 1], gap="small")

# input on the main page
with col_input:
    st.text_input(
        label="**DOI / PubMed ID / arXiv ID**",
        label_visibility="collapsed",
        value="",
        max_chars=100,
        key="input_doi",
        placeholder="Paste DOI, arXiv ID, or PubMed ID here...",
        on_change=lambda: st.session_state.update({"confirmed_doi": True}),
    )
# a "Search" button to trigger the lookup on the right side of the input box
with col_btn:
    st.button(
        label="Search",
        key="button",
        type="primary",
        use_container_width=True,
        on_click=lambda: st.session_state.update({"confirmed_doi": True}),
    )

# perform the lookup (updates `last_render` in the session state) ...
if st.session_state.get("confirmed_doi", False):
    do_lookup()

# ... and (re-)render the last result, which persists across script re-runs
last_render = st.session_state.get("last_render")
if last_render is not None:
    st.divider()
    output_container = st.container()
    with output_container:
        if last_render["status"] == "success":
            render_success(output_container, last_render["text"])
        elif last_render["status"] == "error":
            output_container.error(last_render["text"])
        elif last_render["status"] == "redirect":
            render_redirect(output_container, last_render["url"])

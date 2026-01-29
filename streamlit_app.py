import warnings

import streamlit as st

from bib_lookup.bib_lookup import BibLookup
from bib_lookup.version import __version__

st.set_page_config(
    page_title="Bib Lookup",
    page_icon=":books:",
    layout="centered",
)


# ignore warnings
warnings.filterwarnings("ignore")


@st.cache_resource
def get_bib_lookuper():
    return BibLookup(verbose=0)


def do_lookup():
    if input_doi == "":
        pass  # do nothing
    else:
        current_arxiv2doi = st.session_state.arxiv2doi if "arxiv2doi" in st.session_state else True
        current_align = st.session_state.align if "align" in st.session_state else "middle"
        current_fmt = st.session_state.fmt if "fmt" in st.session_state else "bibtex"
        current_capitalize_title = st.session_state.capitalize_title if "capitalize_title" in st.session_state else False
        if "history" in st.session_state and st.session_state["history"] != {}:
            if (
                st.session_state["history"]["doi"] == input_doi
                and st.session_state["history"]["arxiv2doi"] == current_arxiv2doi
            ):
                cached_bib = st.session_state["history"]["bib"]
                if isinstance(cached_bib, str) and cached_bib.startswith(BibLookup.__REDIRECT_FLAG__):
                    url = cached_bib.split("visit: ")[-1].strip()
                    output_container.warning("⚠️ This DOI cannot be resolved to BibTeX automatically (ChinaDOI/CNKI).")
                    output_container.link_button("👉 Click to visit Article Page", url)
                    return
                if st.session_state["history"]["fmt"] == current_fmt == "bibtex":
                    bib = str(bl._to_bib_item(cached_bib, align=current_align, capitalize_title=current_capitalize_title))
                    output_container.code(bib, language="latex", line_numbers=False)
                    return
                elif st.session_state["history"]["fmt"] == current_fmt:
                    output_container.code(cached_bib, language="latex", line_numbers=False)
                    return
        try:
            bib = bl(
                input_doi,
                arxiv2doi=current_arxiv2doi,
                format=current_fmt,
                align=current_align,
                capitalize_title=current_capitalize_title,
            )
            # cache into session_state["history"]
            if "history" not in st.session_state:
                st.session_state["history"] = {}
            if input_doi not in st.session_state["history"] and bib not in bl.lookup_errors:
                st.session_state["history"]["doi"] = input_doi
                st.session_state["history"]["fmt"] = current_fmt
                st.session_state["history"]["arxiv2doi"] = current_arxiv2doi
                st.session_state["history"]["bib"] = bib
                st.session_state["history"]["capitalize_title"] = current_capitalize_title
        except Exception as e:
            output_container.error(f"Error: {e}")
        else:
            if bib and bib.startswith(BibLookup.__REDIRECT_FLAG__):
                url = bib.split("visit: ")[-1].strip()
                output_container.warning(
                    "Automatic lookup failed. This appears to be a ChinaDOI/CNKI record that does not support standard BibTeX export."
                )
                output_container.markdown(f"**Redirect URL detected:** `{url}`")
                output_container.link_button("👉 Click to visit Article Page", url)
            elif bib in bl.lookup_errors:
                output_container.error(f"Lookup Failed: {bib}")
            else:
                output_container.code(bib, language="latex", line_numbers=False)

    st.session_state["confirmed_doi"] = False


bl = get_bib_lookuper()


st.title("Bib Lookup 🔍")

# show the version number on the sidebar

st.sidebar.markdown(f"version: {__version__}")

# configurations on the sidebar

st.sidebar.title("Configurations")
# select the style of alignment
align = st.sidebar.selectbox(
    label="Alignment",
    options=["middle", "left", "left-middle"],
    index=0,
    key="align",
    # on_change=do_lookup,
    on_change=lambda: st.session_state.update({"confirmed_doi": True}),
)
# select the format of the output
fmt = st.sidebar.selectbox(
    label="Format",
    options=["bibtex", "text", "rdf-xml", "turtle", "ris", "crossref-xml", "datacite-xml", "crossref-tdm", "bibentry"],
    index=0,
    key="fmt",
    # on_change=do_lookup,
    on_change=lambda: st.session_state.update({"confirmed_doi": True}),
)
# toggle arxiv2doi to be on or off
arxiv2doi = st.sidebar.checkbox(
    label="arXiv ID to DOI",
    value=True,
    key="arxiv2doi",
    # on_change=do_lookup,
    on_change=lambda: st.session_state.update({"confirmed_doi": True}),
)
# toggle capitalize_title to be on or off
capitalize_title = st.sidebar.checkbox(
    label="Capitalize title",
    value=False,
    key="capitalize_title",
    # on_change=do_lookup,
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
    input_doi = st.text_input(
        label="**DOI / PubMed ID / arXiv ID**",
        label_visibility="collapsed",
        value="",
        max_chars=100,
        key="input_doi",
        # help="Enter a DOI, PubMed ID or arXiv ID",
        placeholder="Paste DOI, arXiv ID, or PubMed ID here...",
        on_change=lambda: st.session_state.update({"confirmed_doi": True}),
    )
# a "Search" button to trigger the lookup on the right side of the input box
with col_btn:
    button = st.button(
        label="Search",
        key="button",
        type="primary",
        use_container_width=True,
        # on_click=do_lookup,
        on_click=lambda: st.session_state.update({"confirmed_doi": True}),
    )

# a container for writting output
if st.session_state.get("confirmed_doi", False):
    st.divider()
output_container = st.container()

if st.session_state.get("confirmed_doi", False):
    do_lookup()

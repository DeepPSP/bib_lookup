import warnings

import streamlit as st
from packaging import version

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


bl = get_bib_lookuper()


st.title("Bib Lookup")


# input on the main page

input_doi = st.text_input(
    label="**DOI / PubMed ID / arXiv ID**",
    value="",
    max_chars=100,
    key="input_doi",
)


# a "Search" button to trigger the lookup on the right side of the input box
button = st.button(
    label="Search",
    key="button",
    # on_click=do_lookup,
)

# a container for writting output

output_container = st.container()


def do_lookup():
    if input_doi == "":
        pass  # do nothing
    else:
        current_arxiv2doi = st.session_state.arxiv2doi if "arxiv2doi" in st.session_state else True
        current_align = st.session_state.align if "align" in st.session_state else "middle"
        current_fmt = st.session_state.fmt if "fmt" in st.session_state else "bibtex"
        if "history" in st.session_state and st.session_state["history"] != {}:
            if (
                st.session_state["history"]["doi"] == input_doi
                and st.session_state["history"]["arxiv2doi"] == current_arxiv2doi
            ):
                if st.session_state["history"]["fmt"] == current_fmt == "bibtex":
                    bib = str(bl._to_bib_item(st.session_state["history"]["bib"], align=current_align))
                    output_container.code(bib, language="latex", line_numbers=False)
                    return
                elif st.session_state["history"]["fmt"] == current_fmt:
                    # other formats
                    bib = st.session_state["history"]["bib"]
                    output_container.code(bib, language="latex", line_numbers=False)
                    return
        try:
            bib = bl(
                input_doi,
                arxiv2doi=current_arxiv2doi,
                format=current_fmt,
                align=current_align,
            )
            # cache into session_state["history"]
            if "history" not in st.session_state:
                st.session_state["history"] = {}
            if input_doi not in st.session_state["history"] and bib not in bl.lookup_errors:
                st.session_state["history"]["doi"] = input_doi
                st.session_state["history"]["fmt"] = current_fmt
                st.session_state["history"]["arxiv2doi"] = current_arxiv2doi
                st.session_state["history"]["bib"] = bib
        except Exception as e:
            output_container.error(f"Error: {e}")
        else:
            output_container.code(bib, language="latex", line_numbers=False)


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
    on_change=do_lookup,
)
# toggle arxiv2doi to be on or off
arxiv2doi = st.sidebar.checkbox(
    label="arXiv ID to DOI",
    value=True,
    key="arxiv2doi",
    on_change=do_lookup,
)
# select the format of the output
fmt = st.sidebar.selectbox(
    label="format",
    options=["bibtex", "text", "rdf-xml", "turtle", "ris", "crossref-xml", "datacite-xml", "crossref-tdm", "bibentry"],
    index=0,
    key="fmt",
    on_change=do_lookup,
)
# link to issue tracker on GitHub
for _ in range(7):
    # add some space
    st.sidebar.write("\n")
st.sidebar.markdown("**:red[Report an issue]**")
if version.parse(st.__version__) < version.parse("1.31.0"):
    st.sidebar.markdown(
        '<p style="text-align:center;color:red;"><a href="https://github.com/DeepPSP/bib_lookup/issues" target="_blank">GitHub Issue Tracker</a></p>',
        unsafe_allow_html=True,
    )
    st.sidebar.markdown(
        '<p style="text-align:center;color:red;"><a href="https://gitee.com/deep-psp/bib_lookup/issues" target="_blank">Gitee Issue Tracker</a></p>',
        unsafe_allow_html=True,
    )
else:
    st.sidebar.page_link(
        page="https://github.com/DeepPSP/bib_lookup/issues",
        label=":red[GitHub Issue Tracker]",
        icon="🛠️",
    )
    st.sidebar.page_link(
        page="https://gitee.com/deep-psp/bib_lookup/issues",
        label=":red[Gitee Issue Tracker]",
        icon="🛠️",
    )


if button:
    if input_doi == "":
        output_container.error("DOI cannot be empty")
    else:
        do_lookup()

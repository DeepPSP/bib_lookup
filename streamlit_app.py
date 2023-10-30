import streamlit as st

from bib_lookup.bib_lookup import BibLookup
from bib_lookup.version import __version__

st.set_page_config(
    page_title="Bib Lookup",
    page_icon=":books:",
    layout="centered",
)


@st.cache_resource
def get_bib_lookuper():
    return BibLookup(verbose=0)


bl = get_bib_lookuper()


st.title("Bib Lookup")


# input on the main page

input_doi = st.text_input(
    label="DOI",
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
        # output_container.error("DOI cannot be empty")
        pass  # do nothing
    else:
        current_arxiv2doi = st.session_state.arxiv2doi if "arxiv2doi" in st.session_state else True
        current_align = st.session_state.align if "align" in st.session_state else "middle"
        current_fmt = st.session_state.fmt if "fmt" in st.session_state else "bibtex"
        if "history" in st.session_state:
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
            if input_doi not in st.session_state["history"]:
                st.session_state["history"]["doi"] = input_doi
                st.session_state["history"]["fmt"] = current_fmt
                st.session_state["history"]["arxiv2doi"] = current_arxiv2doi
                st.session_state["history"]["bib"] = bib
        except Exception as e:
            output_container.error(f"Error: {e}")
            # st.error(f"Error: {e}")
        else:
            output_container.code(bib, language="latex", line_numbers=False)
            # st.code(bib, language="latex", line_numbers=False)


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

if button:
    if input_doi == "":
        output_container.error("DOI cannot be empty")
    else:
        do_lookup()
    # if input_doi == "":
    #     st.error("DOI cannot be empty")
    # else:
    #     # output_container = st.empty()
    #     try:
    #         bib = bl(input_doi, arxiv2doi=arxiv2doi, format=fmt, align=align)
    #     except Exception as e:
    #         st.error(f"Error: {e}")
    #     else:
    #         st.code(bib, language="latex", line_numbers=False)

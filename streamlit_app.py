import streamlit as st

from bib_lookup.bib_lookup import BibLookup
from bib_lookup.version import __version__

bl = BibLookup()


st.set_page_config(
    page_title="Bib Lookup",
    page_icon=":books:",
    layout="centered",
)


st.title("Bib Lookup")


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
)
# toggle arxiv2doi to be on or off
arxiv2doi = st.sidebar.checkbox(
    label="arXiv ID to DOI",
    value=True,
    key="arxiv2doi",
)
# select the format of the output
fmt = st.sidebar.selectbox(
    label="format",
    options=["bibtex", "text", "rdf-xml", "turtle", "ris", "crossref-xml", "datacite-xml", "crossref-tdm", "bibentry"],
    index=0,
    key="fmt",
)


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
)

if button:
    if input_doi == "":
        st.error("DOI cannot be empty")
    else:
        # output_container = st.empty()
        try:
            bib = bl(input_doi, arxiv2doi=arxiv2doi, format=fmt, align=align)
        except Exception as e:
            st.error(f"Error: {e}")
        else:
            st.code(bib, language="latex", line_numbers=False)
            # write the output to a text area
            # st.text_area(
            #     label="Bib",
            #     value=bib,
            #     height=27 * len(bib.split("\n")),
            #     max_chars=100000,
            #     key="output",
            # )

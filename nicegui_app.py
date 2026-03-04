import argparse
import warnings

from nicegui import ui

from bib_lookup.bib_lookup import BibLookup
from bib_lookup.version import __version__

# Filter warnings
warnings.filterwarnings("ignore")

# Initialize BibLookup
bl = BibLookup(verbose=0, print_result=False)


# State
class State:
    def __init__(self):
        self.result_text = ""
        self.result_type = "none"  # none, success, error, warning


state = State()


def perform_lookup(is_auto: bool = False):
    """Perform the lookup and update the UI."""
    query = doi_input.value.strip()

    if not query:
        if not is_auto:
            ui.notify("Please enter a DOI, arXiv ID, or PubMed ID.", type="warning")
        return

    # Update UI to searching state
    search_btn.disable()
    if not is_auto:
        search_btn_text.text = "Searching..."
    result_container.clear()

    # Get configuration values
    current_fmt = format_select.value
    current_align = align_select.value
    current_arxiv2doi = arxiv_toggle.value
    current_capitalize_title = cap_toggle.value

    def run_lookup():
        try:
            # Perform lookup
            bib = bl(
                query,
                arxiv2doi=current_arxiv2doi,
                format=current_fmt,
                align=current_align,
                capitalize_title=current_capitalize_title,
                print_result=False,
            )

            # Handle Redirect / HTML response
            if isinstance(bib, str) and bib.startswith(BibLookup.__REDIRECT_FLAG__):
                url = bib.split("visit: ")[-1].strip()
                show_result(url, "warning")
                return

            # Handle Lookup Errors
            if bib in bl.lookup_errors:
                show_result(f"Lookup Failed: {bib}", "error")
                return

            # Success
            show_result(str(bib), "success")

        except Exception as e:
            show_result(f"Error: {str(e)}", "error")
            import traceback

            traceback.print_exc()
        finally:
            reset_search_btn()

    # Run in background to not block UI
    ui.timer(0.1, run_lookup, once=True)


def reset_search_btn():
    search_btn.enable()
    search_btn_text.text = "Search"


def show_result(text: str, type: str):
    state.result_text = text
    state.result_type = type

    result_container.clear()
    with result_container:
        if type == "success":
            # Result Card
            with ui.card().classes("w-full glass-card p-6 mt-4 relative"):
                # Copy button at top right (Absolute positioned)
                ui.button(icon="content_copy", on_click=copy_to_clipboard).props("flat round dense color=grey").classes(
                    "absolute top-2 right-2"
                ).tooltip("Copy to clipboard")

                # Code display
                ui.html(f'<pre class="whitespace-pre-wrap font-mono text-sm text-gray-800">{text}</pre>').classes(
                    "w-full overflow-x-auto"
                )

        elif type == "error":
            with ui.card().classes("w-full bg-red-50 border border-red-200 p-4 mt-4"):
                with ui.row().classes("items-center gap-2"):
                    ui.icon("error", color="red").classes("text-xl")
                    ui.label(text).classes("text-red-700 font-medium")

        elif type == "warning":
            with ui.card().classes("w-full bg-orange-50 border border-orange-200 p-4 mt-4"):
                with ui.column().classes("gap-2"):
                    with ui.row().classes("items-center gap-2"):
                        ui.icon("warning", color="orange").classes("text-xl")
                        ui.label("Automatic lookup failed. This appears to be a ChinaDOI/CNKI record.").classes(
                            "text-orange-800 font-medium"
                        )

                    if text.startswith("http"):
                        ui.link("👉 Click to visit Article Page", text).classes("text-blue-600 font-bold hover:underline")
                    else:
                        ui.label(text).classes("text-orange-800")


def copy_to_clipboard():
    ui.clipboard.write(state.result_text)
    ui.notify("Copied to clipboard!", type="positive", icon="check")


# --- UI Setup ---

# Add custom font and styles
ui.add_head_html("""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
body {
    font-family: 'Inter', sans-serif;
    background-color: #f3f4f6;
    background-image: radial-gradient(#e5e7eb 1px, transparent 1px);
    background-size: 20px 20px;
}
.glass-card {
    background: rgba(255, 255, 255, 0.75);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.8);
    box-shadow: 0 4px 30px rgba(0, 0, 0, 0.05);
}
.sidebar-glass {
    background: rgba(255, 255, 255, 0.9) !important;
    backdrop-filter: blur(10px);
}
</style>
""")

# Sidebar (Replicating Streamlit Sidebar)
with ui.left_drawer(value=True).classes("sidebar-glass border-r border-gray-200 p-6") as drawer:
    ui.label(f"version: {__version__}").classes("text-gray-500 text-xs mb-6")

    ui.label("Configurations").classes("text-xl font-bold text-gray-800 mb-4")

    # Alignment
    ui.label("Alignment").classes("text-sm font-medium text-gray-700 mb-1")
    align_options = ["middle", "left", "left-middle"]
    align_select = (
        ui.select(align_options, value="middle", on_change=lambda e: perform_lookup(is_auto=True))
        .classes("w-full mb-4")
        .props("dense outlined options-dense")
    )

    # Format
    ui.label("Format").classes("text-sm font-medium text-gray-700 mb-1")
    format_options = ["bibtex", "text", "ris", "rdf-xml", "turtle", "crossref-xml", "datacite-xml", "crossref-tdm", "bibentry"]
    format_select = (
        ui.select(format_options, value="bibtex", on_change=lambda e: perform_lookup(is_auto=True))
        .classes("w-full mb-4")
        .props("dense outlined options-dense")
    )

    # Toggles
    arxiv_toggle = ui.checkbox("arXiv ID to DOI", value=True, on_change=lambda e: perform_lookup(is_auto=True)).classes(
        "text-sm text-gray-800 mb-2"
    )
    cap_toggle = ui.checkbox("Capitalize title", value=False, on_change=lambda e: perform_lookup(is_auto=True)).classes(
        "text-sm text-gray-800 mb-6"
    )

    ui.separator().classes("mb-6")

    # Links
    ui.label("🛠️ Report an issue").classes("text-sm font-bold text-red-600 mb-2")
    with ui.row().classes("w-full gap-2"):
        ui.button(
            "GitHub", on_click=lambda: ui.navigate.to("https://github.com/DeepPSP/bib_lookup/issues", new_tab=True)
        ).props("outline dense size=sm").classes("flex-grow")
        ui.button("Gitee", on_click=lambda: ui.navigate.to("https://gitee.com/deep-psp/bib_lookup/issues", new_tab=True)).props(
            "outline dense size=sm"
        ).classes("flex-grow")

# Main Content
with ui.column().classes("w-full max-w-4xl mx-auto p-4 md:p-8 items-stretch"):

    # Header Row
    with ui.row().classes("w-full items-center gap-4 mb-8"):
        ui.button(icon="menu", on_click=lambda: drawer.toggle()).props("flat round color=grey-800")
        ui.label("Bib Lookup 🔍").classes("text-4xl font-bold text-gray-800")

    # Input Row (Streamlit-like layout: Input [4] + Button [1])
    with ui.row().classes("w-full items-stretch gap-4 mb-8 no-wrap"):
        # Input Wrapper
        with ui.element("div").classes(
            "flex-grow glass-card rounded-xl px-4 flex items-center transition-all focus-within:ring-2 focus-within:ring-blue-400"
        ):
            # borderless removes the underline; dense reduces padding; we control height via parent flex/padding
            doi_input = (
                ui.input(placeholder="Paste DOI, arXiv ID, or PubMed ID...")
                .classes("w-full text-lg")
                .props('borderless input-class="text-gray-800"')
                .on("keydown.enter", lambda: perform_lookup(is_auto=False))
            )

        # Search Button
        # h-14 is 3.5rem (56px).
        search_btn = ui.button(on_click=lambda: perform_lookup(is_auto=False)).classes(
            "h-14 px-8 rounded-xl font-bold shadow-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors"
        )
        with search_btn:
            search_btn_text = ui.label("Search")

    # Result Area
    result_container = ui.column().classes("w-full")


if __name__ in {"__main__", "__mp_main__"}:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8080, help="Port to run the server on")
    args, unknown = parser.parse_known_args()

    ui.run(title="Bib Lookup", favicon="📚", port=args.port)

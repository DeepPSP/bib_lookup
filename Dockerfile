# No `# syntax=` directive on purpose: the BuildKit frontend bundled with
# recent docker already supports the cache mounts below, so the build needs
# no network access beyond the (locally cached) base image.

# --- builder stage: resolve and install the Python dependency set ----------
FROM python:3.12-slim AS builder

# hatch-vcs cannot infer a version without .git (the build context never
# includes it); pass SETUPTOOLS_SCM_PRETEND_VERSION=<tag> to pin one
ARG SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0
ENV SETUPTOOLS_SCM_PRETEND_VERSION=${SETUPTOOLS_SCM_PRETEND_VERSION}

# an isolated venv is the modern packaging unit: the runtime stage copies it
# wholesale and stays free of pip/setuptools and build tooling
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /build
COPY pyproject.toml README.md LICENSE ./
COPY bib_lookup/ ./bib_lookup/

# cache mount: pip downloads survive between builds instead of being thrown
# away (the old --no-cache-dir habit) — same image, much faster rebuilds.
# The app lives in the `app` extra (streamlit), not the base dependencies.
RUN --mount=type=cache,target=/root/.cache/pip \
    python -m pip install '.[app]'

# --- runtime stage ----------------------------------------------------------
FROM python:3.12-slim

LABEL org.opencontainers.image.title="bib-lookup web app" \
      org.opencontainers.image.description="Streamlit single-page app for looking up BibTeX entries by DOI / PubMed ID / arXiv ID" \
      org.opencontainers.image.source="https://github.com/DeepPSP/bib_lookup" \
      org.opencontainers.image.licenses="MIT"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8501 \
    BASE_URL_PATH=/app/bib-lookup

# bring in only the finished venv — no compilers, no pip, smaller image
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app
COPY streamlit_app.py ./

# unprivileged runtime user; uid 1000 keeps host-mounted volumes simple.
# ~/.cache/bib-lookup (BibLookup's cache dir) lives here.
RUN useradd --create-home --uid 1000 appuser
USER appuser

EXPOSE 8501

# docker compose honors this and marks the container healthy/unhealthy
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8501/app/bib-lookup/_stcore/health', timeout=4)"]

# sh -c is needed for ${PORT}/${BASE_URL_PATH} interpolation; `exec` hands the
# PID to streamlit so SIGTERM (docker stop) reaches it directly
CMD ["sh", "-c", "exec streamlit run streamlit_app.py --server.address 0.0.0.0 --server.port ${PORT} --server.headless true --server.baseUrlPath ${BASE_URL_PATH}"]

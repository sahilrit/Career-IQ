# CareerOS — self-hosted image. Zero paid services required: this runs
# the full platform (CLI + Dashboard) against local SQLite storage.
# See docs/development/self-hosted.md.

FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app
COPY . .

RUN uv sync --all-packages --frozen
RUN uv run playwright install --with-deps chromium
RUN rm -rf /var/lib/apt/lists/*

ENV CAREEROS_DATA_DIR=/data
VOLUME ["/data"]

EXPOSE 8501

CMD ["uv", "run", "streamlit", "run", "packages/careeros-dashboard/src/careeros_dashboard/app.py", "--server.address=0.0.0.0"]

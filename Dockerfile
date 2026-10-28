FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.13.1 /uv /usr/local/bin/uv

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src/ ./src/

RUN uv pip install --system --no-cache . \
    && useradd --uid 1000 --create-home --home-dir /home/garmin --shell /usr/sbin/nologin garmin \
    && install -d -o garmin -g garmin /home/garmin/.config/garmin /home/garmin/Downloads/garmin

ENV HOME=/home/garmin \
    GARMIN_MCP_DOWNLOAD_DIR=/home/garmin/Downloads/garmin
USER garmin

ENTRYPOINT ["garmin-personal-mcp"]

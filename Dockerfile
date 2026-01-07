FROM python:3.13.7-bookworm AS builder
RUN apt-get update && apt-get install --no-install-recommends -y \
        build-essential && \
    apt-get clean && rm -rf /var/lib/apt/lists/*
ADD https://astral.sh/uv/install.sh /install.sh
RUN chmod -R 655 /install.sh && /install.sh && rm /install.sh
ENV PATH="/root/.local/bin:$PATH"
WORKDIR /app
COPY ./pyproject.toml .
RUN uv sync



FROM python:3.13.7-bookworm AS production
WORKDIR /app
COPY . . 
COPY --from=builder /app/.venv .venv
ENV PATH="/app/.venv/bin:$PATH"
# CMD ["python", "-m", "src.telegram.telegram"]
CMD ["sh", "-c", "python -m src.database.database && python -m src.telegram.telegram"]

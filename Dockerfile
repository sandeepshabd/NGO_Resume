FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

WORKDIR /app

COPY pyproject.toml README.md ./
COPY packages ./packages
COPY agents ./agents

RUN pip install --no-cache-dir .

RUN useradd --create-home --shell /usr/sbin/nologin appuser
USER appuser

CMD ["sh", "-c", "uvicorn ${AGENT_MODULE}:app --host 0.0.0.0 --port ${PORT}"]

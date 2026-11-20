FROM python:3.12-slim
RUN pip install --no-cache-dir uv
WORKDIR /app
COPY pyproject.toml uv.lock* ./
COPY contracts/ contracts/
COPY pipeline/ pipeline/
RUN uv sync --no-dev --package callmate-pipeline
EXPOSE 8000
# --no-sync: the image already has the right environment from `uv sync --no-dev` above;
#   without this, `uv run` re-syncs against the full workspace lockfile at every container
#   start, pulling dev-only tools (ruff, mypy, pytest) that have no business in production.
# --proxy-headers --forwarded-allow-ips='*': trust X-Forwarded-Proto from Fly's edge proxy —
#   without it, uvicorn thinks every request is plain http, and the Twilio signature check in
#   twilio_webhooks.py (which signs the real https:// URL) fails with a 403 on every webhook.
CMD ["uv", "run", "--no-sync", "uvicorn", "callmate_pipeline.main:app", "--host", "0.0.0.0", \
     "--port", "8000", "--proxy-headers", "--forwarded-allow-ips=*"]

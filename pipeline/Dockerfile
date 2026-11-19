FROM python:3.12-slim
RUN pip install --no-cache-dir uv
WORKDIR /app
COPY pyproject.toml uv.lock* ./
COPY contracts/ contracts/
COPY pipeline/ pipeline/
RUN uv sync --no-dev --package callmate-pipeline
EXPOSE 8000
CMD ["uv", "run", "uvicorn", "callmate_pipeline.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM python:3.12-slim
RUN pip install --no-cache-dir uv
WORKDIR /app
COPY pyproject.toml uv.lock* ./
COPY contracts/ contracts/
COPY brain/ brain/
RUN uv sync --no-dev --package callmate-brain
EXPOSE 8001
CMD ["uv", "run", "uvicorn", "callmate_brain.main:app", "--host", "0.0.0.0", "--port", "8001"]

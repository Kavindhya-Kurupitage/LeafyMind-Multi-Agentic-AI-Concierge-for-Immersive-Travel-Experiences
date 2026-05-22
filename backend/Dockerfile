FROM python:3.11-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system appuser \
    && useradd --system --gid appuser --home-dir /app --no-create-home appuser

COPY requirements.txt .
# Slow/unstable links to PyPI often hit the default 15s read timeout and fail with
# "No matching distribution found" even though the package exists.
RUN pip install --upgrade pip \
    && pip install --no-cache-dir --default-timeout=300 --retries 10 -r requirements.txt

COPY . .
RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# Default without --reload (docker-compose overrides if needed). Reload breaks BFF login during restarts.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONUTF8=1 MPLCONFIGDIR=/tmp/matplotlib CREDIT_DB_PATH=/app/runtime/credit.sqlite3
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY api/ api/
COPY src/ src/
COPY app/ app/
COPY models/ models/
COPY reports/artifact_manifest.json reports/artifact_manifest.json
RUN useradd -m -u 1001 appuser && mkdir -p /app/runtime /app/logs && chown appuser:appuser /app/runtime /app/logs && chmod -R a-w /app/models
USER appuser
EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-server-header"]

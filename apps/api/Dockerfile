FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY packages /app/packages
COPY apps/api /app/apps/api

RUN pip install --no-cache-dir /app/packages/quant_core /app/packages/quant_adapters /app/apps/api

EXPOSE 8000

CMD ["fastapi", "run", "apps/api/src/quantresearch_api/main.py", "--host", "0.0.0.0", "--port", "8000"]

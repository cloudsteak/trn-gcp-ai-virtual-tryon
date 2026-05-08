FROM python:3.12-slim AS builder

RUN pip install uv

WORKDIR /app

COPY pyproject.toml .
RUN uv pip install --system --no-cache -r pyproject.toml

COPY src/ src/

FROM python:3.12-slim

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app/src src/

ENV PYTHONPATH=/app/src

EXPOSE 8080

CMD ["uvicorn", "virtual_tryon.main:app", "--host", "0.0.0.0", "--port", "8080"]

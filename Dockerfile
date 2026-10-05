FROM python:3.12-slim

RUN groupadd -r appgroup && useradd -r -g appgroup appuser

WORKDIR /app

COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r /app/requirements.txt

COPY ai-consumer.py /app/ai-consumer.py

RUN chown -R appuser:appgroup /app

USER appuser

ENTRYPOINT ["python3", "/app/ai-consumer.py"]
CMD []

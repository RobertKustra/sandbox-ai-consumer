FROM python:3.12-slim

WORKDIR /app

COPY ai-consumer.py /app/ai-consumer.py

ENTRYPOINT ["python3", "/app/ai-consumer.py"]
CMD []

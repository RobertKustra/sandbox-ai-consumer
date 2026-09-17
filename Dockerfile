FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY ai-consumer.py /app/ai-consumer.py

ENTRYPOINT ["python3", "/app/ai-consumer.py"]
CMD []

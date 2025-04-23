FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN apt-get update && apt-get install -y git netcat-openbsd && \
    git clone https://github.com/modelcontextprotocol/python-sdk.git /tmp/python-sdk && \
    pip install /tmp/python-sdk && \
    pip install --no-cache-dir -r requirements.txt && \
    rm -rf /tmp/python-sdk

COPY . .

RUN chmod +x /app/wait-for-postgres.sh

CMD ["./wait-for-postgres.sh", "uvicorn", "server:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "3333"]

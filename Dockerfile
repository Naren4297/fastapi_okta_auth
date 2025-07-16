# Dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY . .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

ENV PYTHONPATH=/app

CMD ["uvicorn", "fastapi_app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

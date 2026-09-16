FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-chi-sim \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.runtime.txt ./requirements.runtime.txt
COPY constraints.txt ./constraints.txt
RUN pip install --no-cache-dir -r requirements.runtime.txt -c constraints.txt

COPY app ./app
COPY scripts ./scripts
COPY streamlit_app.py ./streamlit_app.py
COPY data ./data
COPY documents ./documents

EXPOSE 9000 8502

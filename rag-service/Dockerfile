# Image for both the RAG API (default command) and the Streamlit UI (see docker-compose.yml)
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY streamlit_app ./streamlit_app

EXPOSE 8000 8501
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]

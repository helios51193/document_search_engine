FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1

CMD ["python","manage.py","makemigrations","&","gunicorn", "document_search_engine.wsgi:application", "-b", "0.0.0.0:8000"]
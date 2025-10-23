# Production-grade Django Dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

# Collect static files (if any)
RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "securefiles.wsgi:application", "--bind", "0.0.0.0:8000", "--workers=3", "--timeout", "120", "--log-level", "debug", "--access-logfile", "-", "--error-logfile", "-"]

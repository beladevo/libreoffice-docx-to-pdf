FROM python:3.11-slim-bookworm

RUN apt-get update && \
    apt-get -y install --no-install-recommends libreoffice curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
WORKDIR /usr/src/app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --retries=3 CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

ENV ENVIRONMENT=production
ENV LOG_FILE=app.log
ENV TIME_LOG_FILE=conversion_time.log

CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-8000} run:app"]

FROM python:3.9-slim-buster

RUN apt-get update && \
    apt-get -y install libreoffice && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
WORKDIR /usr/src/app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=10s --retries=3 CMD curl -f http://localhost:5000/health || exit 1

ENV ENVIRONMENT=production
ENV LOG_FILE=app.log
ENV TIME_LOG_FILE=conversion_time.log


RUN soffice --headless --invisible --nologo --nolockcheck --nodefault --nofirststartwizard &

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "run:app"]

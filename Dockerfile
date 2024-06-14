FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV TEMP_DIR=/home/temp

RUN apt-get update && \
    apt-get -y upgrade && \
    apt-get -y install python3.10 python3-pip libreoffice libreoffice-java-common curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/app

RUN mkdir -p /home/temp

COPY . .

RUN pip3 install --no-cache-dir -r requirements.txt

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=10s --retries=3 CMD curl -f http://localhost:5000/health || exit 1

CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]

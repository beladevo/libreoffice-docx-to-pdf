FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV TEMP_DIR=/home/temp
ENV FLASK_ENV=development

RUN apt-get update && \
    apt-get -y upgrade && \
    apt-get -y install python3.10 python3-pip libreoffice libreoffice-java-common curl openssh-server && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /run/sshd && \
    echo 'root:Docker!' | chpasswd && \
    sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config && \
    sed -i 's/Port 22/Port 2222/' /etc/ssh/sshd_config

WORKDIR /usr/src/app

RUN mkdir -p /home/temp

COPY . .

RUN pip3 install --no-cache-dir -r requirements.txt

EXPOSE 5000 2222

HEALTHCHECK --interval=30s --timeout=10s --retries=3 CMD curl -f http://localhost:5000/health || exit 1

CMD service ssh start && flask run --host=0.0.0.0 --port=5000

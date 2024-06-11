FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Update and install necessary packages
RUN apt-get update && \
    apt-get -y upgrade && \
    apt-get -y install python3.10 python3-pip libreoffice libreoffice-java-common && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /usr/src/app

# Copy the current directory contents into the container at /usr/src/app
COPY . .

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Run the application
CMD ["flask", "run", "--host=0.0.0.0"]

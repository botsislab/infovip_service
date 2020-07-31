# Base image
# FROM ubuntu:18.10
FROM python:3.7.2

# Install python and uwsgi
RUN apt-get update
# RUN apt-get install -y python3 python3-dev python3-pip nginx
RUN apt-get install -y nginx
RUN pip3 install uwsgi

WORKDIR /app

# Copy and install requirements
COPY requirements.txt .
RUN pip3 install -r requirements.txt

# Copy our app into the image
COPY . .

# Setup and start nginx
COPY ./nginx.conf /etc/nginx/sites-enabled/default
CMD service nginx start && uwsgi -s /tmp/uwsgi.sock --chmod-socket=666 --manage-script-name --mount /=api:app

# docker run -p 5000:80 --network=infovip --name infovip-service infovip-service
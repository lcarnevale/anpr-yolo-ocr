FROM python:3.8-slim
LABEL maintainer="Lorenzo Carnevale <lcarnevale@unime.it>" \
      name="Plate Detection Api Gateway Microservice" \
      description="Docker container for running a plate detection microservice" \
    #   url="https://hub.docker.com/r/petronetto/pytorch-alpine" \
    #   vcs-url="https://github.com/petronetto/pytorch-alpine" \
      vendor="University of Messina" \
      version="1.0"

RUN echo "|--> Updating"; \
    apt update -y && apt upgrade -y;

COPY requirements.txt /opt/app/requirements.txt

WORKDIR /opt/app

RUN echo "|--> Installing dependencies"; \
    apt-get install -y libgl1 libglib2.0-0; \
    apt-get install -y software-properties-common; \
    add-apt-repository -y ppa:alex-p/tesseract-ocr; \
    apt-get update -y; \
    apt-get install -y tesseract-ocr; \
    pip install -r requirements.txt;
    
COPY app /opt/app

FROM ubuntu:latest

LABEL maintainer="Lorenzo Carnevale <lcarnevale@unime.it>" \
      name="Plate Detection Microservice" \
      description="Docker container for running a plate detection microservice" \
      vendor="University of Messina" \
      version="1.0"

# Aggiornamento e installazione di software-properties-common
RUN echo "|--> Updating"; \
    apt update -y && apt upgrade -y && \
    apt install -y software-properties-common

# Aggiunta del repository deadsnakes PPA per Python 3.10
RUN add-apt-repository ppa:deadsnakes/ppa && apt update -y

# Installazione di Python 3.10, pip e venv
RUN apt install -y python3.10 python3-pip python3.10-venv

# Creazione di un ambiente virtuale e aggiornamento di pip
RUN python3.10 -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip

# Copia del file requirements.txt
COPY requirements.txt /opt/app/requirements.txt

# Impostazione della directory di lavoro
WORKDIR /opt/app

# Installazione delle dipendenze di sistema e dei pacchetti Python
RUN echo "|--> Install dependencies"; \
    apt install -y libgl1 libglib2.0-0 && \
    /opt/venv/bin/pip install -r requirements.txt

# Copia dell'applicazione
COPY app /opt/app

# Impostazione dell'ambiente PATH per utilizzare l'ambiente virtuale
ENV PATH="/opt/venv/bin:$PATH"

# Esposizione della porta 8080
EXPOSE 8080

# Comando di avvio dell'applicazione
CMD ["python3", "main.py", "-c", "config.yaml", "-v"]

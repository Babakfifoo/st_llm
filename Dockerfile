# app/Dockerfile
FROM python:3.12.8-slim

WORKDIR /

# Install build essentials and other necessary tools
RUN apt-get update 
RUN apt-get install build-essential -y
RUN apt-get install curl -y
RUN apt-get install software-properties-common -y
RUN apt-get install git  -y

RUN apt-get clean && rm -rf /var/lib/apt/lists/*
# Copy the entire app folder
COPY . .

# Copy requirements.txt
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "./app/streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]

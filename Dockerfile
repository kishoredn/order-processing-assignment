FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Install minimal build deps for wheels that may need compilation
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential gcc libffi-dev curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install requirements
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the app
COPY . /app

EXPOSE 8000

# Default command is to run the web app. Override in docker-compose for worker.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

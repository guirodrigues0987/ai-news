# Lightweight base image - just the essentials of Python
FROM python:3.12-slim

# Avoid writing .pyc files and force unbuffered output (real-time logs on k3s)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copy only requirements first to leverage Docker layer caching:
# if the code changes but the dependencies do not, this layer is not rebuilt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the rest of the code
COPY . .

# Directory where the final podcast is saved - on k3s this becomes a mounted
# volume, so the file survives after the CronJob container exits
RUN mkdir -p /app/output

# Default command: run the full pipeline (collect -> script -> audio -> email)
CMD ["python", "main.py"]

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies if needed (e.g. for sqlite)
# RUN apt-get update && apt-get install -y ...

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Ensure the data directory is writable by any user (required for HF Spaces)
RUN mkdir -p /app/data && chmod -R 777 /app/data

# Expose the port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM python:3.11-slim

# 1. Create a user with UID 1000 (required by Hugging Face Spaces)
RUN useradd -m -u 1000 user

# 2. Switch to the new user
USER user

# 3. Set environment variables
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# 4. Set working directory to a location writable by the user
WORKDIR $HOME/app

# 5. Copy requirements first to leverage Docker cache
# Note: usage of --chown=user is crucial
COPY --chown=user ./requirements.txt $HOME/app/requirements.txt

# 6. Install dependencies
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# 7. Copy the rest of the application code
COPY --chown=user . $HOME/app

# Expose the port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

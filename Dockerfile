# --- Stage 1: Build the application ---
FROM python:3.11-slim as builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create a project directory that will contain our 'app' package
WORKDIR /project_code

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire 'app' directory into the project directory
# This creates the structure /project_code/app/main.py
COPY ./app ./app

# Copy test directory
COPY ./tests ./tests


# --- Stage 2: Create the final production image ---
FROM python:3.11-slim

# Set the project directory as the working directory
WORKDIR /project_code

# Create a non-root user for security
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

# Copy installed dependencies and application code from the builder stage
COPY --from=builder /project_code /project_code
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Change ownership of the code to the non-root user
RUN chown -R appuser:appgroup /project_code
USER appuser

# Expose the port
EXPOSE 8000

# CORRECT CMD: Run from the parent directory (/project_code),
# telling Gunicorn to load the 'app' object from the 'main' module
# within the 'app' package.
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000", "app.main:app"]
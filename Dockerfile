# Use official Python slim image
FROM python:3.11-slim

WORKDIR /app

# copy requirements and install
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# copy app files
COPY . /app/

# expose port
EXPOSE 8000

# parse data into sqlite db at container startup, then run uvicorn
CMD ["sh", "-c", "python parse_and_load.py && uvicorn main:app --host 0.0.0.0 --port 8000"]

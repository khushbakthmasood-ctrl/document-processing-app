FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

ENV DATABASE_PATH=/app/data/jobs.sqlite
ENV UPLOAD_FOLDER=/app/data/uploads
RUN mkdir -p /app/data/uploads

EXPOSE 5000
CMD ["python", "run.py"]

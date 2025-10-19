FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright and browsers
RUN apt-get update && apt-get install -y --no-install-recommends wget gnupg curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Playwright dependencies and browsers
RUN pip install playwright && playwright install --with-deps

COPY . /app

# Expose port
EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

FROM python:3.12-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends     curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create data directory for SQLite
RUN mkdir -p /app/data

# Fix PYTHONPATH so imports work
ENV PYTHONPATH=/app

EXPOSE 8501
CMD ["sh", "-c", "exec streamlit run ui/app.py --server.port=${PORT:-8501} --server.address=0.0.0.0 --server.headless=true"]

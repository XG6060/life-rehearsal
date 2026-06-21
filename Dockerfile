FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Render assigns PORT env var
CMD streamlit run ui/app.py --server.port=${PORT:-8501} --server.address=0.0.0.0

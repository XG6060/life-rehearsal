FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Render assigns PORT env var, default 8501
CMD exec streamlit run ui/app.py --server.port=$PORT --server.address=0.0.0.0

FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p /app/data
ENV PYTHONPATH=/app
EXPOSE 8501
CMD streamlit run ui/app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true

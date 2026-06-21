FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p /app/data && chmod 777 /app/data
ENV PYTHONPATH=/app HOME=/app
ENV PORT=8080
EXPOSE 8080
CMD streamlit run ui/app.py --server.port=8080 --server.address=0.0.0.0 --server.headless=true

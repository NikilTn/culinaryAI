# backend/Dockerfile

# 1) Use your exact Python version
FROM python:3.11.9-slim

# 2) Set working dir
WORKDIR /app

# 3) Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4) Copy your application code
COPY . .

# 5) Expose Flask’s port
EXPOSE 5000

# 6) Run your Flask app (swap out module:path if needed)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5000", "--reload"]


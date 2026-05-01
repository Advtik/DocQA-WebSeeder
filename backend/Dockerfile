# 1. Base image
FROM python:3.11-slim

# 2. Set working directory
WORKDIR /app

# 3. Copy requirements
COPY requirements.txt .

# 4. Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy project code
COPY . .

# 6. Expose port
EXPOSE 8000

# 7. Run server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]


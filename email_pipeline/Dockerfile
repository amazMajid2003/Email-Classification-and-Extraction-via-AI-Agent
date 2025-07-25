# 1. Start with a clean Python base image
FROM python:3.11-slim

# 2. Set the working directory
WORKDIR /app

# 3. Copy requirements.txt into container
COPY requirements.txt .

# 4. Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy entire codebase into container
COPY . .

# 6. Run the pipeline
CMD ["python", "main.py"]

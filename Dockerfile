FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "-c", "import numpy; import scipy; import matplotlib; print('All imports OK')"]

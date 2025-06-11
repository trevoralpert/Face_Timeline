# Use official Python 3.8 image
FROM python:3.8-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y gcc g++ libjpeg-dev zlib1g-dev libgl1-mesa-glx && \
    rm -rf /var/lib/apt/lists/*

# Install libheif for HEIC support
RUN apt-get update && \
    apt-get install -y libheif-dev && \
    rm -rf /var/lib/apt/lists/*

# Install pip requirements
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . /app/

# Expose Streamlit port
EXPOSE 8501

# Run Streamlit app
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
# 1. Use Python 3.11
FROM python:3.11-slim

# 2. Install Graphics Drivers, CPU Software Rasterizers, and Xvfb
RUN apt-get update && apt-get install -y \
    libgl1 \
    libgl-dev \
    libglx-mesa0 \
    libgl1-mesa-dri \
    libglib2.0-0 \
    build-essential \
    libx11-dev \
    libxcursor-dev \
    libxrandr-dev \
    libxinerama-dev \
    libxi-dev \
    git \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .

# 3. Install Python packages
RUN pip install --default-timeout=1000 --no-cache-dir -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu

COPY . .

# 4. Force fake monitor AND force the CPU to act as a graphics card
ENV PYTHONUNBUFFERED=1
ENV DISPLAY=:99
ENV LIBGL_ALWAYS_SOFTWARE=1
ENV GALLIUM_DRIVER=llvmpipe

EXPOSE 8001

# 5. Boot monitor, wait 2 seconds, run Uvicorn
CMD ["/bin/bash", "-c", "Xvfb :99 -screen 0 1024x768x24 -nolisten tcp & sleep 2 && uvicorn engine_api:app --host 0.0.0.0 --port 8001"]
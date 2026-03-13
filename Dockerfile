# 1. Use an official, stable Python 3.10 Linux image
FROM python:3.10-slim

# 2. Install critical system-level graphics drivers for OpenCV and Depthflow
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 3. Set the working directory inside the container
WORKDIR /app

# 4. Copy the requirements file first (this makes rebuilding much faster)
COPY requirements.txt .

# 5. Install the Python packages
# Note: We force the CPU-only version of PyTorch here to keep the file size smaller,
# assuming you are deploying to a standard CPU cloud droplet first.
RUN pip install --no-cache-dir -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu

# 6. Copy the rest of your engine code into the container
COPY . .

# 7. Expose Port 8001 so the outside world (your Main Backend) can reach it
EXPOSE 8001

# 8. The command to start the engine when the container boots up
CMD ["uvicorn", "engine_api:app", "--host", "0.0.0.0", "--port", "8001"]
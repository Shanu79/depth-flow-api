import modal
import subprocess
import os

# 1. Define the Cloud Container Environment
# modal_app.py
depthflow_image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install(
        "libgl1", "libgl-dev", "libglx-mesa0", "libgl1-mesa-dri", 
        "libglib2.0-0", "build-essential", "xvfb", "ffmpeg"
    )
    .pip_install(
        "fastapi==0.115.14", "uvicorn==0.41.0", "python-multipart==0.0.22", 
        "pydantic==2.11.10", "torch", "torchvision", "transformers", 
        "opencv-python-headless", "numpy", "Pillow==11.3.0", "depthflow==0.9.1"
    )
    .run_commands(
        "python -c \"from transformers import pipeline; pipeline('depth-estimation', model='depth-anything/Depth-Anything-V2-Small-hf')\""
    )
    # --- ADD THIS MISSING BLOCK ---
    .env({
        "NVIDIA_DRIVER_CAPABILITIES": "all",
        "__NV_PRIME_RENDER_OFFLOAD": "1",
        "__GLX_VENDOR_LIBRARY_NAME": "nvidia",
    })
    # ------------------------------
    .add_local_dir(".", remote_path="/root", ignore=[".venv", "__pycache__", ".git", "temp_processing"])
)

app = modal.App("depthflow-engine")

# 2. Provision the Infrastructure
@app.function(
    image=depthflow_image,
    gpu="T4", 
    timeout=300
)
@modal.asgi_app()
def serve_engine():
    # Boot the headless virtual monitor in the background
    subprocess.Popen(["Xvfb", ":99", "-screen", "0", "1920x1080x24", "-ac", "-nolisten", "tcp"])
    os.environ["DISPLAY"] = ":99"
    
    # Import and run your FastAPI app
    from engine_api import app as fastapi_app
    return fastapi_app
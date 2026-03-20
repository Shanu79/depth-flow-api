import os
os.environ["DISPLAY"] = ":99"

import uuid
import json
import io
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, Header, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from PIL import Image

from core.depth_model import get_depth_map
from core.renderer import DepthflowEngine

# ---------------------------------------------------------
# 1. SECURITY CONFIGURATION
# ---------------------------------------------------------
ENGINE_SECRET_KEY = os.getenv("ENGINE_SECRET_KEY", "your-super-secret-internal-key")

app = FastAPI(title="DepthFlow Render Engine Microservice")

# Temp storage for processing
TEMP_DIR = Path("temp_processing")
TEMP_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------
# 2. PYDANTIC SCHEMAS (Strict Payload Validation)
# ---------------------------------------------------------
class RenderSettings(BaseModel):
    duration: int = Field(8, gt=0)              
    fps: int = Field(24, ge=1)                  
    quality: int = Field(80, ge=1, le=100)      
    ssaa: float = Field(1.0, ge=0.0, le=4.0)    
    tiling_mode: str = Field("mirror")
    edge_fix: int = Field(10, ge=0, le=50)      
    invert_depth: float = Field(0.0, ge=0.0, le=1.0)

class MotionSettings(BaseModel):
    style: str = Field("orbit", description="orbit, dolly, zoom, horizontal, vertical, circle, dolly_zoom") 
    amplitude: float = Field(1.5, ge=0.0, le=10.0) 
    speed: float = Field(1.0, gt=0.0)
    reverse: bool = Field(False)
    smooth: bool = Field(True)
    loop: bool = Field(True)
    phase: float = Field(0.0, ge=-10.0, le=10.0)
    focus: float = Field(0.5, ge=0.0, le=1.0)

class EffectsSettings(BaseModel):
    dof_enable: bool = Field(False)             
    dof_intensity: float = Field(1.0, ge=0.0, le=2.0)
    dof_start: float = Field(0.5, ge=0.0, le=1.0)  
    dof_end: float = Field(1.0, ge=0.0, le=1.0)
    dof_quality: int = Field(4, ge=1, le=16)       
    dof_directions: int = Field(16, ge=1, le=32)
    vignette_enable: bool = Field(True)         
    vignette_intensity: float = Field(0.3, ge=0.0, le=1.0) 
    vignette_decay: float = Field(20.0, ge=0.0, le=100.0)
    color_enable: bool = Field(False)
    color_saturation: float = Field(105.0, ge=0.0, le=200.0) 
    color_contrast: float = Field(105.0, ge=0.0, le=200.0)   
    color_brightness: float = Field(100.0, ge=0.0, le=200.0)
    color_gamma: float = Field(100.0, ge=0.0, le=400.0)
    color_sepia: float = Field(0.0, ge=0.0, le=100.0)

class APIPayload(BaseModel):
    render: RenderSettings = RenderSettings()
    motion: MotionSettings
    effects: EffectsSettings = EffectsSettings()

# Cleanup utility to free up cloud disk space after sending the video
def cleanup_files(*file_paths):
    for path in file_paths:
        if os.path.exists(path):
            os.remove(path)

# ---------------------------------------------------------
# 3. THE MICROSERVICE ENDPOINT
# ---------------------------------------------------------
@app.post("/api/v1/render")
async def process_render_job(
    background_tasks: BackgroundTasks,
    image: UploadFile = File(...),
    payload: str = Form(...), 
    x_api_key: str = Header(..., description="Internal Engine Authentication Key")
):
    # Security Check: Reject if the key doesn't match
    if x_api_key != ENGINE_SECRET_KEY:
        raise HTTPException(status_code=403, detail="Forbidden: Invalid Engine Key")

    # Validate JSON Payload
    try:
        parsed_dict = json.loads(payload)
        validated_payload = APIPayload(**parsed_dict)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON Payload: {str(e)}")

    # Setup unique file paths for this job
    job_id = str(uuid.uuid4())
    input_img_path = str(TEMP_DIR / f"{job_id}_{image.filename}")
    output_vid_path = str(TEMP_DIR / f"{job_id}_output.mp4")

    # ---------------------------------------------------------
    # THE 4K GUARDRAIL (SHRINKS MASSIVE IMAGES)
    # ---------------------------------------------------------
    try:
        image_bytes = await image.read()
        pil_img = Image.open(io.BytesIO(image_bytes))

        # If the image is massive, shrink it to 1920px (Standard HD)
        MAX_DIMENSION = 1920
        if max(pil_img.width, pil_img.height) > MAX_DIMENSION:
            pil_img.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.Resampling.LANCZOS)
        
        # Save the safe, optimized image to disk (forces RGB to prevent Alpha channel crashes)
        pil_img.convert("RGB").save(input_img_path, format="JPEG", quality=95)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Image processing failed: {str(e)}")
    # ---------------------------------------------------------

    try:
        # 1. Run AI Depth Estimation
        image_cv, depth_np = get_depth_map(input_img_path)

        # 2. Convert Pydantic model back to dict for the engine
        engine_payload = validated_payload.dict()

        # 3. Execute the Engine
        engine = DepthflowEngine()
        engine.generate_parallax_video(
            image_cv=image_cv, 
            depth_np=depth_np, 
            output_path=output_vid_path, 
            payload=engine_payload
        )

        # 4. Schedule cleanup AFTER the file is successfully sent to the user
        background_tasks.add_task(cleanup_files, input_img_path, output_vid_path)

        # 5. Stream the file back
        return FileResponse(
            path=output_vid_path, 
            media_type="video/mp4", 
            filename=f"rendered_{job_id}.mp4"
        )

    except Exception as e:
        # Cleanup on failure
        cleanup_files(input_img_path, output_vid_path)
        raise HTTPException(status_code=500, detail=f"Rendering Engine Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    # Runs the microservice locally on port 8001
    uvicorn.run(app, host="0.0.0.0", port=8001)
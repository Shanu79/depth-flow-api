import numpy as np
import cv2
from PIL import Image
from transformers import pipeline

print("Loading Depth Anything V2 model...")
# --- ADD device=0 TO THIS LINE ---
depth_estimator = pipeline("depth-estimation", model="depth-anything/Depth-Anything-V2-Small-hf", device=0)

def get_depth_map(image_path):
    print(f"Generating depth map for {image_path}...")
    img = Image.open(image_path).convert('RGB')
    
    # Run inference
    result = depth_estimator(img)
    depth_image = result['depth']
    
    # --- THE FIX: Force strict size matching ---
    if depth_image.size != img.size:
        depth_image = depth_image.resize(img.size, Image.Resampling.BILINEAR)
    # -------------------------------------------
    
    # Convert to numpy array and normalize to 0.0 - 1.0 range
    depth_np = np.array(depth_image, dtype=np.float32)
    depth_np = (depth_np - depth_np.min()) / (depth_np.max() - depth_np.min())
    
    # Convert original image to cv2 format (BGR)
    img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    
    return img_cv, depth_np
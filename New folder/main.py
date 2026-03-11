import os
from core.depth_model import get_depth_map
from core.renderer import DepthflowEngine

def main():
    input_image = "test.jpg"
    output_video = "commercial_cinematic.mp4"
    
    if not os.path.exists(input_image):
        print(f"Error: {input_image} not found.")
        return

    # 1. AI Depth Extraction
    print("Extracting AI Depth Map...")
    image_cv, depth_np = get_depth_map(input_image)

    # 2. Render via Custom Memory Engine
    engine = DepthflowEngine()
    
    # We define our premium cinematic payload!
    cinematic_payload = {
        "dof_enable": True,          # Adds background blur based on depth
        "dof_intensity": 1.5,        # Heavy bokeh
        "vignette_enable": True,     # Darkens the edges
        "vignette_intensity": 0.4,
        "color_enable": True,
        "color_saturation": 1.1,     # Boosts colors slightly
        "color_sepia": 0.15          # Adds a slight vintage cinematic tint
    }

    engine.generate_parallax_video(
        image_cv=image_cv, 
        depth_np=depth_np, 
        output_path=output_video, 
        style="dolly_zoom",          # Try 'orbit', 'arc', 'horizontal', 'dolly_zoom'
        duration=10,
        amplitude=0.8,               # Increase for more extreme camera movement
        effects=cinematic_payload
    )

if __name__ == "__main__":
    main()
import os
from core.depth_model import get_depth_map
from core.renderer import DepthflowEngine

def main():
    input_image = "test.jpg"
    output_video = "commercial_cinematic.mp4"
    
    if not os.path.exists(input_image):
        print(f"Error: {input_image} not found.")
        return

    print("Extracting AI Depth Map...")
    image_cv, depth_np = get_depth_map(input_image)

    # =====================================================================
    # THE FUTURE API PAYLOAD
    # Documented for FastAPI / Pydantic Schema Generation
    # =====================================================================
    api_payload = {
        # --- 1. Global Render Settings ---
        "render": {
            "duration": 15,           # [Optional, Default: 5]   | Range: > 0 (Seconds)
            "fps": 60,               # [Optional, Default: 30]  | Range: >= 1 (Frames per second)
            "quality": 50,           # [Optional, Default: 50]  | Range: 1 to 100 (Internal shader steps)
            "ssaa": 1.0,             # [Optional, Default: 1.0] | Range: 0.0 to 4.0 (Super Sampling Anti-Aliasing)
            "tiling_mode": "mirror", # [Optional, Default: "mirror"] | Options: "mirror", "repeat", "none"
            "edge_fix": 5,           # [Optional, Default: 5]   | Range: 0 to 50 (Dilation pixel count for edge tearing)
            "invert_depth": 0.0      # [Optional, Default: 0.0] | Range: 0.0 to 1.0 (Inverts foreground/background)
        },
        
        # --- 2. Motion Trajectory Settings ---
        "motion": {
            "style": "dolly_zoom",   # [Required] | Options: 'orbit', 'dolly', 'zoom', 'horizontal', 'vertical', 'circle', 'dolly_zoom'
            "amplitude": 1.5,        # [Optional, Default: 0.8] | Range: 0.0 to 10.0 (Movement intensity)
            "speed": 1.5,            # [Optional, Default: 1.0] | Range: > 0.0 (Global animation speed multiplier)
            "reverse": False,        # [Optional, Default: False] | Options: True, False (Play backwards)
            "smooth": True,          # [Optional, Default: True]  | Options: True, False (Apply easing)
            "loop": True,            # [Optional, Default: True]  | Options: True, False (Seamless looping)
            "phase": 0.0,            # [Optional, Default: 0.0] | Range: -10.0 to 10.0 (Starting phase offset)
            "focus": 0.5             # [Optional, Default: 0.5] | Range: 0.0 to 1.0 (Focal point depth/steady value)
        },
        
        # --- 3. Cinematic Post-Processing ---
        # The entire "effects" object is [Optional]. If omitted, no effects are applied.
        "effects": {
            # Depth of Field (Bokeh)
            "dof_enable": True,      # [Optional, Default: False] | Options: True, False
            "dof_intensity": 1.5,    # [Optional, Default: 1.0] | Range: 0.0 to 2.0
            "dof_start": 0.6,        # [Optional, Default: 0.6] | Range: 0.0 to 1.0 (Where blur begins)
            "dof_end": 1.0,          # [Optional, Default: 1.0] | Range: 0.0 to 1.0 (Where blur peaks)
            "dof_quality": 4,        # [Optional, Default: 4]   | Range: 1 to 16
            "dof_directions": 16,    # [Optional, Default: 16]  | Range: 1 to 32
            
            # Vignette
            "vignette_enable": True,     # [Optional, Default: False] | Options: True, False
            "vignette_intensity": 0.4,   # [Optional, Default: 0.2] | Range: 0.0 to 1.0
            "vignette_decay": 20.0,      # [Optional, Default: 20.0]| Range: 0.0 to 100.0
            
            # Color Grading
            "color_enable": True,        # [Optional, Default: False] | Options: True, False
            "color_saturation": 110.0,   # [Optional, Default: 100.0] | Range: 0.0 to 200.0 (100 is original)
            "color_contrast": 100.0,     # [Optional, Default: 100.0] | Range: 0.0 to 200.0 (100 is original)
            "color_brightness": 100.0,   # [Optional, Default: 100.0] | Range: 0.0 to 200.0 (100 is original)
            "color_gamma": 100.0,        # [Optional, Default: 100.0] | Range: 0.0 to 400.0 (100 is original)
            "color_sepia": 15.0          # [Optional, Default: 0.0]   | Range: 0.0 to 100.0 (0 is off)
        }
    }

    # Execute the Engine
    engine = DepthflowEngine()
    engine.generate_parallax_video(
        image_cv=image_cv, 
        depth_np=depth_np, 
        output_path=output_video, 
        payload=api_payload
    )

if __name__ == "__main__":
    main()
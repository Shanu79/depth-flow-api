import cv2
import numpy as np
from PIL import Image

# THE FIX: Import the native Animation classes that the repository uses
from depthflow.scene import DepthScene
from depthflow.animation import Animation

class APIDepthflowScene(DepthScene):
    """
    Custom scene that captures frames to RAM and natively handles cinematic effects.
    """
    def __init__(self, effects=None, **kwargs):
        super().__init__(**kwargs)
        self.captured_frames = []
        self.effects = effects or {}

    def update(self):
        super().update()
        
        # Apply Cinematic Effects (Matches logic from src/effects/depthflow_effects.py)
        if self.effects.get("dof_enable"):
            self.state.blur.enable = True
            self.state.blur.start = self.effects.get("dof_start", 0.6)
            self.state.blur.end = self.effects.get("dof_end", 1.0)
            self.state.blur.intensity = self.effects.get("dof_intensity", 1.0)
            
        if self.effects.get("vignette_enable"):
            self.state.vignette.enable = True
            self.state.vignette.intensity = self.effects.get("vignette_intensity", 0.3)
            
        if self.effects.get("color_enable"):
            self.state.colors.enable = True
            self.state.colors.saturation = self.effects.get("color_saturation", 1.0)
            self.state.colors.sepia = self.effects.get("color_sepia", 0.0)
            
            # Neutralize the other native filters to prevent black/white washouts
            self.state.colors.grayscale = 0.0 
            self.state.colors.contrast = 1.0
            self.state.colors.brightness = 1.0
            self.state.colors.gamma = 1.0

    def next(self, dt):
        super().next(dt)
        # Capture the shader output directly into RAM
        frame_rgb = self.screenshot().copy()
        frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
        self.captured_frames.append(frame_bgr)
        return self


class DepthflowEngine:
    def __init__(self):
        print("Initializing Native Cinematic DepthFlow Engine...")

    def generate_parallax_video(self, image_cv, depth_np, output_path, style="orbit", duration=5, fps=30, effects=None, amplitude=0.5):
        h, w = image_cv.shape[:2]
        
        # Edge Dilation to prevent tearing
        edge_fix = 5 
        kernel_size = edge_fix * 2 + 1
        kernel = np.zeros((kernel_size, kernel_size), np.uint8)
        kernel = cv2.circle(kernel, (edge_fix, edge_fix), edge_fix, 1, -1)
        depth_8u = (depth_np * 255).astype(np.uint8)
        dilated_depth = cv2.dilate(depth_8u, kernel, iterations=1)

        scene = APIDepthflowScene(effects=effects)
        
        image_rgb = cv2.cvtColor(image_cv, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(image_rgb)
        pil_depth = Image.fromarray(dilated_depth)
        
        try:
            scene.image.from_image(pil_image)
            scene.depth.from_image(pil_depth)
        except AttributeError:
            scene.input(image=pil_image, depth=pil_depth)
            
        scene.state.height = 0.5 

        # ---------------------------------------------------------
        # THE 1:1 AKATZ-AI MOTION INJECTION
        # ---------------------------------------------------------
        style = style.lower()
        if style == "orbit":
            preset = Animation.Orbital(intensity=amplitude, steady=0.5, reverse=False, zoom=0.98)
            scene.config.animation.add(preset)
            
        elif style == "dolly":
            preset = Animation.Dolly(intensity=amplitude, reverse=False, smooth=True, loop=True, focus=0.5, phase=0.0)
            scene.config.animation.add(preset)
            
        elif style == "zoom":
            preset = Animation.Zoom(intensity=amplitude, reverse=False, smooth=True, phase=0.0, loop=False, isometric=0.8)
            scene.config.animation.add(preset)
            
        elif style == "horizontal":
            preset = Animation.Horizontal(intensity=amplitude, reverse=False, smooth=True, loop=True, phase=0.0, steady=0.3, isometric=0.6)
            scene.config.animation.add(preset)
            
        elif style == "vertical":
            preset = Animation.Vertical(intensity=amplitude, reverse=False, smooth=True, loop=True, phase=0.0, steady=0.3, isometric=0.6)
            scene.config.animation.add(preset)
            
        elif style == "circle":
            preset = Animation.Circle(intensity=amplitude, reverse=False, phase=(0.0, 0.0, 0.0), amplitude=(1.0, 1.0, 0.0), steady=0.3, isometric=0.6)
            scene.config.animation.add(preset)
        
        # Dolly Zoom (Custom composite of their presets)
        elif style == "dolly_zoom":
            scene.config.animation.add(Animation.Dolly(intensity=amplitude, focus=0.5))
            scene.config.animation.add(Animation.Zoom(intensity=amplitude*0.4, isometric=0.8))

        # ---------------------------------------------------------

        print(f"Executing GPU Shader for {duration} seconds...")
        
        scene.main(
            render=False, 
            output=None, 
            fps=fps, 
            time=duration, 
            freewheel=True,
            width=w,
            height=h
        )

        print(f"Stitching {len(scene.captured_frames)} frames to {output_path}...")
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (w, h))
        
        for frame in scene.captured_frames:
            frame_resized = cv2.resize(frame, (w, h), interpolation=cv2.INTER_LINEAR)
            out.write(frame_resized)
            
        out.release()
        scene.captured_frames.clear()
        print("Generation Complete.")
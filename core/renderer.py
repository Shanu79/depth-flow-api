import cv2
import numpy as np
from PIL import Image

from depthflow.scene import DepthScene
from depthflow.animation import Animation

class APIDepthflowScene(DepthScene):
    """
    Custom scene that natively handles the complete API payload.
    """
    def __init__(self, effects=None, render_cfg=None, **kwargs):
        super().__init__(**kwargs)
        self.captured_frames = []
        self.effects = effects or {}
        
        # Apply Tiling and Invert settings
        if render_cfg:
            self.state.invert = render_cfg.get("invert_depth", 0.0)
            tiling = render_cfg.get("tiling_mode", "mirror")
            if tiling == "mirror":
                self.state.mirror = True
            elif tiling == "repeat":
                self.state.mirror = False # Handled natively by wrapping

    def update(self):
        super().update()
        
        # Apply Cinematic Effects
        if self.effects.get("dof_enable"):
            self.state.blur.enable = True
            self.state.blur.start = self.effects.get("dof_start", 0.6)
            self.state.blur.end = self.effects.get("dof_end", 1.0)
            self.state.blur.intensity = self.effects.get("dof_intensity", 1.0)
            self.state.blur.quality = self.effects.get("dof_quality", 4)
            self.state.blur.directions = self.effects.get("dof_directions", 16)
            
        if self.effects.get("vignette_enable"):
            self.state.vignette.enable = True
            self.state.vignette.intensity = self.effects.get("vignette_intensity", 0.2)
            self.state.vignette.decay = self.effects.get("vignette_decay", 20.0)
            
        if self.effects.get("color_enable"):
            self.state.colors.enable = True
            self.state.colors.saturation = self.effects.get("color_saturation", 100.0)
            self.state.colors.sepia = self.effects.get("color_sepia", 0.0)
            self.state.colors.grayscale = 0.0 
            self.state.colors.contrast = self.effects.get("color_contrast", 100.0)
            self.state.colors.brightness = self.effects.get("color_brightness", 100.0)
            self.state.colors.gamma = self.effects.get("color_gamma", 100.0)

    def next(self, dt):
        super().next(dt)
        frame_rgb = self.screenshot().copy()
        frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
        self.captured_frames.append(frame_bgr)
        return self


class DepthflowEngine:
    def __init__(self):
        print("Initializing Native Cinematic DepthFlow Engine...")

    def generate_parallax_video(self, image_cv, depth_np, output_path, payload):
        # Extract configurations from our API payload
        render_cfg = payload.get("render", {})
        motion_cfg = payload.get("motion", {})
        effects_cfg = payload.get("effects", {})
        
        h, w = image_cv.shape[:2]
        
        # 1. Edge Dilation (Configurable via API)
        edge_fix = render_cfg.get("edge_fix", 5)
        if edge_fix > 0:
            kernel_size = edge_fix * 2 + 1
            kernel = np.zeros((kernel_size, kernel_size), np.uint8)
            kernel = cv2.circle(kernel, (edge_fix, edge_fix), edge_fix, 1, -1)
            depth_8u = (depth_np * 255).astype(np.uint8)
            dilated_depth = cv2.dilate(depth_8u, kernel, iterations=1)
        else:
            dilated_depth = (depth_np * 255).astype(np.uint8)

        # 2. Initialize Scene
        scene = APIDepthflowScene(effects=effects_cfg, render_cfg=render_cfg)
        
        image_rgb = cv2.cvtColor(image_cv, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(image_rgb)
        pil_depth = Image.fromarray(dilated_depth)
        
        try:
            scene.image.from_image(pil_image)
            scene.depth.from_image(pil_depth)
            if render_cfg.get("tiling_mode") == "repeat":
                scene.image.repeat(True)
                scene.depth.repeat(True)
        except AttributeError:
            scene.input(image=pil_image, depth=pil_depth)
            
        scene.state.height = 0.5 

        # 3. Motion Injection (With all advanced UI toggles)
        style = motion_cfg.get("style", "orbit").lower()
        amp = motion_cfg.get("amplitude", 0.8)
        rev = motion_cfg.get("reverse", False)
        smth = motion_cfg.get("smooth", True)
        lp = motion_cfg.get("loop", True)
        ph = motion_cfg.get("phase", 0.0)
        foc = motion_cfg.get("focus", 0.5)

        if style == "orbit":
            scene.config.animation.add(Animation.Orbital(intensity=amp, steady=foc, reverse=rev, zoom=0.98))
        elif style == "dolly":
            scene.config.animation.add(Animation.Dolly(intensity=amp, reverse=rev, smooth=smth, loop=lp, focus=foc, phase=ph))
        elif style == "zoom":
            scene.config.animation.add(Animation.Zoom(intensity=amp, reverse=rev, smooth=smth, phase=ph, loop=lp, isometric=0.8))
        elif style == "horizontal":
            scene.config.animation.add(Animation.Horizontal(intensity=amp, reverse=rev, smooth=smth, loop=lp, phase=ph, steady=0.3, isometric=0.6))
        elif style == "vertical":
            scene.config.animation.add(Animation.Vertical(intensity=amp, reverse=rev, smooth=smth, loop=lp, phase=ph, steady=0.3, isometric=0.6))
        elif style == "circle":
            scene.config.animation.add(Animation.Circle(intensity=amp, reverse=rev, phase=(ph, ph, 0.0), amplitude=(1.0, 1.0, 0.0), steady=0.3, isometric=0.6))
        elif style == "dolly_zoom":
            scene.config.animation.add(Animation.Dolly(intensity=amp, focus=foc, reverse=rev, smooth=smth, loop=lp))
            scene.config.animation.add(Animation.Zoom(intensity=amp*0.4, isometric=0.8, reverse=rev, smooth=smth))

        fps = render_cfg.get("fps", 30)
        duration = render_cfg.get("duration", 5)

        print(f"Executing GPU Shader for {duration} seconds...")
        
        # 4. Render Headless (Passing Quality and SSAA natively)
        scene.main(
            render=False, 
            output=None, 
            fps=fps, 
            time=duration,
            speed=motion_cfg.get("speed", 1.0),
            quality=render_cfg.get("quality", 50),
            ssaa=render_cfg.get("ssaa", 1.0),
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
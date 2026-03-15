# 🌊 DepthFlow Cinematic API

A high-performance, headless 2.5D animation engine. This application converts static 2D images into cinematic 3D parallax videos by leveraging Depth-Anything-V2 for depth estimation and a custom OpenGL Shader Engine for real-time rendering.

## 🚀 Context & Capabilities

This project is designed as a production-ready backend for commercial AI image-to-video services. Unlike standard parallax tools, it incorporates:

- **AI-Driven Depth Estimation**: Automatic 3D map generation from any 2D image.
- **Headless GPU/CPU Rendering**: High-speed frame capture directly from shader memory to RAM.
- **Cinematic Post-Processing**: Native support for Depth of Field (Bokeh), Vignetting, and Color Grading.
- **Advanced Motion Presets**: 1:1 implementation of professional camera trajectories (Dolly-Zoom, Orbit, Arc, etc.).

## 🛠 Parameters & Configuration

The engine is controlled via a centralized `api_payload`. Below are the documented ranges and requirements for the developer:

### 1. Global Render Settings (render)

| Parameter     | Requirement | Default | Range / Options |
|---------------|-------------|---------|-----------------|
| duration      | Optional    | 5       | > 0 (Seconds)   |
| fps           | Optional    | 30      | 1 to 120        |
| quality       | Optional    | 50      | 1 to 100 (Shader precision) |
| ssaa          | Optional    | 1.0     | 0.0 to 4.0 (Anti-aliasing) |
| tiling_mode   | Optional    | "mirror" | "mirror", "repeat", "none" |
| edge_fix      | Optional    | 5       | 0 to 50 (Dilation to prevent edge tearing) |
| invert_depth  | Optional    | 0.0     | 0.0 to 1.0 (Swaps foreground/background) |

### 2. Motion Trajectory (motion)

| Parameter     | Requirement | Default | Range / Options |
|---------------|-------------|---------|-----------------|
| style         | Required    | -       | 'orbit', 'dolly', 'zoom', 'horizontal', 'vertical', 'circle', 'dolly_zoom' |
| amplitude     | Optional    | 0.8     | 0.0 to 10.0 (Movement intensity) |
| speed         | Optional    | 1.0     | > 0.0 (Playback speed) |
| reverse       | Optional    | False   | True, False |
| loop          | Optional    | True    | True, False |
| focus         | Optional    | 0.5     | 0.0 to 1.0 (Focal depth) |

### 3. Cinematic Effects (effects)

| Parameter          | Default | Range / Options |
|--------------------|---------|-----------------|
| dof_enable         | False   | Depth of Field toggle |
| dof_intensity      | 1.0     | 0.0 to 2.0 |
| dof_start/end      | 0.6 / 1.0 | 0.0 to 1.0 (Blur transition) |
| vignette_intensity | 0.2     | 0.0 to 1.0 |
| color_saturation   | 100.0   | 0.0 to 200.0 (100 is original) |
| color_sepia        | 0.0     | 0.0 to 100.0 |

## 📦 Example API Payloads

Depending on the desired output quality and processing speed, developers can send different tiers of payloads to the `/generate` endpoint.

### The "Standard" Payload (Social Media & Web)
Perfect for general use, social media generators, or web animations. It overrides the default settings to generate a smoother, longer video while keeping heavy post-processing turned off to ensure fast API response times.

```json
{
  "render": {
    "duration": 10,
    "fps": 60,
    "quality": 50
  },
  "motion": {
    "style": "orbit",
    "amplitude": 1.5,
    "speed": 1.2,
    "focus": 0.5
  }
}
```

### The "Advanced" Payload (Cinematic & Professional)
Designed for high-end applications. It pushes render quality to the maximum, applies a custom color grade, activates high-quality Depth of Field (Bokeh), and executes complex camera movements like the Vertigo effect (dolly_zoom).

```json
{
  "render": {
    "duration": 15,
    "fps": 60,
    "quality": 100,
    "ssaa": 2.0,
    "tiling_mode": "mirror",
    "edge_fix": 10
  },
  "motion": {
    "style": "dolly_zoom",
    "amplitude": 2.0,
    "speed": 0.8,
    "reverse": false,
    "smooth": true,
    "loop": false,
    "phase": 0.0,
    "focus": 0.7
  },
  "effects": {
    "dof_enable": true,
    "dof_intensity": 1.5,
    "dof_start": 0.4,
    "dof_end": 1.0,
    "dof_quality": 8,
    "vignette_enable": true,
    "vignette_intensity": 0.6,
    "color_enable": true,
    "color_saturation": 115.0,
    "color_contrast": 105.0,
    "color_gamma": 95.0,
    "color_sepia": 10.0
  }
}
```

### ☁️ Cloud CPU Deployment: Next Steps
While this engine is optimized for GPU, it is fully compatible with Cloud CPU environments (like AWS EC2, DigitalOcean, or Google Cloud) using Software Rendering.

1. Headless Virtual Display (Xvfb)
Cloud CPUs lack a physical monitor, but OpenGL requires a display context. You must use Xvfb to create a virtual frame buffer:

Bash
sudo apt-get install xvfb python3-opengl
xvfb-run -s "-screen 0 1920x1080x24" python main.py
2. Software OpenGL (Mesa)
On instances without a GPU, force the system to use the CPU for OpenGL calculations:

Bash
# Force Mesa software rendering
export LIBGL_ALWAYS_SOFTWARE=1
export GALLIUM_DRIVER=llvmpipe
3. Environment Dependencies
Ensure the following are installed in your cloud environment:

FFmpeg: Required by OpenCV for video stitching.

Mesa-utils: For software GL dispatching.

Virtual Environment:

Bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
4. FastAPI Integration
The next step for deployment is wrapping main.py in a FastAPI endpoint.

Endpoint: POST /api/v1/render

Input: Multi-part form data (Image + JSON Payload).

Output: File stream of the generated .mp4.

### 📂 Project Structure
engine_api.py: Entry point for the FastAPI microservice.

main.py: CLI testing script for local payload validation.

core/depth_model.py: Handles Depth-Anything-V2 AI inference.

core/renderer.py: The custom APIDepthflowScene that manages math and memory frame capture.

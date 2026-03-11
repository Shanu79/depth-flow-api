# import cv2
# import numpy as np
# from simple_lama_inpainting import SimpleLama
# from PIL import Image
# from rembg import remove, new_session

# print("Loading LaMa Inpainting model...")
# lama = SimpleLama()

# print("Loading U²-Net Segmentation model...")
# rembg_session = new_session()

# def split_and_inpaint_layers(img_cv, depth_np):
#     print("Separating Foreground and Inpainting Background...")
    
#     h, w = img_cv.shape[:2]
#     img_pil = Image.fromarray(cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB))
    
#     # 1. SEMANTIC FOREGROUND MASKING (The Fix)
#     # Use AI to perfectly outline the main subject, ignoring depth gradients
#     mask_pil = remove(img_pil, session=rembg_session, only_mask=True)
#     base_mask = np.array(mask_pil)
    
#     # Fallback: If no clear subject is found (e.g., landscape photo), 
#     # fall back to the old depth-based thresholding.
#     if np.count_nonzero(base_mask) < (h * w * 0.05):
#         print("No prominent subject found. Falling back to depth thresholding...")
#         depth_8u = (depth_np * 255).astype(np.uint8)
#         _, base_mask = cv2.threshold(depth_8u, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

#     # 2. The Background (LaMa) Mask
#     bg_kernel = np.ones((9, 9), np.uint8) 
#     lama_mask = cv2.dilate(base_mask, bg_kernel, iterations=2)
    
#     mask_pil_lama = Image.fromarray(lama_mask).convert('L')
#     bg_inpainted_pil = lama(img_pil, mask_pil_lama)
    
#     # Force strict size matching
#     if bg_inpainted_pil.size != img_pil.size:
#         bg_inpainted_pil = bg_inpainted_pil.resize(img_pil.size, Image.Resampling.BILINEAR)
        
#     bg_inpainted_cv = cv2.cvtColor(np.array(bg_inpainted_pil), cv2.COLOR_RGB2BGR)
    
#     depth_8u = (depth_np * 255).astype(np.uint8)
#     bg_depth_8u = cv2.inpaint(depth_8u, lama_mask, inpaintRadius=5, flags=cv2.INPAINT_TELEA)
#     bg_depth_np = bg_depth_8u.astype(np.float32) / 255.0
    
#     # 3. The Foreground Alpha Matting
#     fg_kernel = np.ones((3, 3), np.uint8)
#     eroded_mask = cv2.erode(base_mask, fg_kernel, iterations=1)
#     soft_alpha_mask = cv2.GaussianBlur(eroded_mask, (15, 15), 0)
    
#     fg_cv = cv2.cvtColor(img_cv, cv2.COLOR_BGR2BGRA)
#     fg_cv[:, :, 3] = soft_alpha_mask 
    
#     return bg_inpainted_cv, bg_depth_np, fg_cv, depth_np
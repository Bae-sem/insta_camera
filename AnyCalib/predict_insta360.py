import sys
import os
import torch
import numpy as np
import json
from PIL import Image

# Add current directory to path to find anycalib
sys.path.append(os.getcwd())

try:
    from anycalib import AnyCalib
except ImportError:
    print("Could not import AnyCalib. Make sure you are in the AnyCalib directory and installed it.")
    sys.exit(1)

def run_calibration():
    # Check for CUDA
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    # Initialize model
    model_id = "anycalib_gen" 
    print(f"Loading model: {model_id}...")
    try:
        model = AnyCalib(model_id=model_id).to(device)
        model.eval()
    except Exception as e:
        print(f"Error loading model: {e}")
        return

    # Image paths
    base_path = "../photos"
    out_dir = "anycalib_results"
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    image_files = [f"origin_{i}.jpg" for i in range(1, 7)]

    # Camera model
    target_cam_id = "kb:4" 
    print(f"Target Camera Model: {target_cam_id}")

    results = {}

    for img_file in image_files:
        img_path = os.path.join(base_path, img_file)
        if not os.path.exists(img_path):
            print(f"Image not found: {img_path}")
            continue

        try:
            print(f"Processing {img_file}...")
            pil_img = Image.open(img_path).convert("RGB")
            img_np = np.array(pil_img)
            
            # Predict
            img_tensor = torch.tensor(img_np, dtype=torch.float32, device=device).permute(2, 0, 1) / 255.0
            
            with torch.no_grad():
                output = model.predict(img_tensor, cam_id=target_cam_id)
            
            intrinsics = output["intrinsics"].cpu().numpy()
            results[img_file] = intrinsics.tolist()
            
            print(f"  Intrinsics: {intrinsics}")
            
            # Undistort verification
            try:
                import cv2
                fx, fy, cx, cy = intrinsics[0], intrinsics[1], intrinsics[2], intrinsics[3]
                D = intrinsics[4:] 
                
                K = np.array([[fx, 0, cx], [0, fy, cy], [0, 0, 1]], dtype=np.float32)
                D_np = np.array(D, dtype=np.float32)

                img_cv = cv2.imread(img_path)
                h, w = img_cv.shape[:2]
                
                # 1. Standard approach (No Zoom, just K)
                nk = K.copy()
                undistorted_img = cv2.fisheye.undistortImage(img_cv, K, D_np, Knew=nk, new_size=(w, h))

                # Save images
                import re
                match = re.search(r'origin_(\d+)', img_file)
                if match:
                    num = match.group(1)
                    out_name = f"calib_photo{num}.jpg"
                else:
                    out_name = f"calib_{img_file}"
                
                cv2.imwrite(os.path.join(out_dir, out_name), undistorted_img)
                print(f"  Saved image to {out_dir}")

            except ImportError:
                print("OpenCV not found.")
            except Exception as e:
                print(f"Error undistorting {img_file}: {e}")

        except Exception as e:
            print(f"Failed to process {img_file}: {e}")

    # Save to JSON
    json_path = "anycalib.json"
    with open(json_path, 'w') as f:
        json.dump(results, f, indent=4)
    print(f"\nSaved calibration parameters to {json_path}")

if __name__ == "__main__":
    run_calibration()

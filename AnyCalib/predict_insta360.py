#!/usr/bin/env python3
"""
Insta360 Pro 2 Camera Calibration using AnyCalib

This script performs camera calibration on Insta360 Pro 2 fisheye images
using the AnyCalib model. All parameters can be configured via config.json.

Usage:
    python predict_insta360.py                    # Uses default config.json
    python predict_insta360.py --config my_config.json  # Uses custom config
"""

import sys
import os
import argparse
import json
import torch
import numpy as np
from PIL import Image

# Add current directory to path to find anycalib
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from anycalib import AnyCalib
except ImportError:
    print("Error: Could not import AnyCalib.")
    print("Make sure you are in the AnyCalib directory and have installed it with 'pip install -e .'")
    sys.exit(1)


def load_config(config_path: str = "config.json") -> dict:
    """Load configuration from JSON file."""
    if not os.path.exists(config_path):
        print(f"Warning: Config file '{config_path}' not found. Using default values.")
        return get_default_config()
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    print(f"Loaded configuration from: {config_path}")
    return config


def get_default_config() -> dict:
    """Return default configuration."""
    return {
        "model": {
            "model_id": "anycalib_gen"
        },
        "camera": {
            "cam_id": "kb:4"
        },
        "input": {
            "image_dir": "../photos",
            "image_pattern": "origin_{}.jpg",
            "image_indices": [1, 2, 3, 4, 5, 6]
        },
        "output": {
            "output_dir": "anycalib_results",
            "json_file": "anycalib.json",
            "save_undistorted": True,
            "undistorted_prefix": "calib_photo"
        },
        "optimization": {
            "nonlin_opt_method": "gauss_newton",
            "init_with_sac": False,
            "fallback_to_sac": True,
            "rm_borders": 0,
            "sample_size": -1
        },
        "device": {
            "use_cuda": True
        }
    }


def get_device(config: dict) -> torch.device:
    """Determine the device to use based on config and availability."""
    use_cuda = config.get("device", {}).get("use_cuda", True)
    
    if use_cuda and torch.cuda.is_available():
        device = torch.device("cuda")
        print(f"Using device: CUDA ({torch.cuda.get_device_name(0)})")
    else:
        device = torch.device("cpu")
        if use_cuda:
            print("Warning: CUDA requested but not available. Using CPU.")
        else:
            print("Using device: CPU")
    
    return device


def load_model(config: dict, device: torch.device) -> AnyCalib:
    """Load the AnyCalib model based on configuration."""
    model_config = config.get("model", {})
    opt_config = config.get("optimization", {})
    
    model_id = model_config.get("model_id", "anycalib_gen")
    
    print(f"\nLoading model: {model_id}")
    
    try:
        model = AnyCalib(
            model_id=model_id,
            nonlin_opt_method=opt_config.get("nonlin_opt_method", "gauss_newton"),
            init_with_sac=opt_config.get("init_with_sac", False),
            fallback_to_sac=opt_config.get("fallback_to_sac", True),
            rm_borders=opt_config.get("rm_borders", 0),
            sample_size=opt_config.get("sample_size", -1)
        ).to(device)
        model.eval()
        return model
    except Exception as e:
        print(f"Error loading model: {e}")
        sys.exit(1)


def get_image_paths(config: dict) -> list:
    """Generate list of image paths based on configuration."""
    input_config = config.get("input", {})
    
    image_dir = input_config.get("image_dir", "../photos")
    pattern = input_config.get("image_pattern", "origin_{}.jpg")
    indices = input_config.get("image_indices", [1, 2, 3, 4, 5, 6])
    
    image_paths = []
    for idx in indices:
        filename = pattern.format(idx)
        filepath = os.path.join(image_dir, filename)
        image_paths.append((idx, filename, filepath))
    
    return image_paths


def save_undistorted_image(
    img_path: str, 
    intrinsics: np.ndarray, 
    output_dir: str, 
    prefix: str, 
    idx: int
) -> bool:
    """Save undistorted image using OpenCV fisheye undistortion."""
    try:
        import cv2
        
        fx, fy, cx, cy = intrinsics[0], intrinsics[1], intrinsics[2], intrinsics[3]
        D = intrinsics[4:]  # Distortion coefficients
        
        K = np.array([[fx, 0, cx], [0, fy, cy], [0, 0, 1]], dtype=np.float32)
        D_np = np.array(D, dtype=np.float32)
        
        img_cv = cv2.imread(img_path)
        if img_cv is None:
            print(f"    Error: Could not read image with OpenCV")
            return False
        
        h, w = img_cv.shape[:2]
        
        # Standard undistortion (no zoom, using same K)
        nk = K.copy()
        undistorted_img = cv2.fisheye.undistortImage(img_cv, K, D_np, Knew=nk, new_size=(w, h))
        
        # Save undistorted image
        out_name = f"{prefix}{idx}.jpg"
        out_path = os.path.join(output_dir, out_name)
        cv2.imwrite(out_path, undistorted_img)
        print(f"    Saved undistorted image: {out_name}")
        return True
        
    except ImportError:
        print("    Warning: OpenCV not installed. Skipping undistortion.")
        return False
    except Exception as e:
        print(f"    Error during undistortion: {e}")
        return False


def run_calibration(config: dict):
    """Main calibration function."""
    # Setup device
    device = get_device(config)
    
    # Load model
    model = load_model(config, device)
    
    # Get image paths
    image_paths = get_image_paths(config)
    
    # Camera model
    cam_id = config.get("camera", {}).get("cam_id", "kb:4")
    print(f"Camera model: {cam_id}")
    
    # Output settings
    output_config = config.get("output", {})
    output_dir = output_config.get("output_dir", "anycalib_results")
    json_file = output_config.get("json_file", "anycalib.json")
    save_undistorted = output_config.get("save_undistorted", True)
    undistorted_prefix = output_config.get("undistorted_prefix", "calib_photo")
    
    # Create output directory
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"\nCreated output directory: {output_dir}")
    
    # Process images
    results = {}
    print(f"\nProcessing {len(image_paths)} images...\n")
    
    for idx, filename, filepath in image_paths:
        if not os.path.exists(filepath):
            print(f"[{idx}] Image not found: {filepath}")
            continue
        
        try:
            print(f"[{idx}] Processing: {filename}")
            
            # Load image
            pil_img = Image.open(filepath).convert("RGB")
            img_np = np.array(pil_img)
            img_tensor = torch.tensor(img_np, dtype=torch.float32, device=device).permute(2, 0, 1) / 255.0
            
            # Run prediction
            with torch.no_grad():
                output = model.predict(img_tensor, cam_id=cam_id)
            
            # Extract intrinsics
            intrinsics = output["intrinsics"].cpu().numpy()
            results[filename] = intrinsics.tolist()
            
            # Print results
            print(f"    Intrinsics: fx={intrinsics[0]:.2f}, fy={intrinsics[1]:.2f}, cx={intrinsics[2]:.2f}, cy={intrinsics[3]:.2f}")
            if len(intrinsics) > 4:
                print(f"    Distortion: {[f'{d:.6f}' for d in intrinsics[4:]]}")
            
            # Save undistorted image
            if save_undistorted:
                save_undistorted_image(filepath, intrinsics, output_dir, undistorted_prefix, idx)
            
        except Exception as e:
            print(f"[{idx}] Error processing {filename}: {e}")
    
    # Save results to JSON
    if results:
        with open(json_file, 'w') as f:
            json.dump(results, f, indent=4)
        print(f"\n{'='*50}")
        print(f"Calibration complete!")
        print(f"  - Results saved to: {json_file}")
        print(f"  - Undistorted images: {output_dir}/")
        print(f"  - Processed {len(results)}/{len(image_paths)} images")
        print(f"{'='*50}")
    else:
        print("\nWarning: No images were processed successfully.")


def main():
    parser = argparse.ArgumentParser(
        description="Insta360 Pro 2 Camera Calibration using AnyCalib",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python predict_insta360.py
  python predict_insta360.py --config my_config.json
  python predict_insta360.py -c /path/to/config.json

For detailed configuration options, see config.json or the project README.
        """
    )
    parser.add_argument(
        '-c', '--config',
        type=str,
        default='config.json',
        help='Path to configuration JSON file (default: config.json)'
    )
    parser.add_argument(
        '--print-config',
        action='store_true',
        help='Print default configuration and exit'
    )
    
    args = parser.parse_args()
    
    if args.print_config:
        print("Default configuration:")
        print(json.dumps(get_default_config(), indent=4))
        return
    
    print("="*50)
    print("Insta360 Pro 2 Camera Calibration (AnyCalib)")
    print("="*50)
    
    config = load_config(args.config)
    run_calibration(config)


if __name__ == "__main__":
    main()

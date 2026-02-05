#!/usr/bin/env python3
import json
import sys
import os

def fix_calib_json(json_path):
    """
    koide3/direct_visual_lidar_calibration 툴의 preprocess 결과물(calib.json)을
    equirectangular 모델에 맞게 수정하는 스크립트.
    
    preprocess 툴은 기본적으로 핀홀 모델을 가정하여 intrinsic 4개, distortion 5개를 저장하지만,
    equirectangular 모델은 intrinsic 2개(width, height), distortion 0개를 요구합니디.
    """
    
    if not os.path.exists(json_path):
        print(f"Error: File not found at {json_path}")
        sys.exit(1)

    with open(json_path, 'r') as f:
        data = json.load(f)

    camera_config = data.get("camera", {})
    model = camera_config.get("camera_model", "")

    print(f"Current Model: {model}")

    if model == "equirectangular":
        print("⚡ Equirectangular model detected. Applying Fix...")
        
        # 1. Distortion Coeffs 삭제 (빈 리스트)
        # 파노라마는 이미 왜곡이 펴진 상태이므로 값이 필요 없음
        camera_config["distortion_coeffs"] = []
        
        # 2. Intrinsics 수정 (4개 -> 2개)
        # 원래 값: [fx, fy, cx, cy] 등으로 잘못 들어있음
        # 목표 값: [Width, Height]
        # 다행히 preprocess 툴은 intrinsics를 K매트릭스에서 가져오는데, 
        # 우리가 insta_bridge에서 정확한 K를 줬다면 K[0]가 fx, K[4]가 fy임.
        # 하지만 equirectangular 정의상 intrinsics[0] = Width, intrinsics[1] = Height여야 함.
        
        # 여기서 우리는 "이미지 해상도"를 알아야 함.
        # calib.json에는 이미지 해상도 정보가 직접적으로는 없음 (이미지 파일 등을 로드해야 알 수 있음)
        # 하지만 사용자가 "3840x1920" 해상도를 사용한다고 가정하고 하드코딩하거나,
        # 사용자가 수동으로 입력하게 할 수 있음.
        
        # 안전한 방법: 사용자에게 묻거나, 기본값 3840x1920 적용
        # 여기서는 가장 많이 쓰이는 Insta360 Stitching 해상도 적용
        
        # 현재 값 확인
        current_intrinsics = camera_config.get("intrinsics", [])
        print(f"Original Intrinsics: {current_intrinsics}")
        
        # 해상도 추정 (fx를 통해 역산하거나, 고정값 사용)
        # insta_bridge.py에서 fx = width / 2pi 로 보냈다면 역산 가능하지만,
        # 가장 확실한건 그냥 3840, 1920을 넣는 것임.
        
        # 주의: 만약 1920x960 모드라면 이 값을 바꿔줘야 함.
        # 일단 3840x1920 (4K Pano) 기준으로 수정.
        
        new_width = 3840.0
        new_height = 1920.0
        
        # 만약 기존 K값에서 힌트를 얻고 싶다면?
        # fx ~ 611 이었다면? width = 611 * 2 * 3.14 = 3837... -> 3840
        if len(current_intrinsics) > 0:
             est_width = current_intrinsics[0] * 2 * 3.14159265
             if abs(est_width - 1920) < 100:
                 new_width = 1920.0
                 new_height = 960.0
                 print(f"Detected 2K Mode (Estimated Width: {est_width:.1f})")
             else:
                 print(f"Detected 4K Mode (Estimated Width: {est_width:.1f})")

        camera_config["intrinsics"] = [new_width, new_height]
        
        print(f"✅ Fixed Intrinsics: {camera_config['intrinsics']}")
        print(f"✅ Fixed Distortion: {camera_config['distortion_coeffs']}")
        
        # 저장
        with open(json_path, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Successfully updated {json_path}")
        
    else:
        print("Not an equirectangular model. No changes needed.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 fix_calib.py <path_to_calib.json>")
        sys.exit(1)
    
    fix_calib_json(sys.argv[1])

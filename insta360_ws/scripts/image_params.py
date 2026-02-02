#!/usr/bin/env python3
"""
이미지 파라미터 조회

사용법:
    python3 image_params.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from insta360 import Insta360Camera
from insta360.config import AAA_MODES, WHITE_BALANCE, ISO_VALUES, SHUTTER_VALUES


# 역변환 맵 생성
AAA_MODES_REV = {v: k for k, v in AAA_MODES.items()}
WB_REV = {v: k for k, v in WHITE_BALANCE.items()}
ISO_REV = {v: k for k, v in ISO_VALUES.items()}
SHUTTER_REV = {v: k for k, v in SHUTTER_VALUES.items()}


def main():
    print("=" * 50)
    print("📸 Insta360 Pro 2 이미지 파라미터")
    print("=" * 50)
    
    try:
        with Insta360Camera() as cam:
            print(f"✅ 연결됨: {cam.serial}\n")
            
            try:
                params = cam.get_image_params()
                
                # 보기 좋게 출력
                aaa = params.get('aaa_mode', 0)
                print(f"🎛️ 3A 모드: {AAA_MODES_REV.get(aaa, aaa)}")
                
                wb = params.get('wb', 0)
                print(f"☀️ 화이트밸런스: {WB_REV.get(wb, wb)}")
                
                iso = params.get('iso_value', 0)
                print(f"📷 ISO: {ISO_REV.get(iso, iso)}")
                
                shutter = params.get('shutter_value', 0)
                print(f"⏱️ 셔터: {SHUTTER_REV.get(shutter, shutter)}")
                
                print(f"🌟 밝기: {params.get('brightness', 0)}")
                print(f"🎨 대비: {params.get('contrast', 0)}")
                print(f"🌈 채도: {params.get('saturation', 0)}")
                print(f"✨ 선명도: {params.get('sharpness', 0)}")
                print(f"📊 EV 보정: {params.get('ev_bias', 0)}")
                
            except RuntimeError as e:
                print(f"⚠️ 이미지 파라미터 조회 불가")
                print(f"   (미리보기/녹화 중에만 조회 가능할 수 있음)")
                print(f"   오류: {e}")
                
    except Exception as e:
        print(f"❌ 오류: {e}")


if __name__ == "__main__":
    main()

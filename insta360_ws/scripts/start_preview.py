#!/usr/bin/env python3
"""미리보기 시작 (연결 유지)"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from insta360 import Insta360Camera
from insta360.config import CAMERA_IP

SETTINGS = {
    'origin': {'mime': 'h264', 'width': 1920, 'height': 1440, 'framerate': 30, 'bitrate': 20480},
    'stiching': {'mode': 'pano', 'mime': 'h264', 'width': 3840, 'height': 1920, 'framerate': 30, 'bitrate': 10240},
    'stabilization': True
}

print("👁️ 미리보기 시작")
cam = Insta360Camera()
cam.connect()
print(f"✅ 연결: {cam.serial}")

url = cam.start_preview(SETTINGS)

# 127.0.0.1 -> 카메라 IP로 변환
fixed_url = url.replace("127.0.0.1", CAMERA_IP)

print(f"\n✅ 미리보기 시작됨!")
print(f"\n📺 VLC로 보기:")
print(f"   vlc {fixed_url}")
print(f"\n⚠️ 연결을 유지하려면 이 터미널을 열어두세요!")
print(f"📝 중지: python3 scripts/stop_preview.py")

# 연결 유지 - 미리보기 중에도 하트비트 필요
import time
try:
    print("\n[Ctrl+C로 종료]")
    while True:
        time.sleep(3)
        cam.get_state()  # 하트비트
        print(".", end="", flush=True)
except KeyboardInterrupt:
    print("\n\n⏹️ 중지 중...")
    cam.stop_preview()
    cam.disconnect()
    print("✅ 완료!")

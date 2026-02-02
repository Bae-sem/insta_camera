#!/usr/bin/env python3
"""녹화 시작"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from insta360 import Insta360Camera

SETTINGS = {
    'origin': {'mime': 'h264', 'width': 1920, 'height': 1440, 'framerate': 30, 'bitrate': 20000, 'saveOrigin': True, 'storage_loc': 0},
    'stiching': {'mode': 'pano', 'mime': 'h264', 'width': 3840, 'height': 1920, 'framerate': 30, 'bitrate': 10000}
}

print("🔴 녹화 시작")
with Insta360Camera() as cam:
    print(f"✅ 연결: {cam.serial}")
    data = cam._send_command('camera._startRecording', SETTINGS, timeout=30)
    if data.get('state') == 'done':
        print("✅ 녹화 시작됨!")
        print("📝 중지: python3 scripts/stop_record.py")
    else:
        print(f"❌ 실패: {data}")

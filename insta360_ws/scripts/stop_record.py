#!/usr/bin/env python3
"""녹화 중지"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from insta360 import Insta360Camera

print("⏹️ 녹화 중지")
with Insta360Camera() as cam:
    print(f"✅ 연결: {cam.serial}")
    data = cam._send_command('camera._stopRecording')
    if data.get('state') == 'done':
        print("✅ 녹화 중지됨!")
        seq = data.get('sequence')
        if seq:
            print("⏳ 결과 대기...")
            result = cam.wait_for_result(seq, timeout=60)
            if result:
                print(f"📁 저장됨: {result}")
    else:
        print(f"⚠️ 결과: {data}")

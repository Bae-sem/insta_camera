#!/usr/bin/env python3
"""미리보기 중지"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from insta360 import Insta360Camera

print("⏹️ 미리보기 중지")
with Insta360Camera() as cam:
    print(f"✅ 연결: {cam.serial}")
    if cam.stop_preview():
        print("✅ 미리보기 중지됨!")
    else:
        print("⚠️ 이미 중지되어 있거나 실패")

#!/usr/bin/env python3
"""
파일 목록 조회

사용법:
    python3 list_files.py                    # SD 카드 파일 목록
    python3 list_files.py /mnt/sdcard/VID_*  # 특정 경로
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from insta360 import Insta360Camera


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "/mnt/sdcard"
    
    print("=" * 50)
    print(f"📁 파일 목록: {path}")
    print("=" * 50)
    
    try:
        with Insta360Camera() as cam:
            print(f"✅ 연결됨: {cam.serial}")
            
            print(f"\n📋 파일 목록 요청...")
            seq = cam.list_files(path)
            
            print(f"⏳ 결과 대기 중... (seq: {seq})")
            result = cam.wait_for_result(seq, timeout=30)
            
            if result:
                files = result.get('entries', result.get('files', []))
                print(f"\n📁 {len(files) if isinstance(files, list) else '?'}개 항목:")
                
                if isinstance(files, list):
                    for f in files[:20]:  # 최대 20개만 표시
                        if isinstance(f, dict):
                            print(f"   {f.get('name', f)}")
                        else:
                            print(f"   {f}")
                    if len(files) > 20:
                        print(f"   ... 외 {len(files)-20}개")
                else:
                    print(f"   결과: {result}")
            else:
                print("⚠️ 타임아웃")
                
    except Exception as e:
        print(f"❌ 오류: {e}")


if __name__ == "__main__":
    main()

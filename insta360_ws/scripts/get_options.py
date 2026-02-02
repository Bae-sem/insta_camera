#!/usr/bin/env python3
"""
설정 가능한 옵션 조회/설정

사용법:
    python3 get_options.py                    # 설정 가능한 옵션 조회
    python3 get_options.py stabilization      # 특정 옵션 조회
    python3 get_options.py stabilization true # 옵션 설정
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from insta360 import Insta360Camera


# 설정 가능한 옵션 목록 (API 테스트로 확인됨)
SETTABLE_OPTIONS = {
    "stabilization": {
        "description": "흔들림 보정 (FlowState)",
        "type": "bool",
        "values": "true / false"
    },
    "audio_gain": {
        "description": "오디오 게인 (마이크 볼륨)",
        "type": "int",
        "values": "0 ~ 127 (기본: 64)"
    },
    "flicker": {
        "description": "안티플리커 (형광등 깜빡임 방지)",
        "type": "int",
        "values": "0=Off, 1=50Hz, 2=60Hz"
    },
}


def main():
    print("=" * 50)
    print("⚙️ Insta360 Pro 2 설정 옵션")
    print("=" * 50)
    
    try:
        with Insta360Camera() as cam:
            print(f"✅ 연결됨: {cam.serial}\n")
            
            if len(sys.argv) == 1:
                # 모든 설정 가능한 옵션 조회
                print("📋 설정 가능한 옵션:")
                print("-" * 40)
                for opt, info in SETTABLE_OPTIONS.items():
                    try:
                        val = cam.get_option(opt)
                        print(f"\n   {opt}")
                        print(f"      설명: {info['description']}")
                        print(f"      현재값: {val}")
                        print(f"      가능한 값: {info['values']}")
                    except:
                        print(f"\n   {opt}")
                        print(f"      설명: {info['description']}")
                        print(f"      현재값: (조회 불가)")
                
                print("\n" + "-" * 40)
                print("💡 사용법:")
                print("   조회: python3 get_options.py [옵션명]")
                print("   설정: python3 get_options.py [옵션명] [값]")
                print("   예시: python3 get_options.py audio_gain 80")
                print()
                        
            elif len(sys.argv) == 2:
                # 특정 옵션 조회
                opt = sys.argv[1]
                
                if opt not in SETTABLE_OPTIONS:
                    print(f"⚠️ '{opt}'은(는) 알려진 설정 옵션이 아닙니다.")
                    print(f"   사용 가능한 옵션: {', '.join(SETTABLE_OPTIONS.keys())}")
                    return
                
                info = SETTABLE_OPTIONS[opt]
                try:
                    val = cam.get_option(opt)
                    print(f"📋 {opt}")
                    print(f"   설명: {info['description']}")
                    print(f"   현재값: {val}")
                    print(f"   가능한 값: {info['values']}")
                except Exception as e:
                    print(f"❌ {opt} 조회 실패: {e}")
                    
            elif len(sys.argv) == 3:
                # 옵션 설정
                opt = sys.argv[1]
                val_str = sys.argv[2]
                
                if opt not in SETTABLE_OPTIONS:
                    print(f"⚠️ '{opt}'은(는) 알려진 설정 옵션이 아닙니다.")
                    print(f"   사용 가능한 옵션: {', '.join(SETTABLE_OPTIONS.keys())}")
                    return
                
                # 값 변환
                if val_str.lower() == 'true':
                    val = True
                elif val_str.lower() == 'false':
                    val = False
                elif val_str.lstrip('-').isdigit():
                    val = int(val_str)
                else:
                    val = val_str
                
                info = SETTABLE_OPTIONS[opt]
                print(f"⚙️ 설정: {opt}")
                print(f"   설명: {info['description']}")
                print(f"   변경: → {val}")
                
                if cam.set_option(opt, val):
                    # 변경 후 확인
                    new_val = cam.get_option(opt)
                    print(f"   결과: {new_val}")
                    print("✅ 설정 완료!")
                else:
                    print("❌ 설정 실패")
            else:
                print("사용법:")
                print("  python3 get_options.py                    # 모든 옵션 조회")
                print("  python3 get_options.py stabilization      # 특정 옵션 조회")
                print("  python3 get_options.py stabilization true # 옵션 설정")
                
    except Exception as e:
        print(f"❌ 오류: {e}")


if __name__ == "__main__":
    main()

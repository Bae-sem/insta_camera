#!/usr/bin/env python3
"""
카메라 상태 정보 조회 (읽기 전용)

사용법:
    python3 camera_info.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from insta360 import Insta360Camera


def main():
    print("=" * 50)
    print("📷 Insta360 Pro 2 카메라 상태")
    print("=" * 50)
    
    try:
        with Insta360Camera() as cam:
            print(f"\n✅ 연결됨")
            print(f"   모델: {cam.model}")
            print(f"   시리얼: {cam.serial}")
            print(f"   버전: {cam.version}")
            
            # State 전체 조회
            state = cam.get_state()
            state_data = state.get('state', {})
            
            # 배터리 정보
            battery = state_data.get('_battery', {})
            if battery:
                print("\n🔋 배터리:")
                print(f"   잔량: {battery.get('battery_level', 0)}%")
                print(f"   충전중: {'예' if battery.get('battery_charge') else '아니오'}")
            
            # 시스템 온도
            sys_temp = state_data.get('_sys_temp', {})
            if sys_temp:
                print("\n🌡️ 시스템 온도:")
                print(f"   배터리: {sys_temp.get('bat_temp', 0)}°C")
                print(f"   메인보드: {sys_temp.get('nv_temp', 0)}°C")
                module_temp = sys_temp.get('module_temp', 0)
                if module_temp < 500:  # 1000은 센서 없음 표시
                    print(f"   모듈: {module_temp}°C")
            
            # GPS 상태
            gps_state = state_data.get('_gps_state')
            if gps_state is not None:
                gps_status = {0: 'No device', 1: 'No location', 2: '2D Fix', 3: '3D Fix'}
                print(f"\n📍 GPS: {gps_status.get(gps_state, 'Unknown')}")
            
            # 카메라 상태
            cam_state = state_data.get('_cam_state')
            if cam_state is not None:
                states = {
                    0: "대기",
                    1: "녹화중",
                    2: "라이브중",
                    4: "프리뷰중"
                }
                print(f"\n📷 상태: {states.get(cam_state, f'Unknown ({cam_state})')}")
            
            # 마이크 정보
            snd_state = state_data.get('_snd_state', {})
            if snd_state:
                mic_types = {0: 'None', 1: 'Built-in', 2: '3.5mm', 3: 'USB', -1: 'Unknown'}
                print("\n🎤 마이크:")
                print(f"   장치명: {snd_state.get('dev_name', 'N/A')}")
                print(f"   타입: {mic_types.get(snd_state.get('type', -1), 'Unknown')}")
                print(f"   공간음향: {'예' if snd_state.get('is_spatial') else '아니오'}")
            else:
                print("\n🎤 마이크: 미연결")
            
            # 저장 공간
            ext_dev = state_data.get('_external_dev', {})
            entries = ext_dev.get('entries', [])
            if entries:
                print(f"\n💾 저장공간:")
                print(f"   기본 경로: {ext_dev.get('save_path', 'N/A')}")
                for entry in entries:
                    name = entry.get('name', 'Unknown')
                    idx = entry.get('index', 0)
                    free = entry.get('free', 0)
                    total = entry.get('total', 1)
                    mount_type = entry.get('mounttype', 'unknown')
                    pct = 100 * free / total if total > 0 else 0
                    status = "✅" if entry.get('test') else "❌"
                    print(f"   [{idx}] {name}: {free:.0f}/{total:.0f} MB ({pct:.1f}% 여유) {status}")
            
            # 녹화/라이브 시간 정보
            left_info = state_data.get('_left_info', {})
            rec_sec = left_info.get('_rec_sec', 0)
            live_sec = left_info.get('_live_rec_sec', 0)
            if rec_sec > 0 or live_sec > 0:
                print("\n⏱️ 현재 작업:")
                if rec_sec > 0:
                    print(f"   녹화 경과: {rec_sec}초")
                if live_sec > 0:
                    print(f"   라이브 경과: {live_sec}초")
            
            print()
                
    except Exception as e:
        print(f"❌ 오류: {e}")


if __name__ == "__main__":
    main()

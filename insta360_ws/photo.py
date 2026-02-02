import requests
import time
import os
import json

# === 설정 ===
CAMERA_IP = "192.168.1.188"
PORT = "20000"
SAVE_DIR = "./photos"

# === URL ===
EXECUTE_URL = f"http://{CAMERA_IP}:{PORT}/osc/commands/execute"
STATE_URL = f"http://{CAMERA_IP}:{PORT}/osc/state"

# 기본 헤더
HEADERS = {"Content-Type": "application/json; charset=utf-8"}


def send_state(auth_headers):
    """State 폴링 - 하트비트 유지 및 완료된 비동기 작업 ID 확인
    
    문서: POST /osc/state, Fingerprint 헤더 필요
    """
    try:
        # POST 요청, 빈 body로 전송
        resp = requests.post(STATE_URL, json={}, headers=auth_headers, timeout=5)
        return resp.json()
    except Exception as e:
        print(f"   [State 폴링 실패: {e}]")
        return {}


def get_result(auth_headers, sequence_id):
    """_getResult 호출"""
    try:
        result_payload = {
            "name": "camera._getResult",
            "parameters": {
                "list_ids": [sequence_id]
            }
        }
        res_resp = requests.post(EXECUTE_URL, json=result_payload, headers=auth_headers, timeout=10)
        return res_resp.json()
    except Exception as e:
        print(f"   [getResult 실패: {e}]")
        return {}


def main():
    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)

    fingerprint = None
    auth_headers = None
    
    try:
        # ==========================================
        # 1. 연결 (Connect)
        # ==========================================
        print(f"🔌 카메라({CAMERA_IP})에 연결 시도...")
        
        connect_payload = {
            "name": "camera._connect",
            "parameters": {
                "hw_time": time.strftime("%m%d%H%M%Y.%S"),
                "time_zone": "GMT+09:00"
            }
        }
        resp = requests.post(EXECUTE_URL, json=connect_payload, headers=HEADERS, timeout=10)
        data = resp.json()
        print(f"   [DEBUG] Connect 응답: {json.dumps(data, indent=2)}")

        if data.get('state') != 'done':
            print(f"❌ 연결 실패: {json.dumps(data, indent=2)}")
            return

        # Fingerprint 추출
        results = data.get('results', {})
        fingerprint = results.get('Fingerprint')
        print(f"✅ 연결 성공! (Fingerprint: {fingerprint})")

        # ★ 중요: Fingerprint를 헤더에 추가
        auth_headers = HEADERS.copy()
        auth_headers["Fingerprint"] = fingerprint

        # ==========================================
        # 1.5 State 폴링 테스트 (연결 확인)
        # ==========================================
        print("🔍 State 폴링 테스트...")
        state_resp = send_state(auth_headers)
        print(f"   [DEBUG] State 테스트: {json.dumps(state_resp, indent=2)}")
        
        if state_resp.get('state') == 'exception':
            print("⚠️ State 폴링 실패 - 연결 유지에 문제가 있을 수 있음")

        # ==========================================
        # 2. 촬영 요청 (_takePicture)
        # ==========================================
        print("📸 촬영 요청 중...")

        take_payload = {
            "name": "camera._takePicture",
            "parameters": {
                "origin": {
                    "mime": "jpeg",
                    "width": 4000,
                    "height": 3000,
                    "saveOrigin": True,
                    "storage_loc": 0
                },
                "stiching": {
                    "mode": "pano",
                    "mime": "jpeg",
                    "width": 7680,
                    "height": 3840,
                    "map": "equirectangular",
                    "algorithm": "normal"
                },
                "delay": 0
            }
        }

        resp = requests.post(EXECUTE_URL, json=take_payload, headers=auth_headers, timeout=60)
        data = resp.json()
        print(f"   [DEBUG] takePicture 응답: {json.dumps(data, indent=2)}")

        sequence_id = data.get('sequence')
        
        if data.get('state') != 'done' or not sequence_id:
            print(f"❌ 촬영 요청 실패")
            disconnect(auth_headers)
            return
        
        print(f"🎫 작업 티켓: Sequence ID = {sequence_id}")

        # ==========================================
        # 3. 결과 대기 (_getResult 반복 호출)
        # ==========================================
        print("⏳ 결과 대기 중... (최대 120초)")
        
        file_url = None
        
        for i in range(120):
            time.sleep(1)
            
            # 매 초마다 state 폴링 (하트비트) - 오류 무시
            send_state(auth_headers)
            
            # 3초마다 getResult 확인
            if i > 0 and i % 3 == 0:
                res_data = get_result(auth_headers, sequence_id)
                
                # 디버깅 (처음 5번)
                if i <= 15:
                    print(f"   [{i}s] getResult: {json.dumps(res_data, indent=2)}")
                else:
                    print(f"   [{i}s] 확인 중...")
                
                # 에러 체크
                if res_data.get('state') == 'exception':
                    error = res_data.get('error', {})
                    if error.get('code') == 'disabledCommand':
                        print(f"   ⚠️ 연결 끊김 감지, 재연결 시도...")
                        # 재연결 시도
                        resp = requests.post(EXECUTE_URL, json=connect_payload, headers=HEADERS, timeout=10)
                        conn_data = resp.json()
                        if conn_data.get('state') == 'done':
                            fingerprint = conn_data.get('results', {}).get('Fingerprint')
                            auth_headers["Fingerprint"] = fingerprint
                            print(f"   ✅ 재연결 성공! (새 Fingerprint: {fingerprint})")
                        continue
                
                # 결과 파싱
                res_array = res_data.get('results', {}).get('res_array', [])
                for item in res_array:
                    if item.get('id') == sequence_id:
                        inner = item.get('results', {})
                        task_state = inner.get('state')
                        
                        if task_state == 'done':
                            final_results = inner.get('results', {})
                            file_url = final_results.get('_picUrl')
                            print(f"✅ 완료! URL: {file_url}")
                            break
                        elif task_state == 'error':
                            print(f"❌ 작업 실패: {json.dumps(inner, indent=2)}")
                            disconnect(auth_headers)
                            return
                
                if file_url:
                    break
            else:
                if i % 10 == 0:
                    print(f"   [{i}s] 대기 중...")

        # ==========================================
        # 4. 다운로드
        # ==========================================
        if file_url:
            # 카메라 내부 경로를 HTTP URL로 변환
            # 문서: http://{camera_ip}:8000/{fileuri}
            if file_url.startswith('/'):
                base_url = f"http://{CAMERA_IP}:8000{file_url}"
            else:
                base_url = f"http://{CAMERA_IP}:8000/{file_url}"
            
            print(f"📂 결과 경로: {base_url}")
            
            try:
                # 디렉토리 인덱스 가져오기
                index_resp = requests.get(base_url, timeout=10)
                index_html = index_resp.text
                
                # HTML에서 파일 링크 파싱 (href="filename")
                import re
                files = re.findall(r'href="([^"]+\.(jpg|jpeg|JPG|JPEG))"', index_html)
                
                if files:
                    print(f"📁 발견된 이미지 파일 {len(files)}개:")
                    for filename, _ in files:
                        print(f"   - {filename}")
                    
                    # 각 이미지 다운로드
                    for filename, _ in files:
                        download_url = f"{base_url}/{filename}"
                        save_path = os.path.join(SAVE_DIR, filename)
                        print(f"⬇️ 다운로드: {download_url}")
                        
                        content = requests.get(download_url, timeout=120).content
                        with open(save_path, 'wb') as f:
                            f.write(content)
                        print(f"   💾 저장: {save_path} ({len(content):,} bytes)")
                    
                    print(f"\n✅ 총 {len(files)}개 이미지 저장 완료!")
                else:
                    # 파일 목록이 없으면 직접 다운로드 시도
                    print("⚠️ 이미지 파일 목록을 찾지 못함, 직접 다운로드 시도...")
                    filename = file_url.split('/')[-1] + ".jpg"
                    download_url = base_url + ".jpg"
                    save_path = os.path.join(SAVE_DIR, filename)
                    
                    content = requests.get(download_url, timeout=120).content
                    with open(save_path, 'wb') as f:
                        f.write(content)
                    print(f"💾 저장: {save_path} ({len(content):,} bytes)")
                    
            except Exception as e:
                print(f"❌ 다운로드 실패: {e}")
        else:
            print("⚠️ 120초 내에 결과를 받지 못했습니다.")

        # 5. 연결 해제
        disconnect(auth_headers)

    except Exception as e:
        print(f"\n❌ 에러: {e}")
        import traceback
        traceback.print_exc()
        if auth_headers:
            disconnect(auth_headers)


def disconnect(headers):
    print("🔌 연결 해제 중...")
    try:
        requests.post(EXECUTE_URL, json={
            "name": "camera._disconnect",
            "parameters": {}
        }, headers=headers, timeout=5)
        print("👋 종료")
    except:
        pass


if __name__ == "__main__":
    main()
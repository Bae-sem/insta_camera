"""
Insta360 Pro 2 Camera Controller

카메라 연결, 촬영, 녹화, 라이브, 설정 등 모든 기능을 제공하는 클래스
"""

import time
import json
import requests
from typing import Optional, Dict, List, Any, Union

from . import config
from . import utils


class Insta360Camera:
    """Insta360 Pro 2 카메라 컨트롤러"""
    
    def __init__(self, ip: str = None, command_port: int = None, file_port: int = None):
        """
        카메라 초기화
        
        Args:
            ip: 카메라 IP 주소 (기본값: config.CAMERA_IP)
            command_port: 명령 포트 (기본값: config.COMMAND_PORT)
            file_port: 파일 서버 포트 (기본값: config.FILE_PORT)
        """
        self.ip = ip or config.CAMERA_IP
        self.command_port = command_port or config.COMMAND_PORT
        self.file_port = file_port or config.FILE_PORT
        
        self.execute_url = f"http://{self.ip}:{self.command_port}/osc/commands/execute"
        self.state_url = f"http://{self.ip}:{self.command_port}/osc/state"
        self.file_base_url = f"http://{self.ip}:{self.file_port}"
        
        self.fingerprint: Optional[str] = None
        self.connected = False
        self._headers = config.DEFAULT_HEADERS.copy()
        
        # 카메라 정보 (연결 시 설정됨)
        self.model: Optional[str] = None
        self.version: Optional[str] = None
        self.serial: Optional[str] = None
    
    @property
    def auth_headers(self) -> Dict[str, str]:
        """인증 헤더 반환 (Fingerprint 포함)"""
        headers = self._headers.copy()
        if self.fingerprint:
            headers["Fingerprint"] = self.fingerprint
        return headers
    
    def _send_command(self, name: str, parameters: Dict = None, timeout: int = 10) -> Dict:
        """API 명령 전송 헬퍼"""
        payload = {"name": name}
        if parameters:
            payload["parameters"] = parameters
        
        resp = requests.post(self.execute_url, json=payload, headers=self.auth_headers, timeout=timeout)
        return resp.json()
    
    # =========================================
    # 연결 관리
    # =========================================
    
    def connect(self, timezone: str = "GMT+09:00") -> Dict[str, Any]:
        """
        카메라 연결
        
        Returns:
            연결 응답 (카메라 정보 포함)
        """
        payload = {
            "name": "camera._connect",
            "parameters": {
                "hw_time": time.strftime("%m%d%H%M%Y.%S"),
                "time_zone": timezone
            }
        }
        
        resp = requests.post(self.execute_url, json=payload, headers=self._headers, timeout=config.CONNECT_TIMEOUT)
        data = resp.json()
        
        if data.get('state') != 'done':
            error = data.get('error', {})
            raise ConnectionError(f"연결 실패: {error.get('description', data)}")
        
        results = data.get('results', {})
        self.fingerprint = results.get('Fingerprint')
        self.model = data.get('machine', 'unknown')
        self.connected = True
        
        # 시스템 정보 저장
        sys_info = results.get('sys_info', {})
        self.serial = sys_info.get('sn')
        self.version = results.get('last_info', {}).get('version')
        
        return data
    
    def disconnect(self) -> bool:
        """카메라 연결 해제"""
        try:
            self._send_command("camera._disconnect", timeout=5)
            self.connected = False
            self.fingerprint = None
            return True
        except:
            return False
    
    def reconnect(self) -> bool:
        """재연결"""
        try:
            self.connect()
            return True
        except:
            return False
    
    # =========================================
    # 상태 조회
    # =========================================
    
    def get_state(self) -> Dict[str, Any]:
        """카메라 상태 조회 (하트비트 역할도 함)"""
        try:
            resp = requests.post(self.state_url, json={}, headers=self.auth_headers, timeout=config.STATE_TIMEOUT)
            return resp.json()
        except Exception as e:
            return {"error": str(e)}
    
    def get_finished_task_ids(self) -> List[int]:
        """완료된 비동기 작업 ID 목록"""
        state = self.get_state()
        return state.get('state', {}).get('_idRes', [])
    
    def get_battery(self) -> Dict[str, Any]:
        """배터리 상태 조회"""
        state = self.get_state()
        return state.get('state', {}).get('_battery', {})
    
    def get_storage_info(self) -> Dict[str, Any]:
        """저장 공간 정보 조회"""
        state = self.get_state()
        return state.get('state', {}).get('_external_dev', {})
    
    # =========================================
    # 옵션 조회/설정
    # =========================================
    
    def get_image_params(self) -> Dict[str, Any]:
        """
        이미지 파라미터 전체 조회
        
        Returns:
            이미지 파라미터 (aaa_mode, wb, iso, shutter, brightness 등)
        """
        data = self._send_command("camera._getImageParam")
        if data.get('state') == 'done':
            return data.get('results', {})
        raise RuntimeError(f"이미지 파라미터 조회 실패: {data}")
    
    def get_option(self, property_name: str) -> Any:
        """
        특정 옵션 조회
        
        Args:
            property_name: 옵션 이름
            
        Returns:
            옵션 값
        """
        data = self._send_command("camera._getOptions", {"property": property_name})
        if data.get('state') == 'done':
            return data.get('results', {}).get('value')
        raise RuntimeError(f"옵션 조회 실패: {data}")
    
    def set_option(self, property_name: str, value: Any) -> bool:
        """
        옵션 설정
        
        Args:
            property_name: 옵션 이름
            value: 설정할 값
            
        Returns:
            성공 여부
        """
        data = self._send_command("camera._setOptions", {"property": property_name, "value": value})
        return data.get('state') == 'done'
    
    def set_options(self, options: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        여러 옵션 일괄 설정
        
        Args:
            options: [{"property": "name", "value": value}, ...]
            
        Returns:
            응답 데이터
        """
        payload = {"name": "camera._setOptions", "parameters": options}
        resp = requests.post(self.execute_url, json=payload, headers=self.auth_headers, timeout=10)
        return resp.json()
    
    # =========================================
    # 비동기 작업 처리
    # =========================================
    
    def get_result(self, sequence_id: int) -> Dict[str, Any]:
        """비동기 작업 결과 조회"""
        return self._send_command("camera._getResult", {"list_ids": [sequence_id]})
    
    def wait_for_result(self, sequence_id: int, timeout: int = 120, 
                        poll_interval: int = 3, verbose: bool = True) -> Optional[Dict]:
        """
        비동기 작업 완료 대기 및 결과 반환
        
        Args:
            sequence_id: 작업 시퀀스 ID
            timeout: 최대 대기 시간 (초)
            poll_interval: 결과 조회 간격 (초)
            verbose: 진행 상황 출력
            
        Returns:
            작업 결과 또는 None
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            time.sleep(1)
            self.get_state()  # 하트비트
            elapsed = int(time.time() - start_time)
            
            if elapsed > 0 and elapsed % poll_interval == 0:
                if verbose:
                    print(f"   [{elapsed}s] 결과 확인 중...")
                
                res_data = self.get_result(sequence_id)
                
                # 연결 끊김 처리
                if res_data.get('state') == 'exception':
                    error = res_data.get('error', {})
                    if error.get('code') == 'disabledCommand':
                        if verbose:
                            print("   ⚠️ 연결 끊김, 재연결...")
                        if self.reconnect() and verbose:
                            print("   ✅ 재연결 성공!")
                        continue
                
                # 결과 파싱
                res_array = res_data.get('results', {}).get('res_array', [])
                for item in res_array:
                    if item.get('id') == sequence_id:
                        inner = item.get('results', {})
                        if inner.get('state') == 'done':
                            return inner.get('results', {})
                        elif inner.get('state') == 'error':
                            raise RuntimeError(f"작업 실패: {inner}")
        
        return None
    
    # =========================================
    # 사진 촬영
    # =========================================
    
    def take_picture(self, settings: Dict = None) -> int:
        """
        사진 촬영 요청
        
        Args:
            settings: 촬영 설정 (None이면 기본값 사용)
            
        Returns:
            sequence_id (비동기 작업 ID)
        """
        photo_settings = settings or config.DEFAULT_PHOTO_SETTINGS
        data = self._send_command("camera._takePicture", photo_settings, timeout=config.COMMAND_TIMEOUT)
        
        if data.get('state') != 'done':
            raise RuntimeError(f"촬영 실패: {data}")
        
        sequence_id = data.get('sequence')
        if not sequence_id:
            raise RuntimeError("시퀀스 ID 없음")
        
        return sequence_id
    
    # =========================================
    # 동영상 녹화
    # =========================================
    
    def start_recording(self, settings: Dict = None) -> Dict[str, Any]:
        """
        녹화 시작
        
        Args:
            settings: 녹화 설정 (None이면 기본값 사용)
            
        Returns:
            응답 데이터
        """
        record_settings = settings or config.DEFAULT_RECORD_SETTINGS
        data = self._send_command("camera._startRecording", record_settings, timeout=config.COMMAND_TIMEOUT)
        
        if data.get('state') != 'done':
            raise RuntimeError(f"녹화 시작 실패: {data}")
        
        return data
    
    def stop_recording(self) -> int:
        """
        녹화 중지
        
        Returns:
            sequence_id (결과 조회용)
        """
        data = self._send_command("camera._stopRecording")
        
        if data.get('state') != 'done':
            raise RuntimeError(f"녹화 중지 실패: {data}")
        
        return data.get('sequence')
    
    # =========================================
    # 미리보기 (Preview)
    # =========================================
    
    def start_preview(self, settings: Dict = None) -> str:
        """
        미리보기 시작
        
        Args:
            settings: 프리뷰 설정 (None이면 기본값 사용)
            
        Returns:
            RTMP 프리뷰 URL
        """
        preview_settings = settings or config.DEFAULT_PREVIEW_SETTINGS
        data = self._send_command("camera._startPreview", preview_settings, timeout=config.COMMAND_TIMEOUT)
        
        if data.get('state') != 'done':
            raise RuntimeError(f"미리보기 시작 실패: {data}")
        
        return data.get('results', {}).get('_previewUrl')
    
    def stop_preview(self) -> bool:
        """미리보기 중지"""
        data = self._send_command("camera._stopPreview")
        return data.get('state') == 'done'
    
    # =========================================
    # 라이브 스트리밍
    # =========================================
    
    def start_live(self, settings: Dict = None) -> str:
        """
        라이브 스트리밍 시작
        
        Args:
            settings: 라이브 설정 (None이면 기본값 사용)
            
        Returns:
            라이브 URL
        """
        live_settings = settings or config.DEFAULT_LIVE_SETTINGS
        data = self._send_command("camera._startLive", live_settings, timeout=config.COMMAND_TIMEOUT)
        
        if data.get('state') != 'done':
            raise RuntimeError(f"라이브 시작 실패: {data}")
        
        return data.get('results', {}).get('_liveUrl')
    
    def stop_live(self) -> int:
        """
        라이브 중지
        
        Returns:
            sequence_id
        """
        data = self._send_command("camera._stopLive")
        return data.get('sequence')
    
    # =========================================
    # 파일 관리
    # =========================================
    
    def list_files(self, path: str = "/mnt/sdcard") -> int:
        """
        파일 목록 조회 (비동기)
        
        Args:
            path: 조회할 경로
            
        Returns:
            sequence_id (get_result로 결과 조회)
        """
        data = self._send_command("camera._listFiles", {"path": path})
        
        if data.get('state') != 'done':
            raise RuntimeError(f"파일 목록 조회 실패: {data}")
        
        return data.get('sequence')
    
    def download_photos(self, camera_path: str, save_dir: str = None, verbose: bool = True) -> List[str]:
        """카메라에서 사진 다운로드"""
        save_dir = save_dir or config.DEFAULT_SAVE_DIR
        utils.ensure_dir(save_dir)
        
        if camera_path.startswith('/'):
            base_url = f"{self.file_base_url}{camera_path}"
        else:
            base_url = f"{self.file_base_url}/{camera_path}"
        
        if verbose:
            print(f"📂 경로: {base_url}")
        
        index_resp = requests.get(base_url, timeout=10)
        files = utils.parse_image_files(index_resp.text)
        
        if not files:
            raise RuntimeError("이미지 없음")
        
        if verbose:
            print(f"📁 이미지: {len(files)}개")
        
        downloaded = []
        for filename in files:
            download_url = f"{base_url}/{filename}"
            save_path = f"{save_dir}/{filename}"
            
            if verbose:
                print(f"⬇️ {filename}")
            
            size = utils.download_file(download_url, save_path, config.DOWNLOAD_TIMEOUT)
            downloaded.append(save_path)
            
            if verbose:
                print(f"   💾 {utils.format_bytes(size)}")
        
        return downloaded
    
    # =========================================
    # 컨텍스트 매니저
    # =========================================
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
        return False
    
    def __repr__(self):
        status = "연결됨" if self.connected else "연결 안됨"
        return f"<Insta360Camera {self.model} @ {self.ip} ({status})>"

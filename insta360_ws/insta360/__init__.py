"""
Insta360 Pro 2 Camera Module

사용 예시:
    from insta360 import Insta360Camera
    
    # 방법 1: with 문 사용 (권장)
    with Insta360Camera() as camera:
        sequence_id = camera.take_picture()
        result = camera.wait_for_result(sequence_id)
        camera.download_photos(result['_picUrl'])
    
    # 방법 2: 직접 연결 관리
    camera = Insta360Camera(ip="192.168.1.188")
    camera.connect()
    # ... 작업 ...
    camera.disconnect()
"""

from .camera import Insta360Camera
from .config import (
    CAMERA_IP, 
    COMMAND_PORT, 
    FILE_PORT,
    DEFAULT_PHOTO_SETTINGS,
    DEFAULT_SAVE_DIR
)

__all__ = [
    'Insta360Camera',
    'CAMERA_IP',
    'COMMAND_PORT', 
    'FILE_PORT',
    'DEFAULT_PHOTO_SETTINGS',
    'DEFAULT_SAVE_DIR'
]

__version__ = "1.0.0"

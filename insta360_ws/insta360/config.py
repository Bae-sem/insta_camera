# Insta360 Pro 2 Camera Configuration

# =========================================
# 네트워크 설정
# =========================================
CAMERA_IP = "192.168.1.188"
COMMAND_PORT = 20000
FILE_PORT = 8000

# URL (자동 생성)
EXECUTE_URL = f"http://{CAMERA_IP}:{COMMAND_PORT}/osc/commands/execute"
STATE_URL = f"http://{CAMERA_IP}:{COMMAND_PORT}/osc/state"
FILE_BASE_URL = f"http://{CAMERA_IP}:{FILE_PORT}"

# 기본 헤더
DEFAULT_HEADERS = {"Content-Type": "application/json; charset=utf-8"}

# =========================================
# 타임아웃 설정 (초)
# =========================================
CONNECT_TIMEOUT = 10
COMMAND_TIMEOUT = 60
DOWNLOAD_TIMEOUT = 120
STATE_TIMEOUT = 5

# =========================================
# 저장 경로
# =========================================
DEFAULT_SAVE_DIR = "./photos"

# =========================================
# 사진 촬영 기본 설정
# =========================================
DEFAULT_PHOTO_SETTINGS = {
    "origin": {
        "mime": "jpeg",
        "width": 4000,
        "height": 3000,
        "saveOrigin": True,
        "storage_loc": 0  # 0: TF card, 1: Main storage
    },
    "stiching": {  # 공식 API 오타 유지
        "mode": "pano",
        "mime": "jpeg",
        "width": 7680,
        "height": 3840,
        "map": "equirectangular",
        "algorithm": "normal"  # "opticalFlow" | "normal"
    },
    "delay": 0
}

# =========================================
# 동영상 녹화 기본 설정
# =========================================
DEFAULT_RECORD_SETTINGS = {
    "origin": {
        "mime": "h264",
        "width": 3840,
        "height": 2880,
        "framerate": 30,
        "bitrate": 60000,  # Kbps
        "logMode": 0,
        "hdr": False,
        "saveOrigin": True,
        "storage_loc": 0
    },
    "stiching": {
        "mode": "pano",
        "mime": "h264",
        "width": 3840,
        "height": 1920,
        "framerate": 30,
        "bitrate": 30000
    },
    "audio": {
        "mime": "aac",
        "sampleFormat": "s16",
        "channelLayout": "stereo",
        "samplerate": 48000,
        "bitrate": 128
    }
}

# =========================================
# 미리보기 기본 설정
# =========================================
DEFAULT_PREVIEW_SETTINGS = {
    "origin": {
        "mime": "h264",
        "width": 1920,
        "height": 1440,
        "framerate": 30,
        "bitrate": 20480
    },
    "stiching": {
        "mode": "pano",
        "mime": "h264",
        "width": 3840,
        "height": 1920,
        "framerate": 30,
        "bitrate": 10240
    },
    "stabilization": True
}

# =========================================
# 라이브 스트리밍 기본 설정
# =========================================
DEFAULT_LIVE_SETTINGS = {
    "origin": {
        "mime": "h264",
        "width": 1920,
        "height": 1440,
        "framerate": 30,
        "bitrate": 20480,
        "logMode": 0,
        "saveOrigin": False
    },
    "stiching": {
        "mode": "pano",
        "mime": "h264",
        "width": 3840,
        "height": 1920,
        "framerate": 30,
        "bitrate": 10240,
        "map": "equirectangular",
        "_liveUrl": "rtmp://localhost/live/insta360",  # 수정 필요
        "liveOnHdmi": False,
        "fileSave": False
    },
    "audio": {
        "mime": "aac",
        "sampleFormat": "s16",
        "channelLayout": "stereo",
        "samplerate": 48000,
        "bitrate": 128
    }
}

# =========================================
# 이미지 파라미터 값 맵핑 (참조용)
# =========================================
AAA_MODES = {
    "manual": 0,
    "auto": 1,
    "wdr": 2,
    "shutter_priority": 3,
    "iso_priority": 4
}

WHITE_BALANCE = {
    "auto": 0,
    "2700K": 1,
    "3200K": 6,
    "4000K": 2,
    "5000K": 3,
    "6500K": 4,
    "7500K": 5
}

ISO_VALUES = {
    100: 1, 125: 2, 160: 3, 200: 4, 250: 5,
    320: 6, 400: 7, 500: 8, 640: 9, 800: 10,
    1000: 11, 1250: 12, 1600: 13, 2000: 14, 2500: 15,
    3200: 16, 4000: 17, 5000: 18, 6400: 19
}

SHUTTER_VALUES = {
    "2s": 1, "1s": 4, "1/2s": 7, "1/3s": 9, "1/4s": 10,
    "1/5s": 11, "1/8s": 13, "1/10s": 14, "1/15s": 16,
    "1/20s": 17, "1/25s": 18, "1/30s": 19, "1/40s": 20,
    "1/50s": 21, "1/60s": 22, "1/80s": 23, "1/100s": 24,
    "1/120s": 25, "1/160s": 26, "1/200s": 27, "1/240s": 28,
    "1/320s": 29, "1/400s": 30, "1/500s": 31, "1/640s": 32,
    "1/800s": 33, "1/1000s": 34, "1/1250s": 35, "1/1600s": 36,
    "1/2000s": 37, "1/2500s": 38, "1/3200s": 39, "1/4000s": 40,
    "1/5000s": 41, "1/6400s": 42, "1/8000s": 43
}

# 📷 Insta360 Pro 2 Python Controller

Insta360 Pro 2 카메라를 Python으로 제어하는 모듈입니다.

---

## 📁 프로젝트 구조

```
insta360_ws/
├── insta360/                 # 📦 코어 모듈
│   ├── camera.py             # Insta360Camera 클래스
│   ├── config.py             # 모든 설정값
│   └── utils.py              # 유틸리티 함수
├── scripts/                  # 🚀 실행 스크립트
│   ├── camera_info.py        # 카메라 상태 조회 (배터리, 온도 등)
│   ├── take_photo.py         # 사진 촬영
│   ├── start_record.py       # 녹화 시작
│   ├── stop_record.py        # 녹화 중지
│   ├── start_preview.py      # 미리보기 시작
│   ├── stop_preview.py       # 미리보기 중지
│   ├── get_options.py        # 설정 옵션 조회/변경 (stabilization 등)
│   ├── image_params.py       # 이미지 파라미터
│   └── list_files.py         # 파일 목록
├── photos/                   # 📸 다운로드된 사진
└── Docs/                     # 📚 API 문서
```

---

## 🚀 빠른 시작

### 1. 카메라 IP 설정

`insta360/config.py` 파일에서 카메라 IP 확인:

```python
CAMERA_IP = "192.168.1.188"  # 카메라 화면에서 확인
```

### 2. 스크립트 실행

```bash
# 카메라 정보 확인
python3 scripts/camera_info.py

# 사진 촬영
python3 scripts/take_photo.py

# 녹화 시작/중지
python3 scripts/start_record.py
python3 scripts/stop_record.py

# 미리보기 시작/중지
python3 scripts/start_preview.py
python3 scripts/stop_preview.py
```

---

## � 스크립트 상세 설명

### 📸 `take_photo.py` - 사진 촬영

```bash
python3 scripts/take_photo.py              # 기본 촬영
python3 scripts/take_photo.py -o ./my_dir  # 저장 경로 지정
python3 scripts/take_photo.py --pano-only  # 파노라마만 다운로드
```

**생성되는 파일:**
- `pano.jpg` - 7680x3840 스티칭된 파노라마 (메인 결과물)
- `origin_1~6.jpg` - 6개 렌즈 원본 fisheye 이미지
- `thumbnail.jpg` - 썸네일

---

### 🎬 `start_record.py` / `stop_record.py` - 녹화

```bash
python3 scripts/start_record.py  # 녹화 시작
# ... 원하는 만큼 녹화 ...
python3 scripts/stop_record.py   # 녹화 중지
```

녹화 파일은 카메라 SD 카드에 저장됩니다.

---

### 👁️ `start_preview.py` / `stop_preview.py` - 미리보기

```bash
python3 scripts/start_preview.py  # 스트림 시작 (터미널 유지 필요)
python3 scripts/stop_preview.py   # 중지
```

**스트림 시청 (다른 터미널에서):**

```bash
# 🚀 ffplay (권장 - 가장 빠름, ~0.2초 지연)
ffplay -fflags nobuffer -flags low_delay -framedrop rtmp://192.168.1.188/live/preview

# VLC (안정적, ~1초 지연)
vlc --avcodec-hw=none --vout=x11 --network-caching=1000 rtmp://192.168.1.188/live/preview
```

---

### 📷 `camera_info.py` - 카메라 상태 조회 (읽기 전용)

```bash
python3 scripts/camera_info.py
```

**표시되는 정보:**
- 🔋 배터리 (잔량, 충전 상태)
- 🌡️ 시스템 온도 (배터리, 메인보드)
- 📍 GPS 상태
- 📷 카메라 동작 상태 (대기/녹화중/라이브중)
- 🎤 마이크 연결 정보
- 💾 저장공간 (SD카드, TF카드 6개)

---

### ⚙️ `get_options.py` - 설정 옵션 조회/변경

```bash
python3 scripts/get_options.py                    # 설정 가능한 옵션 목록
python3 scripts/get_options.py stabilization      # 특정 옵션 조회
python3 scripts/get_options.py stabilization true # 옵션 변경
```

**설정 가능한 옵션:**
| 옵션            | 설명                            | 값                          |
| --------------- | ------------------------------- | --------------------------- |
| `stabilization` | 흔들림 보정 (FlowState)         | `true` / `false`            |
| `audio_gain`    | 오디오 게인 (마이크 볼륨)       | `0` ~ `127` (기본: 64)      |
| `flicker`       | 안티플리커 (형광등 깜빡임 방지) | `0`=Off, `1`=50Hz, `2`=60Hz |

> 💡 추가 옵션이 발견되면 `SETTABLE_OPTIONS`에 등록하여 사용

---

## ⚙️ config.py 설정 가이드

### 네트워크 설정

```python
CAMERA_IP = "192.168.1.188"   # 카메라 IP (카메라 화면에서 확인)
COMMAND_PORT = 20000          # API 포트 (고정)
FILE_PORT = 8000              # 파일 서버 포트 (고정)
```

### 타임아웃 설정

```python
CONNECT_TIMEOUT = 10    # 연결 타임아웃 (초)
COMMAND_TIMEOUT = 60    # 촬영 명령 타임아웃 (초)
DOWNLOAD_TIMEOUT = 120  # 파일 다운로드 타임아웃 (초)
STATE_TIMEOUT = 5       # 상태 폴링 타임아웃 (초)
```

### 사진 촬영 설정 (`DEFAULT_PHOTO_SETTINGS`)

```python
"origin": {
    "mime": "jpeg",        # 포맷: "jpeg" | "raw"
    "width": 4000,         # 단일 렌즈 해상도 (가로)
    "height": 3000,        # 단일 렌즈 해상도 (세로)
    "saveOrigin": True,    # 원본 fisheye 이미지 저장 여부
    "storage_loc": 0       # 저장 위치: 0=SD카드, 1=메인스토리지
}

"stiching": {
    "mode": "pano",              # 모드: "pano" | "3d_top_left" | "3d_top_right"
    "mime": "jpeg",              # 포맷
    "width": 7680,               # 스티칭 결과 해상도 (가로)
    "height": 3840,              # 스티칭 결과 해상도 (세로)
    "map": "equirectangular",    # 매핑: "equirectangular" | "cubemap"
    "algorithm": "normal"        # 알고리즘: "normal" | "opticalFlow" (고품질)
}

"delay": 0  # 촬영 딜레이 (초)
```

### 녹화 설정 (`DEFAULT_RECORD_SETTINGS`)

```python
"origin": {
    "mime": "h264",        # 코덱: "h264" | "h265"
    "width": 3840,         # 단일 렌즈 해상도
    "height": 2880,
    "framerate": 30,       # 프레임레이트: 30, 60, 120
    "bitrate": 60000,      # 비트레이트 (Kbps)
    "hdr": False,          # HDR 활성화
    "saveOrigin": True,    # 원본 저장
    "storage_loc": 0
}

"stiching": {
    "mode": "pano",
    "mime": "h264",
    "width": 3840,         # 최대 4K (4K 이하만 실시간 스티칭)
    "height": 1920,
    "framerate": 30,
    "bitrate": 30000
}
```

---

## 📊 해상도 가이드 (Pro 2)

| 원본 해상도      | 출력 해상도               | 실시간 스티칭 | 3D 지원 |  HDR  |
| ---------------- | ------------------------- | :-----------: | :-----: | :---: |
| 4000x3000 (사진) | 8000x4000 / 8000x8000(3D) |       ✓       |    ✓    |   ✗   |
| 3840x2880@30fps  | 7680x3840 / 7680x7680(3D) |       ✗       |    ✓    |   ✓   |
| 3840x2160@30fps  | 7680x3840                 |       ✓       |    ✗    |   ✗   |
| 1920x1440@30fps  | 3840x1920 / 3840x3840(3D) |       ✓       |    ✓    |   ✗   |
| 1920x1440@120fps | 3840x1920 / 3840x3840(3D) |       ✗       |    ✓    |   ✗   |

> **참고:** 실시간 스티칭은 최대 4K (3840x1920)까지만 지원

---

## 📸 이미지 파라미터 값

### 3A 모드 (`aaa_mode`)

| 값  | 모드                         |
| --- | ---------------------------- |
| 0   | Manual (수동)                |
| 1   | Auto (자동)                  |
| 2   | WDR                          |
| 3   | Shutter Priority (셔터 우선) |
| 4   | ISO Priority (ISO 우선)      |

### 화이트밸런스 (`wb`)

| 값  | 색온도 |
| --- | ------ |
| 0   | Auto   |
| 1   | 2700K  |
| 6   | 3200K  |
| 2   | 4000K  |
| 3   | 5000K  |
| 4   | 6500K  |
| 5   | 7500K  |

### ISO (`iso_value`)

| 값  | ISO  |
| --- | ---- |
| 1   | 100  |
| 4   | 200  |
| 7   | 400  |
| 10  | 800  |
| 13  | 1600 |
| 16  | 3200 |
| 19  | 6400 |

### 셔터 속도 (`shutter_value`)

| 값  | 속도    |
| --- | ------- |
| 1   | 2s      |
| 4   | 1s      |
| 19  | 1/30s   |
| 22  | 1/60s   |
| 25  | 1/120s  |
| 34  | 1/1000s |

---

## 💻 Python 코드에서 사용하기

### 기본 사용법

```python
from insta360 import Insta360Camera

# with 문 사용 (권장 - 자동 연결/해제)
with Insta360Camera() as cam:
    # 카메라 정보
    print(f"모델: {cam.model}")
    print(f"시리얼: {cam.serial}")
    
    # 사진 촬영
    seq = cam.take_picture()
    result = cam.wait_for_result(seq)
    cam.download_photos(result['_picUrl'], save_dir="./photos")
```

### 커스텀 설정으로 촬영

```python
from insta360 import Insta360Camera

custom_settings = {
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
        "algorithm": "opticalFlow"  # 고품질 스티칭
    },
    "delay": 3  # 3초 후 촬영
}

with Insta360Camera() as cam:
    seq = cam.take_picture(settings=custom_settings)
    result = cam.wait_for_result(seq)
    cam.download_photos(result['_picUrl'])
```

### 녹화

```python
import time
from insta360 import Insta360Camera

with Insta360Camera() as cam:
    cam.start_recording()
    time.sleep(10)  # 10초 녹화
    cam.stop_recording()
```

### 상태 조회

```python
with Insta360Camera() as cam:
    battery = cam.get_battery()
    storage = cam.get_storage_info()
    print(f"배터리: {battery['battery_level']}%")
```

---

## � API 메서드 목록

| 메서드                            | 설명                 |
| --------------------------------- | -------------------- |
| `connect()`                       | 카메라 연결          |
| `disconnect()`                    | 연결 해제            |
| `get_state()`                     | 상태 조회 (하트비트) |
| `get_battery()`                   | 배터리 정보          |
| `get_storage_info()`              | 저장공간 정보        |
| `get_image_params()`              | 이미지 파라미터      |
| `get_option(name)`                | 옵션 조회            |
| `set_option(name, value)`         | 옵션 설정            |
| `take_picture(settings)`          | 사진 촬영            |
| `start_recording(settings)`       | 녹화 시작            |
| `stop_recording()`                | 녹화 중지            |
| `start_preview(settings)`         | 미리보기 시작        |
| `stop_preview()`                  | 미리보기 중지        |
| `start_live(settings)`            | 라이브 시작          |
| `stop_live()`                     | 라이브 중지          |
| `list_files(path)`                | 파일 목록            |
| `download_photos(path, save_dir)` | 사진 다운로드        |

---

## ⚠️ 주의사항

1. **연결 유지**: 카메라는 10초간 통신이 없으면 연결을 끊음 → `get_state()` 호출로 하트비트 유지
2. **비동기 작업**: `take_picture`, `stop_recording` 등은 비동기 → `wait_for_result(seq)` 필요
3. **실시간 스티칭**: 최대 4K (3840x1920)까지만 지원
4. **스티칭 오타**: API에서 `stitching`이 아닌 `stiching` 사용 (공식 오타)
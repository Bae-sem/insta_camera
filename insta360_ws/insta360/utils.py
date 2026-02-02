# Insta360 Camera Utilities

import re
import os
import requests


def parse_image_files(html_content):
    """HTML 디렉토리 인덱스에서 이미지 파일 목록 추출"""
    files = re.findall(r'href="([^"]+\.(jpg|jpeg|JPG|JPEG))"', html_content)
    return [f[0] for f in files]


def ensure_dir(path):
    """디렉토리가 없으면 생성"""
    if not os.path.exists(path):
        os.makedirs(path)
    return path


def download_file(url, save_path, timeout=120):
    """파일 다운로드 및 저장"""
    content = requests.get(url, timeout=timeout).content
    with open(save_path, 'wb') as f:
        f.write(content)
    return len(content)


def format_bytes(size):
    """바이트를 읽기 쉬운 형식으로 변환"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"

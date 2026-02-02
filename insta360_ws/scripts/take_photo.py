#!/usr/bin/env python3
"""
사진 촬영 스크립트

사용법:
    python scripts/take_photo.py
    python scripts/take_photo.py --save-dir ./my_photos
    python scripts/take_photo.py --pano-only
"""

import argparse
import sys
import os

# 상위 디렉토리를 path에 추가 (모듈 import를 위해)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from insta360 import Insta360Camera, DEFAULT_SAVE_DIR


def take_photo(save_dir: str = None, pano_only: bool = False, verbose: bool = True):
    """
    사진 촬영 및 다운로드
    
    Args:
        save_dir: 저장 디렉토리
        pano_only: True면 파노라마 이미지만 다운로드
        verbose: 진행 상황 출력
    """
    save_dir = save_dir or DEFAULT_SAVE_DIR
    
    print("=" * 50)
    print("📷 Insta360 Pro 2 사진 촬영")
    print("=" * 50)
    
    try:
        # with 문을 사용하면 자동으로 연결/해제됨
        with Insta360Camera() as camera:
            print(f"✅ 카메라 연결됨 (Fingerprint: {camera.fingerprint})")
            
            # 사진 촬영
            print("\n📸 촬영 중...")
            sequence_id = camera.take_picture()
            print(f"🎫 작업 ID: {sequence_id}")
            
            # 결과 대기
            print("\n⏳ 결과 대기 중...")
            result = camera.wait_for_result(sequence_id, timeout=120, verbose=verbose)
            
            if not result:
                print("❌ 시간 초과")
                return
            
            pic_url = result.get('_picUrl')
            print(f"✅ 촬영 완료: {pic_url}")
            
            # 다운로드
            print(f"\n⬇️ 다운로드 시작 (저장 위치: {save_dir})")
            downloaded = camera.download_photos(pic_url, save_dir, verbose)
            
            # 파노라마만 필터링
            if pano_only:
                pano_files = [f for f in downloaded if 'pano' in f.lower()]
                print(f"\n✅ 파노라마 이미지: {pano_files}")
            else:
                print(f"\n✅ 총 {len(downloaded)}개 파일 다운로드 완료!")
                
    except ConnectionError as e:
        print(f"❌ 연결 오류: {e}")
    except RuntimeError as e:
        print(f"❌ 실행 오류: {e}")
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        import traceback
        traceback.print_exc()


def main():
    parser = argparse.ArgumentParser(description="Insta360 Pro 2 사진 촬영")
    parser.add_argument(
        "--save-dir", "-o",
        default=DEFAULT_SAVE_DIR,
        help=f"저장 디렉토리 (기본: {DEFAULT_SAVE_DIR})"
    )
    parser.add_argument(
        "--pano-only",
        action="store_true",
        help="파노라마 이미지만 다운로드"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="진행 상황 출력 최소화"
    )
    
    args = parser.parse_args()
    take_photo(
        save_dir=args.save_dir,
        pano_only=args.pano_only,
        verbose=not args.quiet
    )


if __name__ == "__main__":
    main()

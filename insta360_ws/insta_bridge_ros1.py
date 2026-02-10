#!/usr/bin/env python3
"""
Insta360 Pro 2 ROS 1 Bridge Node (With Compression)

ROS 1 (rospy) 환경에서 Insta360 카메라 스트림을 ROS 토픽으로 퍼블리시합니다.

토픽:
    - /insta360/image_raw (sensor_msgs/Image) -> 원본 (데이터 큼, 주의)
    - /insta360/image_raw/compressed (sensor_msgs/CompressedImage) -> 압축본 (rosbag 용)
    - /insta360/camera_info (sensor_msgs/CameraInfo)

사용법:
    rosrun insta360_ros insta_bridge_ros1.py
    또는
    python3 insta_bridge_ros1.py _ip:=192.168.1.188
"""

import rospy
from sensor_msgs.msg import Image, CameraInfo, CompressedImage # CompressedImage 추가
import cv2
from cv_bridge import CvBridge
import numpy as np
import time
import os
import subprocess
import re
import sys
import threading

# 상위 디렉토리를 path에 추가 (모듈 import를 위해)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Insta360 라이브러리 임포트
from insta360.camera import Insta360Camera
from insta360 import config

class Insta360BridgeROS1:
    """ROS 1 기반 Insta360 Bridge 노드"""
    
    # start_preview.py와 동일한 설정 적용
    PREVIEW_SETTINGS = {
        'origin': {'mime': 'h264', 'width': 1920, 'height': 1440, 'framerate': 30, 'bitrate': 20480},
        'stiching': {'mode': 'pano', 'mime': 'h264', 'width': 3840, 'height': 1920, 'framerate': 30, 'bitrate': 10240},
        'stabilization': True
    }

    def __init__(self):
        # ROS 노드 초기화
        rospy.init_node('insta360_bridge', anonymous=False)
        
        # RTSP 안정성을 위한 환경 변수 설정
        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;udp"
        
        # 파라미터 설정 (ROS 1 스타일)
        self.ip = rospy.get_param('~ip', config.CAMERA_IP)
        self.frame_id = rospy.get_param('~frame_id', 'insta360_link')
        extra_offset = rospy.get_param('~extra_latency_msec', 150) / 1000.0
        
        # 퍼블리셔 생성
        # 1. 원본 RAW 이미지 (기존 유지)
        self.image_pub = rospy.Publisher('~image_raw', Image, queue_size=10)
        # 2. 압축 이미지 (신규 추가 - rosbag 녹화용)
        self.compressed_pub = rospy.Publisher('~image_raw/compressed', CompressedImage, queue_size=10)
        # 3. 카메라 정보
        self.info_pub = rospy.Publisher('~camera_info', CameraInfo, queue_size=10)
        
        self.br = CvBridge()
        self.cam = None
        self.cap = None
        self.failure_count = 0
        
        # Heartbeat 관리
        self.alive = True
        self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop)
        self.heartbeat_thread.daemon = True
        
        # 스트림 시작 시간 기록
        self.stream_start_time = None
        
        # 1. 네트워크 지연(RTT) 측정 (Auto Latency)
        rtt_sec = self.measure_network_latency()
        self.latency_sec = (rtt_sec / 2.0) + extra_offset
        
        rospy.loginfo("=" * 50)
        rospy.loginfo(f"🚀 Auto Latency Calibration")
        rospy.loginfo(f"   - Network RTT (Ping): {rtt_sec*1000:.2f} ms")
        rospy.loginfo(f"   - TOTAL LATENCY: {self.latency_sec*1000:.2f} ms")
        rospy.loginfo("=" * 50)

        # 카메라 연결 및 스트림 시작
        self.init_camera()
        
        # 타이머 설정 (30 FPS) - 이미지 획득용
        self.timer = rospy.Timer(rospy.Duration(1.0/30.0), self.timer_callback)
        rospy.loginfo('Insta360 Bridge ROS1 Node has been started.')
        
        # 종료 시 정리
        rospy.on_shutdown(self.shutdown)

    def _heartbeat_loop(self):
        """별도 스레드에서 주기적으로 Heartbeat 전송"""
        while self.alive and not rospy.is_shutdown():
            try:
                if self.cam and self.cam.connected:
                    self.cam.get_state() 
            except Exception:
                pass
            time.sleep(3.0)

    def measure_network_latency(self):
        """카메라와의 Ping을 통해 RTT 측정"""
        try:
            # Ping 5회 수행
            result = subprocess.run(
                ['ping', '-c', '5', self.ip],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            match = re.search(r'min/avg/max/mdev = [\d\.]+/([\d\.]+)/', result.stdout)
            if match:
                avg_ms = float(match.group(1))
                return avg_ms / 1000.0
        except Exception as e:
            rospy.logwarn(f"Ping failed: {e}")
        
        return 0.001  # 실패 시 기본값 1ms

    def init_camera(self):
        """카메라 연결 및 스트림 URL 획득"""
        try:
            rospy.loginfo(f'Checking camera connection at {self.ip}...')
            self.cam = Insta360Camera(ip=self.ip)
            
            # 1. 카메라 연결
            try:
                self.cam.connect()
                rospy.loginfo(f'Connected to Insta360 Pro 2 (Serial: {self.cam.serial})')
                
                # 연결 성공 즉시 Heartbeat 스레드 시작
                if not self.heartbeat_thread.is_alive():
                    self.heartbeat_thread.start()
                    
            except Exception as e:
                rospy.logwarn(f'Connection warning (might be already connected): {e}')

            # 2. 프리뷰 시작
            self.rtsp_url = f"rtsp://{self.ip}/live/stitching"
            self.rtmp_url = f"rtmp://{self.ip}/live/preview"

            try:
                initial_url = self.cam.start_preview(self.PREVIEW_SETTINGS)
                rospy.loginfo(f'Received Preview URL: {initial_url}')
                
                if initial_url:
                    if "127.0.0.1" in initial_url:
                        initial_url = initial_url.replace("127.0.0.1", self.ip)
                    elif "localhost" in initial_url:
                        initial_url = initial_url.replace("localhost", self.ip)
                    
                    self.rtmp_url = initial_url
                    rospy.loginfo(f'Using corrected RTMP URL: {self.rtmp_url}')
            except Exception as e:
                rospy.logwarn(f'Could not start preview: {e}')

            # 스트림 안정화를 위한 대기 시간 증가
            rospy.loginfo("Waiting 5 seconds for stream to stabilize...")
            time.sleep(5.0)

            # 3. 스트림 연결 시도 (RTMP 우선 - 프리뷰 URL이 RTMP이므로)
            self.connect_stream(self.rtmp_url)

        except Exception as e:
            rospy.logerr(f'Camera initialization failed: {e}')


    def connect_stream(self, url):
        """스트림 연결 시도 (GStreamer 또는 FFmpeg)"""
        if self.cap is not None:
            self.cap.release()
            
        rospy.loginfo(f'Attempting to connect to stream: {url}')
        
        # RTMP의 경우 GStreamer 파이프라인 시도
        if 'rtmp' in url:
            gst_pipeline = (
                f'rtmpsrc location="{url}" ! '
                'flvdemux ! h264parse ! avdec_h264 ! '
                'videoconvert ! appsink'
            )
            rospy.loginfo(f'Trying GStreamer pipeline...')
            self.cap = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)
            
            if self.cap.isOpened():
                rospy.loginfo(f'Successfully opened stream via GStreamer')
                self.stream_url = url
                self.failure_count = 0
                self.stream_start_time = rospy.Time.now()
                return
            else:
                rospy.logwarn('GStreamer failed, trying FFmpeg...')
        
        # 일반 FFmpeg 방식
        self.cap = cv2.VideoCapture(url)
        self.stream_url = url
        
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        if self.cap.isOpened():
            rospy.loginfo(f'Successfully opened video stream: {url}')
            self.failure_count = 0
            # 스트림 시작 시각 기준점 기록
            self.stream_start_time = rospy.Time.now()
        else:
            rospy.logerr(f'Failed to open stream: {url}')

    def get_equirectangular_camera_info(self, width, height, timestamp):
        """Equirectangular (파노라마) 모델용 CameraInfo 생성"""
        info_msg = CameraInfo()
        info_msg.header.stamp = timestamp
        info_msg.header.frame_id = self.frame_id
        info_msg.height = height
        info_msg.width = width
        
        # Equirectangular 모델 명시
        info_msg.distortion_model = "equirectangular"
        
        # Intrinsic Matrix (K) 계산
        fx = width / (2 * np.pi)
        fy = height / np.pi
        cx = width / 2.0
        cy = height / 2.0
        
        info_msg.K = [fx, 0.0, cx,
                      0.0, fy, cy,
                      0.0, 0.0, 1.0]
        
        # Distortion (D) - 스티칭된 이미지는 왜곡이 없다고 가정
        info_msg.D = [0.0, 0.0, 0.0, 0.0, 0.0]
        
        # Rectification (R) - 단위 행렬
        info_msg.R = [1.0, 0.0, 0.0,
                      0.0, 1.0, 0.0,
                      0.0, 0.0, 1.0]
                      
        # Projection (P)
        info_msg.P = [fx, 0.0, cx, 0.0,
                      0.0, fy, cy, 0.0,
                      0.0, 0.0, 1.0, 0.0]
                      
        return info_msg

    def timer_callback(self, event):
        """타이머 콜백: 프레임 읽기 및 퍼블리시"""
        if self.cap is None:
            return

        if not self.cap.isOpened():
            self.failure_count += 1
            if self.failure_count > 90:
                self.reconnect_strategy()
            return

        ret, frame = self.cap.read()
        if ret:
            self.failure_count = 0
            
            # 하드웨어 타임스탬프 활용 시도
            hw_msec = self.cap.get(cv2.CAP_PROP_POS_MSEC)
            
            if hw_msec > 0 and self.stream_start_time is not None:
                # 스트림 타임스탬프 사용
                elapsed_duration = rospy.Duration(secs=0, nsecs=int(hw_msec * 1_000_000))
                capture_time = self.stream_start_time + elapsed_duration
                
                # 미래 시간 체크
                now = rospy.Time.now()
                if capture_time > now:
                    capture_stamp = now
                else:
                    capture_stamp = capture_time
            else:
                # 타임스탬프가 없으면 현재 시간 사용
                capture_stamp = rospy.Time.now()

            # 1. Image 메시지 생성 (Raw) - 기존 유지
            img_msg = self.br.cv2_to_imgmsg(frame, encoding="bgr8")
            img_msg.header.stamp = capture_stamp
            img_msg.header.frame_id = self.frame_id
            self.image_pub.publish(img_msg)

            # 2. CompressedImage 메시지 생성 (JPEG) - rosbag 용
            # JPEG 압축 (퀄리티 90 정도로 설정, 화질 좋고 용량 작음)
            try:
                msg = CompressedImage()
                msg.header.stamp = capture_stamp
                msg.header.frame_id = self.frame_id
                msg.format = "jpeg"
                # cv2.imencode 리턴값: (success, encoded_image)
                success, encoded_img = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
                if success:
                    msg.data = encoded_img.tobytes()
                    self.compressed_pub.publish(msg)
            except Exception as e:
                rospy.logwarn(f"Compression failed: {e}")

            # 3. CameraInfo 메시지 생성
            info_msg = self.get_equirectangular_camera_info(
                frame.shape[1], frame.shape[0], capture_stamp
            )
            self.info_pub.publish(info_msg)
            
        else:
            self.failure_count += 1
            if self.failure_count % 30 == 0:
                rospy.logwarn(f'No frames received for {self.failure_count/30:.1f} seconds...')
            
            if self.failure_count > 90:
                rospy.logwarn('Stream dead. Triggering reconnection...')
                self.reconnect_strategy()

    def reconnect_strategy(self):
        """재연결 전략: RTSP <-> RTMP 전환"""
        self.failure_count = 0
        if 'rtsp' in self.stream_url:
            target = self.rtmp_url
        else:
            target = self.rtsp_url
            
        rospy.loginfo(f'Switching stream method from {self.stream_url} to {target}')
        self.connect_stream(target)

    def shutdown(self):
        """노드 종료 시 정리"""
        rospy.loginfo("Shutting down Insta360 Bridge...")
        self.alive = False
        try:
            if self.cap:
                self.cap.release()
            if self.cam:
                self.cam.stop_preview()
        except Exception as e:
            rospy.logwarn(f"Error during shutdown: {e}")

    def run(self):
        """메인 루프 실행"""
        rospy.spin()


def main():
    try:
        node = Insta360BridgeROS1()
        node.run()
    except rospy.ROSInterruptException:
        pass


if __name__ == '__main__':
    main()
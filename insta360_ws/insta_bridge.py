import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo
import cv2
from cv_bridge import CvBridge
import numpy as np
import time
import os
import subprocess
import re

# Insta360 라이브러리 임포트
from insta360.camera import Insta360Camera
from insta360 import config

class Insta360Bridge(Node):
    # start_preview.py와 동일한 설정 적용
    PREVIEW_SETTINGS = {
        'origin': {'mime': 'h264', 'width': 1920, 'height': 1440, 'framerate': 30, 'bitrate': 20480},
        'stiching': {'mode': 'pano', 'mime': 'h264', 'width': 3840, 'height': 1920, 'framerate': 30, 'bitrate': 10240},
        'stabilization': True
    }

    def __init__(self):
        super().__init__('insta360_bridge')
        
        # RTSP 안정성을 위한 환경 변수 설정
        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;udp"
        
        # 파라미터 설정
        self.declare_parameter('ip', config.CAMERA_IP)
        self.declare_parameter('frame_id', 'insta360_link')
        self.declare_parameter('extra_latency_msec', 150)
        
        self.ip = self.get_parameter('ip').value
        self.frame_id = self.get_parameter('frame_id').value
        extra_offset = self.get_parameter('extra_latency_msec').value / 1000.0
        
        # 1. 네트워크 지연(RTT) 측정 (Auto Latency)
        rtt_sec = self.measure_network_latency()
        
        # 2. 총 지연 시간 계산 (자동)
        # Total Latency = (RTT / 2) + Decoding/Buffering Delay (~200ms) + Extra Offset
        self.latency_sec = (rtt_sec / 2.0) + extra_offset
        
        self.get_logger().info("="*50)
        self.get_logger().info(f"🚀 Auto Latency Calibration")
        self.get_logger().info(f"   - Network RTT (Ping): {rtt_sec*1000:.2f} ms")
        self.get_logger().info(f"   - Decoding/Buffer Est: {extra_offset*1000:.2f} ms")
        self.get_logger().info(f"   - TOTAL LATENCY: {self.latency_sec*1000:.2f} ms")
        self.get_logger().info("="*50)
        
        # 퍼블리셔 생성 (토픽 이름: image, camera_info)
        self.image_pub = self.create_publisher(Image, 'image', 10)
        self.info_pub = self.create_publisher(CameraInfo, 'camera_info', 10)
        
        self.br = CvBridge()
        self.cam = None
        self.cap = None
        self.failure_count = 0 
        self.heartbeat_timer = 0
        
        # 카메라 연결 및 스트림 시작
        self.init_camera()
        
        # 타이머 설정 (30 FPS)
        self.timer = self.create_timer(1.0/30.0, self.timer_callback)
        self.get_logger().info('Insta360 Bridge Node has been started.')

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
            self.get_logger().warn(f"Ping failed: {e}")
        
        return 0.001 # 실패 시 기본값 1ms

    def init_camera(self):
        """카메라 연결 및 스트림 URL 획득"""
        try:
            self.get_logger().info(f'Checking camera connection at {self.ip}...')
            self.cam = Insta360Camera(ip=self.ip)
            
            # 1. 카메라 연결
            try:
                self.cam.connect()
                self.get_logger().info(f'Connected to Insta360 Pro 2 (Serial: {self.cam.serial})')
                # 시간 동기화 (선택 사항)
                # self.cam._send_command("camera._setOptions", {"property": "datetime", "value": time.strftime("%Y:%m:%d %H:%M:%S")})
            except Exception as e:
                self.get_logger().warn(f'Connection warning (might be already connected): {e}')

            # 2. 프리뷰 시작
            self.rtsp_url = f"rtsp://{self.ip}/live/stitching"
            self.rtmp_url = f"rtmp://{self.ip}/live/preview"

            try:
                initial_url = self.cam.start_preview(self.PREVIEW_SETTINGS)
                self.get_logger().info(f'Received Preview URL: {initial_url}')
                
                if initial_url:
                    if "127.0.0.1" in initial_url:
                        initial_url = initial_url.replace("127.0.0.1", self.ip)
                    elif "localhost" in initial_url:
                        initial_url = initial_url.replace("localhost", self.ip)
                    
                    self.rtmp_url = initial_url
                    self.get_logger().info(f'Using corrected RTMP URL: {self.rtmp_url}')
            except Exception as e:
                self.get_logger().warn(f'Could not start preview: {e}')

            self.get_logger().info("Waiting 2 seconds for stream to stabilize...")
            time.sleep(2.0)

            # 3. 스트림 연결 시도 (RTSP 우선으로 변경 - OpenCV 호환성)
            self.connect_stream(self.rtsp_url) 

        except Exception as e:
            self.get_logger().error(f'Camera initialization failed: {e}')

    def connect_stream(self, url):
        """스트림 연결 시도"""
        if self.cap is not None:
            self.cap.release()
            
        self.get_logger().info(f'Attempting to connect to stream: {url}')
        self.cap = cv2.VideoCapture(url)
        self.stream_url = url
        
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        if self.cap.isOpened():
             self.get_logger().info(f'Successfully opened video stream: {url}')
             self.failure_count = 0
             # 스트림 시작 시각 기준점 기록 (PC 시간)
             self.stream_start_time = self.get_clock().now()
        else:
             self.get_logger().error(f'Failed to open stream: {url}')

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
        # fx = width / 2pi, fy = height / pi
        fx = width / (2 * np.pi)
        fy = height / np.pi
        cx = width / 2.0
        cy = height / 2.0
        
        info_msg.k = [fx, 0.0, cx, 
                      0.0, fy, cy, 
                      0.0, 0.0, 1.0]
        
        # Distortion (D) - 스티칭된 이미지는 이론적으로 왜곡이 없다고(보정되었다고) 가정
        info_msg.d = [0.0, 0.0, 0.0, 0.0, 0.0]
        
        # Rectification (R) - 단위 행렬
        info_msg.r = [1.0, 0.0, 0.0, 
                      0.0, 1.0, 0.0, 
                      0.0, 0.0, 1.0]
                      
        # Projection (P) - K와 동일하게 설정
        info_msg.p = [fx, 0.0, cx, 0.0,
                      0.0, fy, cy, 0.0,
                      0.0, 0.0, 1.0, 0.0]
                      
        return info_msg

    def timer_callback(self):
        # Heartbeat: 3초(30프레임 * 3)마다 상태 조회
        self.heartbeat_timer += 1
        if self.heartbeat_timer >= 90:
            self.heartbeat_timer = 0
            try:
                if self.cam and self.cam.connected:
                    self.cam.get_state()
            except Exception:
                pass

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
            
            # [동기화 핵심] 하드웨어 타임스탬프 활용 시도
            hw_msec = self.cap.get(cv2.CAP_PROP_POS_MSEC)
            
            if hw_msec > 0:
                # 방법 1: 스트림 타임스탬프가 있다면 사용 (스트림 시작 시점 + 경과 시간)
                # 약간의 드리프트가 있을 수 있으나, 네트워크 지연보다는 훨씬 안정적임
                start_ns = self.stream_start_time.nanoseconds
                elapsed_ns = int(hw_msec * 1_000_000)
                
                # capture_time = 스트림연결시각(PC) + 프레임타임스탬프(Camera)
                # 단, 이것도 '연결 시점'의 딜레이는 보정 못함. 하지만 프레임 간격은 정확함.
                capture_time_ns = start_ns + elapsed_ns
                
                # 만약 현재 시간보다 미래라면? (말이 안됨 -> 단순 PC 시간 사용)
                now_ns = self.get_clock().now().nanoseconds
                if capture_time_ns > now_ns:
                     capture_msg = self.get_clock().now().to_msg() # Fallback
                else:
                     capture_msg = rclpy.time.Time(nanoseconds=capture_time_ns).to_msg()
            else:
                # 방법 2: 타임스탬프가 없으면 기존 방식 사용 (PC 시간 - 평균 지연)
                now_rcl = self.get_clock().now()
                # latency_duration = rclpy.duration.Duration(seconds=self.latency_sec) # Commented out as per instruction
                # capture_time = now_rcl - latency_duration # Commented out as per instruction
                # capture_msg = capture_time.to_msg() # Commented out as per instruction
                capture_msg = now_rcl.to_msg() # Fallback to current PC time if hardware timestamp is invalid

            # 1. Image 메시지 생성
            img_msg = self.br.cv2_to_imgmsg(frame, encoding="bgr8")
            img_msg.header.stamp = capture_msg
            img_msg.header.frame_id = self.frame_id
            
            # 2. CameraInfo 메시지 생성 (계산된 값 사용)
            info_msg = self.get_equirectangular_camera_info(
                frame.shape[1], frame.shape[0], capture_msg
            )
            
            self.image_pub.publish(img_msg)
            self.info_pub.publish(info_msg)
        else:
            self.failure_count += 1
            if self.failure_count % 30 == 0:
                self.get_logger().warn(f'No frames received for {self.failure_count/30:.1f} seconds...')
            
            if self.failure_count > 90:
                self.get_logger().warn('Stream dead. Triggering reconnection...')
                self.reconnect_strategy()

    def reconnect_strategy(self):
        """재연결 전략"""
        self.failure_count = 0
        # 현재 URL이 RTMP면 RTSP로, RTSP면 RTMP로 전환
        # (단순 문자열 포함 여부로 판단)
        if 'rtsp' in self.stream_url:
            target = self.rtmp_url
        else:
            target = self.rtsp_url
            
        self.get_logger().info(f'Switching stream method from {self.stream_url} to {target}')
        self.connect_stream(target)

    def destroy_node(self):
        try:
            if self.cap:
                self.cap.release()
            if self.cam:
                self.cam.stop_preview()
        except:
            pass
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = Insta360Bridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
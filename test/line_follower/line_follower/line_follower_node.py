#!/usr/bin/env python3
"""
巡线 + 红点停车 ROS2 节点

算法流程:
  1. 订阅相机图像，取图像下方 ROI 区域
  2. FOLLOW_LINE 状态: 灰度→二值化→找黑线质心→PD 控制转向
  3. 检测到红色像素超过阈值 → 切换到 STOP 状态
  4. STOP 状态: 发布零速度，停留指定时间后恢复巡线
  5. 恢复后有冷却期，防止同一个红点反复触发
"""

import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Image
from cv_bridge import CvBridge


class LineFollower(Node):

    def __init__(self):
        super().__init__('line_follower')

        # --------------- 可调参数（全部可通过 launch 传入） ---------------
        self.declare_parameter('image_topic', '/camera')
        self.declare_parameter('cmd_vel_topic', '/cmd_vel')
        self.declare_parameter('linear_speed', 1.0) # 1m/s
        self.declare_parameter('kp', 0.005) # 0.005 rad/s
        self.declare_parameter('kd', 0.001) # 0.001 rad/s
        self.declare_parameter('stop_duration', 3.0) # 3s
        self.declare_parameter('red_pixel_threshold', 500) # 500
        self.declare_parameter('line_lost_rotate_speed', 0.3) # 0.3 rad/s
        self.declare_parameter('roi_ratio', 0.25) # 看到更远的线，避免丢线掉头
        self.declare_parameter('red_cooldown', 2.0) # 2s
        self.declare_parameter('binary_thresh', 80) # 80
        self.declare_parameter('resume_duration', 1.0) # 停车后盲走前进的秒数

        image_topic = self.get_parameter('image_topic').value
        cmd_vel_topic = self.get_parameter('cmd_vel_topic').value
        self.linear_speed = self.get_parameter('linear_speed').value
        self.kp = self.get_parameter('kp').value
        self.kd = self.get_parameter('kd').value
        self.stop_duration = self.get_parameter('stop_duration').value
        self.red_pixel_threshold = self.get_parameter('red_pixel_threshold').value
        self.lost_rotate = self.get_parameter('line_lost_rotate_speed').value
        self.roi_ratio = self.get_parameter('roi_ratio').value
        self.red_cooldown = self.get_parameter('red_cooldown').value
        self.binary_thresh = self.get_parameter('binary_thresh').value
        self.resume_duration = self.get_parameter('resume_duration').value

        # --------------- ROS 接口 ---------------
        self.bridge = CvBridge()
        self.cmd_pub = self.create_publisher(Twist, cmd_vel_topic, 10)
        self.image_sub = self.create_subscription(
            Image, image_topic, self.image_cb, 10)

        # --------------- 状态机: FOLLOW_LINE → STOP → RESUME → FOLLOW_LINE ---------------
        self.state = 'FOLLOW_LINE'
        self.stop_start: float = 0.0
        self.resume_start: float = 0.0
        self.last_stop_end: float = 0.0
        self.prev_error: float = 0.0
        self.last_cmd_time = self.get_clock().now()

        self.create_timer(0.1, self._safety_cb)
        self.get_logger().info(
            f'LineFollower ready  image={image_topic}  cmd={cmd_vel_topic}')

    # ------------------------------------------------------------------ #
    #                          图像回调                                    #
    # ------------------------------------------------------------------ #
    def image_cb(self, msg: Image):
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
        except Exception as e:
            self.get_logger().error(f'cv_bridge: {e}')
            return

        h, w = frame.shape[:2]
        roi_h = int(h * self.roi_ratio)
        roi = frame[h - roi_h: h, :]

        now = self._now_sec()

        if self.state == 'FOLLOW_LINE':
            if (now - self.last_stop_end > self.red_cooldown
                    and self._detect_red(roi)):
                self.state = 'STOP'
                self.stop_start = now
                self._pub(0.0, 0.0)
                self.get_logger().info('Red dot detected → STOP')
                return
            self._follow_line(roi, w)

        elif self.state == 'STOP':
            self._pub(0.0, 0.0)
            if now - self.stop_start >= self.stop_duration:
                self.state = 'RESUME'
                self.resume_start = now
                self.prev_error = 0.0
                self.get_logger().info('Stop finished → RESUME (driving forward)')

        elif self.state == 'RESUME':
            # 直行驶过红点区域，不做巡线判断
            self._pub(self.linear_speed * 0.5, 0.0)
            if now - self.resume_start >= self.resume_duration:
                self.state = 'FOLLOW_LINE'
                self.last_stop_end = now
                self.get_logger().info('Resume finished → FOLLOW_LINE')

    # ------------------------------------------------------------------ #
    #                          巡线核心                                    #
    # ------------------------------------------------------------------ #
    def _follow_line(self, roi_bgr, full_w):
        gray = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2GRAY)

        # 黑线在灰度图中是暗像素，THRESH_BINARY_INV 把暗的变白
        _, mask = cv2.threshold(
            gray, self.binary_thresh, 255, cv2.THRESH_BINARY_INV)

        # 去掉红色区域对黑线检测的干扰
        red_mask = self._red_mask(roi_bgr)
        mask = cv2.bitwise_and(mask, cv2.bitwise_not(red_mask))

        M = cv2.moments(mask)
        if M['m00'] < 100:
            # 丢线：只往前走，绝不转弯（宁可走直线也不掉头）
            self._pub(self.linear_speed * 0.3, self.lost_rotate)
            return

        cx = M['m10'] / M['m00']
        error = cx - full_w / 2.0

        # PD 控制
        d_error = error - self.prev_error
        angular_z = -(self.kp * error + self.kd * d_error)
        self.prev_error = error

        # 弯道减速
        speed_factor = max(0.3, 1.0 - abs(error) / full_w)
        self._pub(self.linear_speed * speed_factor, angular_z)

    # ------------------------------------------------------------------ #
    #                         红点检测                                     #
    # ------------------------------------------------------------------ #
    def _red_mask(self, bgr):
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
        m1 = cv2.inRange(hsv, np.array([0, 80, 80]), np.array([10, 255, 255]))
        m2 = cv2.inRange(hsv, np.array([160, 80, 80]), np.array([179, 255, 255]))
        return cv2.bitwise_or(m1, m2)

    def _detect_red(self, roi_bgr) -> bool:
        mask = self._red_mask(roi_bgr)
        return cv2.countNonZero(mask) > self.red_pixel_threshold

    # ------------------------------------------------------------------ #
    #                          工具方法                                    #
    # ------------------------------------------------------------------ #
    def _pub(self, lx: float, az: float):
        msg = Twist()
        msg.linear.x = float(lx)
        msg.angular.z = float(az)
        self.cmd_pub.publish(msg)
        self.last_cmd_time = self.get_clock().now()

    def _now_sec(self) -> float:
        t = self.get_clock().now().to_msg()
        return t.sec + t.nanosec * 1e-9

    def _safety_cb(self):
        elapsed = (self.get_clock().now() - self.last_cmd_time).nanoseconds * 1e-9
        if elapsed > 1.0:
            self._pub(0.0, 0.0)


def main(args=None):
    rclpy.init(args=args)
    node = LineFollower()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node._pub(0.0, 0.0)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()

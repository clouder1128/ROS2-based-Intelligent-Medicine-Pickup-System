import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/clouder/ROS2-based-Intelligent-Medicine-Pickup-System/test/install/line_follower'

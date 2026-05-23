#!/usr/bin/env python

import rclpy

from ros_tcp_endpoint import TcpServer
from ros_tcp_endpoint.publisher import RosPublisher


def main(args=None):
    rclpy.init(args=args)
    tcp_server = TcpServer("UnityEndpoint")

    _pre_register_publishers(tcp_server)

    tcp_server.start()

    tcp_server.setup_executor()

    tcp_server.destroy_nodes()
    rclpy.shutdown()


def _pre_register_publishers(tcp_server):
    """Pre-register publishers so Unity topics are accepted even if __publish syscommands are not processed."""
    try:
        from task_msgs.msg import CarState, CabinetState, CabinetRunning, TaskState, Task
    except ImportError:
        tcp_server.logerr("task_msgs msg types not available, skipping pre-registration")
        return

    registrations = {
        "CarState_U":       CarState,
        "CabinetState_U":   CabinetState,
        "CabinetRunning_U": CabinetRunning,
        "TaskState_U":      TaskState,
        "TaskData_U":       Task,
    }
    for topic, cls in registrations.items():
        if topic not in tcp_server.publishers_table:
            publisher = RosPublisher(topic, cls)
            tcp_server.publishers_table[topic] = publisher
            tcp_server.loginfo(f"Pre-registered publisher '{topic}'")


if __name__ == "__main__":
    main()

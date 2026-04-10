#!/usr/bin/env python3
"""Log velocity_pivot for every wheel to a timestamped CSV file."""

import csv
import os
import signal
import sys
from datetime import datetime

import rclpy
from rclpy.node import Node
from kelo_tulip.msg import KeloDrivesInput


class PivotVelocityLogger(Node):
    """Subscribe to /platform_driver/wheels_input and save velocity_pivot to CSV."""

    def __init__(self) -> None:
        super().__init__('pivot_velocity_logger')

        # Build output path
        self.declare_parameter('output_dir', os.path.expanduser('~'))
        base_dir = str(
            self.get_parameter('output_dir').get_parameter_value().string_value
        )
        
        output_dir = os.path.join(base_dir, "skratch_ws/debug")
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.csv_path = os.path.join(output_dir, f'pivot_velocities_{timestamp}.csv')

        # Open file & writer — header written once
        self._file = open(self.csv_path, 'w', newline='')
        self._writer = csv.writer(self._file)
        self._header_written = False
        self._msg_count = 0

        # Subscription
        self.create_subscription(
            KeloDrivesInput,
            '/platform_driver/wheels_input',
            self._callback,
            10,
        )

        self.get_logger().info(f'Logging pivot velocities → {self.csv_path}')

    # callback 
    def _callback(self, msg: KeloDrivesInput) -> None:
        wheels = msg.wheels
        if not wheels:
            return

        num_wheels = len(wheels)

        # Write header on first message (adapts to actual wheel count)
        if not self._header_written:
            header = ['timestamp'] + [
                f'wheel_{i}_velocity_pivot' for i in range(num_wheels)
            ]
            self._writer.writerow(header)
            self._header_written = True

        # Collect velocity_pivot from each wheel
        row = [self.get_clock().now().nanoseconds]
        for w in wheels:
            row.append(w.velocity_pivot)

        self._writer.writerow(row)
        self._msg_count += 1

        # Flush periodically so data isn't lost on kill
        if self._msg_count % 50 == 0:
            self._file.flush()

    # clean shutdown
    def destroy_node(self) -> None:
        self._file.flush()
        self._file.close()
        self.get_logger().info(
            f'Saved {self._msg_count} rows → {self.csv_path}'
        )
        super().destroy_node()


def main() -> None:
    rclpy.init()
    node = PivotVelocityLogger()

    # Ensure Ctrl-C triggers a clean shutdown
    def _signal_handler(sig, frame):
        node.get_logger().info('Shutting down…')
        node.destroy_node()
        rclpy.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, _signal_handler)

    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        if rclpy.ok():
            node.destroy_node()
            rclpy.shutdown()


if __name__ == '__main__':
    main()

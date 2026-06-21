#!/usr/bin/env python3
"""
Aphid Zone Trigger — standalone package.

Subscribes directly to the existing detection topics (read-only,
does not touch aphid_sprayer_bridge or sprayer_driver in any way)
and splits each camera's image into 3 equal-height vertical zones:

    zone 0 = top    (smallest pixel y)
    zone 1 = middle
    zone 2 = bottom (largest pixel y, closest to robot)

Left camera  -> nozzles 0, 1, 2  (top/mid/bottom)
Right camera -> nozzles 3, 4, 5  (top/mid/bottom)

Publishes NozzleCommand to /sprayer/nozzle_command_zoned, a topic
nothing else currently subscribes to — intended for the separate
i2c_solenoid_driver package. No existing package is read, modified,
or subscribed to by anything new here.
"""

import rclpy
from rclpy.node import Node
from vision_msgs.msg import Detection2DArray

from sprayer_interfaces.msg import NozzleCommand

NUM_ZONES = 3  # per camera
NOZZLE_BASE = {'left': 0, 'right': 3}


class AphidZoneTrigger(Node):
    def __init__(self):
        super().__init__('aphid_zone_trigger')

        self.declare_parameter('min_detections_to_spray', 3)
        self.declare_parameter('spray_duration', 0.762)
        self.declare_parameter('cooldown_duration', 1.0)
        self.declare_parameter('image_height', 640)  # matches RT-DETR input size

        self.min_detections = self.get_parameter('min_detections_to_spray').value
        self.spray_duration = self.get_parameter('spray_duration').value
        self.cooldown = self.get_parameter('cooldown_duration').value
        self.image_height = self.get_parameter('image_height').value
        self.zone_height = self.image_height / NUM_ZONES

        self.nozzle_ids = (
            [NOZZLE_BASE['left'] + z for z in range(NUM_ZONES)] +
            [NOZZLE_BASE['right'] + z for z in range(NUM_ZONES)]
        )
        self.nozzle_state = {n: False for n in self.nozzle_ids}
        self.last_spray_time = {n: 0.0 for n in self.nozzle_ids}

        self.cmd_pub = self.create_publisher(
            NozzleCommand, '/sprayer/nozzle_command_zoned', 10)

        self.sub_left = self.create_subscription(
            Detection2DArray, '/left/aphid/detections',
            lambda msg: self.detection_callback(msg, camera='left'), 10)
        self.sub_right = self.create_subscription(
            Detection2DArray, '/right/aphid/detections',
            lambda msg: self.detection_callback(msg, camera='right'), 10)

        self.create_timer(0.1, self.spray_timeout_check)

        self.get_logger().info('Aphid Zone Trigger started')
        self.get_logger().info(
            f'{NUM_ZONES} zones/camera, image_height={self.image_height} -> '
            f'publishing /sprayer/nozzle_command_zoned')
        self.get_logger().info(f'Min detections to spray: {self.min_detections}')
        self.get_logger().info(f'Spray duration: {self.spray_duration}s')

    def zone_for_y(self, y: float) -> int:
        zone = int(y // self.zone_height)
        return max(0, min(NUM_ZONES - 1, zone))

    def detection_callback(self, msg: Detection2DArray, camera: str):
        now = self.get_clock().now().nanoseconds / 1e9

        zone_counts = {z: 0 for z in range(NUM_ZONES)}
        for det in msg.detections:
            y = det.bbox.center.position.y
            zone_counts[self.zone_for_y(y)] += 1

        base_nozzle = NOZZLE_BASE[camera]
        for zone, count in zone_counts.items():
            nozzle_id = base_nozzle + zone
            if count < self.min_detections:
                continue
            if now - self.last_spray_time[nozzle_id] < self.cooldown:
                continue
            if not self.nozzle_state[nozzle_id]:
                self.set_nozzle(nozzle_id, True)
                self.last_spray_time[nozzle_id] = now
                self.get_logger().info(
                    f'Nozzle {nozzle_id} ON — {camera} zone {zone} — {count} aphids detected')

    def spray_timeout_check(self):
        now = self.get_clock().now().nanoseconds / 1e9
        for nozzle_id in self.nozzle_ids:
            if self.nozzle_state[nozzle_id]:
                if now - self.last_spray_time[nozzle_id] > self.spray_duration:
                    self.set_nozzle(nozzle_id, False)
                    self.get_logger().info(f'Nozzle {nozzle_id} OFF — spray duration elapsed')

    def set_nozzle(self, nozzle_id: int, enable: bool):
        cmd = NozzleCommand()
        cmd.nozzle_id = nozzle_id
        cmd.enable = enable
        self.cmd_pub.publish(cmd)
        self.nozzle_state[nozzle_id] = enable

    def on_shutdown(self):
        self.get_logger().info('Shutting down — turning off all zoned nozzles')
        for nozzle_id in self.nozzle_ids:
            self.set_nozzle(nozzle_id, False)


def main(args=None):
    rclpy.init(args=args)
    node = AphidZoneTrigger()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.on_shutdown()
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

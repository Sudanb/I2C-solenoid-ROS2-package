#!/usr/bin/env python3
"""
ROS2 node for the Adafruit I2C-to-8-Channel Solenoid Driver (MCP23017).

Subscribes to per-channel commands and writes directly to the MCP23017
GPIOA register over I2C. Also provides a service for timed pulses
(useful for spray valve actuation where you want on->off without
blocking the main callback thread).

Dependencies:
    pip install smbus2
    ROS2: std_msgs

Wiring:
    STEMMA QT / Qwiic -> I2C bus on host (e.g. Jetson Orin Nano I2C-7,
    or RPi5 I2C-1). Default I2C address 0x20 (all address jumpers open).
"""

import threading
import time

import rclpy
from rclpy.node import Node
from std_srvs.srv import SetBool

# Same custom interface package aphid_sprayer_bridge already publishes
from sprayer_interfaces.msg import NozzleCommand

from smbus2 import SMBus

# MCP23017 register addresses (IOCON.BANK = 0, default power-on state)
IODIRA = 0x00   # I/O direction register, port A (1 = input, 0 = output)
GPIOA = 0x12    # GPIO port A register (read/write pin state)
OLATA = 0x14    # Output latch register, port A

NUM_CHANNELS = 8


class MCP23017SolenoidDriver(Node):
    def __init__(self):
        super().__init__('mcp23017_solenoid_driver')

        self.declare_parameter('i2c_bus', 7)        # Jetson Orin Nano default I2C bus; use 1 for RPi
        self.declare_parameter('i2c_address', 0x20) # default with all addr jumpers open
        self.declare_parameter('active_high', True) # this board sinks to GND when "on" -> drive bit HIGH to enable MOSFET

        bus_num = self.get_parameter('i2c_bus').value
        self.addr = self.get_parameter('i2c_address').value
        self.active_high = self.get_parameter('active_high').value

        self._lock = threading.Lock()
        self.bus = SMBus(bus_num)

        # Configure port A as all outputs
        self.bus.write_byte_data(self.addr, IODIRA, 0x00)

        # Track current state, all off at startup
        self.state = 0x00
        self._write_state()

        # Subscribe directly to what aphid_sprayer_bridge already publishes —
        # no bridge/adapter node needed.
        self.create_subscription(
            NozzleCommand, '/sprayer/nozzle_command_zoned', self.cmd_callback, 10)
        self.create_service(SetBool, 'solenoid_emergency_stop', self.estop_callback)

        self.get_logger().info(
            f'MCP23017 solenoid driver up on i2c bus {bus_num}, addr 0x{self.addr:02X}')

    def _write_state(self):
        with self._lock:
            self.bus.write_byte_data(self.addr, GPIOA, self.state)

    def _set_channel(self, ch: int, on: bool):
        if not (0 <= ch < NUM_CHANNELS):
            self.get_logger().warn(f'Channel {ch} out of range 0-{NUM_CHANNELS-1}')
            return
        bit_on = on if self.active_high else not on
        if bit_on:
            self.state |= (1 << ch)
        else:
            self.state &= ~(1 << ch)
        self._write_state()

    def cmd_callback(self, msg: NozzleCommand):
        """NozzleCommand: nozzle_id (int), enable (bool) — one channel per message."""
        self._set_channel(msg.nozzle_id, msg.enable)

    def pulse_channel(self, ch: int, duration_s: float):
        """Fire a channel for duration_s seconds then turn off. Blocking — call from a thread."""
        self._set_channel(ch, True)
        time.sleep(duration_s)
        self._set_channel(ch, False)

    def estop_callback(self, request, response):
        if request.data:
            self.state = 0x00
            self._write_state()
            response.success = True
            response.message = 'All solenoids OFF'
        else:
            response.success = True
            response.message = 'No-op (estop release does not auto re-enable channels)'
        return response

    def destroy_node(self):
        # Safety: de-energize all solenoids on shutdown
        self.state = 0x00
        try:
            self._write_state()
        except Exception:
            pass
        self.bus.close()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = MCP23017SolenoidDriver()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

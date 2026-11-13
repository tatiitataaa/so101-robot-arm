"""Assign the SO-101 Leader ID to ONE motor, using LeRobot's own setup_motor().

Same code path as `lerobot-setup-motors`, but for a single named joint:
finds the only motor on the bus, turns torque off, writes the joint's ID and
1,000,000 baud to EEPROM, then verifies it answers at the new ID. No movement.

Usage: python set_one_motor_id.py <port> <joint>
  joint: shoulder_pan(1) shoulder_lift(2) elbow_flex(3) wrist_flex(4) wrist_roll(5) gripper(6)
"""
import sys
import warnings

warnings.filterwarnings("ignore")

from lerobot.teleoperators.so_leader import SO101Leader, SO101LeaderConfig

port, joint = sys.argv[1], sys.argv[2]
leader = SO101Leader(SO101LeaderConfig(port=port, id="my_leader"))
bus = leader.bus
if joint not in bus.motors:
    sys.exit(f"Unknown joint '{joint}'. Choose from: {list(bus.motors)}")

print(f"Setting up '{joint}' -> ID {bus.motors[joint].id} (only one motor must be connected)")
try:
    bus.setup_motor(joint)
    print(f"Done: '{joint}' motor now answers as ID {bus.motors[joint].id}")
finally:
    if bus.is_connected:
        bus.disconnect(disable_torque=False)

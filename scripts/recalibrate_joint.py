"""Re-record the range of ONE joint on the Leader or Follower, keeping all other joints.

1. Writes the saved calibration file back onto all motors of that arm, so motors and file
   agree again (e.g. after an aborted lerobot-calibrate run).
2. Records min/max of the chosen joint while you move it end to end; ENTER stops.
3. Updates only that joint's range_min/range_max, writes it to the motor and saves the file
   (the old file is kept next to it as <id>.json.bak).

Torque is turned OFF on the whole arm (the Follower goes limp: have it in its rest pose)
and nothing moves by itself. The homing offset is kept, so no "middle pose" step.

Usage: python scripts/recalibrate_joint.py leader|follower <port> <joint> [id]
  default id: my_leader / my_follower
"""
import shutil
import sys
import warnings

warnings.filterwarnings("ignore")

from lerobot.robots.so_follower import SO101Follower, SO101FollowerConfig
from lerobot.teleoperators.so_leader import SO101Leader, SO101LeaderConfig

if len(sys.argv) < 4 or sys.argv[1] not in ("leader", "follower"):
    sys.exit(__doc__)
arm, port, joint = sys.argv[1:4]
arm_id = sys.argv[4] if len(sys.argv) > 4 else f"my_{arm}"
if arm == "leader":
    device = SO101Leader(SO101LeaderConfig(port=port, id=arm_id))
else:
    device = SO101Follower(SO101FollowerConfig(port=port, id=arm_id))
bus, fpath = device.bus, device.calibration_fpath

if not fpath.is_file():
    sys.exit(f"No calibration file at {fpath}; run lerobot-calibrate first.")
if joint not in bus.motors or joint == "wrist_roll":
    sys.exit(f"Choose one of: {[m for m in bus.motors if m != 'wrist_roll']}")

bus.connect()
try:
    bus.disable_torque()
    calib = device.calibration
    bus.write_calibration(calib)  # restore the saved calibration on every motor
    old = (calib[joint].range_min, calib[joint].range_max)
    print(f"Restored {fpath.name} on all {arm} motors. {joint} old range: {old}")
    print(f"Move {joint} to BOTH ends of its range, then press ENTER.", flush=True)

    mins, maxes = bus.record_ranges_of_motion([joint])
    new = (int(mins[joint]), int(maxes[joint]))
    print(f"\n{joint}: old range {old} -> new range {new}")

    shutil.copy(fpath, str(fpath) + ".bak")
    calib[joint].range_min, calib[joint].range_max = new
    bus.write_calibration(calib)
    device._save_calibration()
    print(f"Saved {fpath} (backup: {fpath.name}.bak)")
finally:
    bus.disconnect()

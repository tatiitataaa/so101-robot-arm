"""Live raw encoder positions (0-4095) of both arms, side by side. Read-only, nothing moves.

Usage: python scripts/live_positions.py <leader_port> <follower_port> [joint ...]
Ctrl+C to stop.
"""
import sys
import time
import warnings

warnings.filterwarnings("ignore")

from check_directions import JOINTS, open_bus

if len(sys.argv) < 3:
    sys.exit(__doc__)
joints = [j for j in JOINTS if j in sys.argv[3:]] or JOINTS
leader, follower = open_bus(sys.argv[1]), open_bus(sys.argv[2])
start = None
try:
    print("Move the joint(s) by hand. Ctrl+C to stop.\n")
    while True:
        cols = []
        for j in joints:
            m = leader.motors[j].id
            lp, fp = leader._read("present_position", m, 3), follower._read("present_position", m, 3)
            cols.append(f"{j}: leader {lp:>4}  follower {fp:>4}")
        print("\r" + "   |   ".join(cols) + "   ", end="", flush=True)
        time.sleep(0.05)
except KeyboardInterrupt:
    print()
finally:
    for bus in (leader, follower):
        if bus.is_connected:
            bus.disconnect(disable_torque=False)

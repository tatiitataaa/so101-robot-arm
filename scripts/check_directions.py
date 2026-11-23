"""Find which joints turn the opposite way on the Leader vs the Follower.

Read-only: it reads raw encoder positions (0-4095) from both arms and never writes
a register, so nothing moves and no calibration is changed. Raw positions don't
depend on any calibration file, so this checks the hardware itself (how each motor
is mounted).

For each joint you move that joint on BOTH arms the same physical way (e.g. both
toward you), and the script says whether the two encoders counted the same way.

Usage: python scripts/check_directions.py <leader_port> <follower_port> [joint ...]
  e.g. ... /dev/tty.usbmodemA /dev/tty.usbmodemB wrist_flex   (check only that joint)
"""
import sys
import warnings

warnings.filterwarnings("ignore")

from lerobot.motors import Motor, MotorNormMode, SerialMotorsBus

JOINTS = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"]
HINTS = {
    "shoulder_pan": "rotate the whole arm LEFT (seen from behind the base)",
    "shoulder_lift": "tilt the upper arm FORWARD / down",
    "elbow_flex": "bend the elbow (fold the forearm in)",
    "wrist_flex": "tilt the wrist DOWN",
    "wrist_roll": "twist the wrist CLOCKWISE (looking at the gripper from the front)",
    "gripper": "OPEN the gripper",
}
MIN_MOVE = 80  # encoder ticks (~7 degrees); smaller moves are treated as "didn't move"


def open_bus(port):
    bus = SerialMotorsBus(
        port, {j: Motor(i, "sts3215", MotorNormMode.RANGE_M100_100) for i, j in enumerate(JOINTS, 1)}
    )
    bus.connect(handshake=False)  # just opens the serial port
    return bus


def read_all(bus):
    return {j: bus._read("present_position", m.id, 3) for j, m in bus.motors.items()}


def delta(a, b):
    """b - a on a 4096-tick circle (handles wrap-around)."""
    return (b - a + 2048) % 4096 - 2048


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    leader, follower = open_bus(sys.argv[1]), open_bus(sys.argv[2])
    try:
        for name, bus in (("Leader", leader), ("Follower", follower)):
            pos = read_all(bus)  # fails here if a motor doesn't answer
            torque = {j: bus._read("torque_enable", m.id, 3) for j, m in bus.motors.items()}
            print(f"{name}: all 6 motors answer. Raw positions: {pos}")
            if any(torque.values()):
                print(f"  NOTE: torque is ON for {[j for j, t in torque.items() if t]} on the {name}; "
                      "power-cycle that arm (unplug power, wait, replug) so you can move it by hand.")
                sys.exit(1)

        print("\nFor each joint: start with both arms in roughly the same pose,\n"
              "press ENTER, move that joint on BOTH arms the same way by ~30-60 degrees, press ENTER.\n"
              "Type s + ENTER to skip a joint.\n")
        results = {}
        for j in [j for j in JOINTS if j in sys.argv[3:]] or JOINTS:
            if input(f"[{j}] press ENTER when ready (s = skip) ").strip().lower() == "s":
                continue
            l0, f0 = read_all(leader)[j], read_all(follower)[j]
            input(f"    now {HINTS[j]} on BOTH arms, then press ENTER ")
            dl, df = delta(l0, read_all(leader)[j]), delta(f0, read_all(follower)[j])
            if abs(dl) < MIN_MOVE or abs(df) < MIN_MOVE:
                verdict = "UNCLEAR (move further and re-run)"
            elif (dl > 0) == (df > 0):
                verdict = "same direction ✅"
            else:
                verdict = "REVERSED ❌"
            results[j] = verdict
            print(f"    leader moved {dl:+d} ticks, follower moved {df:+d} ticks -> {verdict}\n")

        print("Summary:")
        for j, v in results.items():
            print(f"  {j:<14} {v}")
    finally:
        for bus in (leader, follower):
            if bus.is_connected:
                bus.disconnect(disable_torque=False)


if __name__ == "__main__":
    main()

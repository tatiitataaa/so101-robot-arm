"""Read-only communication test for ONE Feetech STS3215 on the bus.

Pings (broadcast scan) at each STS3215 baud rate and reads a few registers.
It never writes a register: no torque, no movement, no ID/baud change.
The port is closed with disable_torque=False so not even a torque-off write is sent.

Usage: python motor_readonly_test.py /dev/tty.usbmodemXXXX
"""
import sys
import warnings

warnings.filterwarnings("ignore")

import rustypot
from lerobot.motors import Motor, MotorNormMode, SerialMotorsBus

port = sys.argv[1]
_, definition = rustypot.find_model("sts3215")

bus = SerialMotorsBus(port, {"m": Motor(1, "sts3215", MotorNormMode.RANGE_M100_100)})
bus.connect(handshake=False)  # just opens the serial port
try:
    # Factory default (1,000,000) first, then the rest.
    bauds = sorted(definition.baudrates, key=lambda b: b != definition.factory_baudrate)
    found = None
    for baud in bauds:
        bus.set_baudrate(baud)
        ids = bus._scan(definition)  # broadcast ping, read-only
        print(f"{baud:>8} baud: {ids or 'no answer'}")
        if ids:
            found = (baud, ids)
            break

    if not found:
        print("\nNo motor answered at any baud rate. Check power, 3-pin cable, and jumpers.")
        sys.exit(2)

    baud, ids = found
    if len(ids) > 1:
        print(f"\nWARNING: {len(ids)} motors answered; connect only one motor.")
    # The bus only reads ids it was built with: rebuild it with the ids found.
    bus.disconnect(disable_torque=False)
    bus = SerialMotorsBus(port, {f"m{i}": Motor(i, "sts3215", MotorNormMode.RANGE_M100_100) for i in ids})
    bus.connect(handshake=False)
    bus.set_baudrate(baud)
    for mid, model in ids.items():
        print(f"\nMotor id={mid} model_number={model} (STS3215=777) at {baud} baud")
        for reg in ("firmware_major_version", "firmware_minor_version", "present_voltage",
                    "present_temperature", "present_position", "torque_enable", "status"):
            val = bus._read(reg, mid, 2)
            extra = {"present_voltage": f"  -> {val / 10:.1f} V",
                     "present_temperature": " C",
                     "present_position": "  (0-4095 raw)"}.get(reg, "")
            print(f"  {reg:<24} {val}{extra}")
finally:
    bus.disconnect(disable_torque=False)

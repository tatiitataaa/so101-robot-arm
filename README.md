# so101-robot-arm
Building and programming an open-source SO-101 Robotic arm using Hugging Face LeRobot. Exploring teleoperation, computer vision, and imitation learning.

Building the [SO-101](https://huggingface.co/docs/lerobot/so101) Leader and Follower arms with
[Hugging Face LeRobot](https://github.com/huggingface/lerobot).

## Setup (macOS, Apple Silicon)

```bash
# 1. Miniforge (conda), installed to ~/miniforge3 without touching ~/.zshrc
curl -fL -o Miniforge3-MacOSX-arm64.sh \
  https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-MacOSX-arm64.sh
bash Miniforge3-MacOSX-arm64.sh -b -p ~/miniforge3

# 2. Environment with Python 3.12 + ffmpeg
~/miniforge3/bin/conda create -y -n lerobot -c conda-forge python=3.12 ffmpeg

# 3. LeRobot with Feetech motor support and CLI tools
source ~/miniforge3/bin/activate lerobot
pip install -r requirements.txt
```

Every new terminal: `source ~/miniforge3/bin/activate lerobot`
(make sure no other venv, e.g. `(.venv)`, is active at the same time).

## Hardware

| Part | Notes |
|---|---|
| Motors | Feetech STS3215, **7.4 V** version |
| Power supply | **5 V DC, 4 A** (never 12 V for 7.4 V motors; USB power alone is not enough) |
| Controller | Feetech bus servo board (USB chip WCH CH343, shows up as `/dev/tty.usbmodem…`) |

Find the board's port with `lerobot-find-port` (unplug the USB cable when asked).

### Plugging in / unplugging

- **Connect:** 3-pin motor cable → USB to laptop → power supply into the wall (last).
- **Disconnect:** power supply out of the wall (first) → USB → 3-pin cable.

## Motor IDs

IDs are stored **on the motor itself** (EEPROM), not in this repo. Label every motor with a sticker.
New motors are all ID 1, so set up **one motor at a time, alone on the board**.

### Leader arm

| Joint | ID | Gear ratio | Status |
|---|---|---|---|
| shoulder_pan | 1 | 1/191 | ☐ |
| shoulder_lift | 2 | 1/345 | ☐ |
| elbow_flex | 3 | 1/191 | ☐ |
| wrist_flex | 4 | 1/147 | ☐ |
| wrist_roll | 5 | 1/147 | ✅ done (verified: model 777, fw 3.10, 1,000,000 baud) |
| gripper | 6 | 1/147 | ☐ (friend) |

### Follower arm

| Joint | ID | Gear ratio | Status |
|---|---|---|---|
| shoulder_pan | 1 | 1/345 | ☐ |
| shoulder_lift | 2 | 1/345 | ☐ |
| elbow_flex | 3 | 1/345 | ☐ |
| wrist_flex | 4 | 1/345 | ☐ |
| wrist_roll | 5 | 1/345 | ☐ |
| gripper | 6 | 1/345 | ☐ |

## Scripts

```bash
# Read-only check of the single connected motor (no writes, no movement)
python scripts/motor_readonly_test.py /dev/tty.usbmodemXXXX

# Give ONE Leader motor its ID (writes ID + baud to the motor's EEPROM, no movement)
python scripts/set_one_motor_id.py /dev/tty.usbmodemXXXX wrist_roll
```

Joints: `shoulder_pan` (1), `shoulder_lift` (2), `elbow_flex` (3), `wrist_flex` (4), `wrist_roll` (5), `gripper` (6).
`set_one_motor_id.py` uses the Leader's ID table. Follower motors are set up with the official
`lerobot-setup-motors --robot.type=so101_follower --robot.port=...` instead.

## Next steps

1. Set IDs for the remaining motors.
2. Assemble both arms.
3. Calibrate (`lerobot-calibrate`), then back up the calibration files LeRobot saves.

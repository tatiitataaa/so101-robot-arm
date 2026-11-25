# so101-robot-arm
Building and programming an open-source SO-101 Robotic arm using Hugging Face LeRobot. Exploring teleoperation, computer vision, and imitation learning.

Building the [SO-101](https://huggingface.co/docs/lerobot/so101) Leader and Follower arms with
[Hugging Face LeRobot](https://github.com/huggingface/lerobot).

## Control room web app (`web/`)

A browser app to control the follower by typing or speaking, follow the leader arm (teleop) and save poses.
It talks to the arms directly over USB from **Chrome or Edge** (Web Serial), so no local server is needed.

- Code: [`web/`](web/) is a linked copy (git submodule) of
  [pangpulkes/robot-arm-control-room](https://github.com/pangpulkes/robot-arm-control-room), which is synced with the
  Lovable project "Arm Whisper Control Room". Change the app there or in Lovable, not in this repo.
- Clone with the app included: `git clone --recurse-submodules https://github.com/tatiitataaa/so101-robot-arm.git`
  (already cloned? `git submodule update --init`). To move `web/` to the newest app version:
  `git submodule update --remote web`, then commit.
- Open the app in its own Chrome tab (not inside the Lovable editor), then **Setup → Connect** the follower
  (port ending in …5B910436491) and the leader (…5B910272241). Only one program can use an arm at a time, so stop
  `lerobot-teleoperate` first.
- Safety built in: connecting only reads; the leader is never written to; moves are slow (≤ 20 °/s, following ≤ 60 °/s);
  each goal stays within a per-joint distance of where the follower really is (elbow 25°, shoulder_lift 20°, others
  10–12°); STOP / Esc holds the arm where it is.

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

All 12 motors are set up and both arms are assembled (verified 2026-11-23: all 6 motors
answer on each board at ~5.4 V).

### Leader arm

| Joint | ID | Gear ratio | Status |
|---|---|---|---|
| shoulder_pan | 1 | 1/191 | ✅ |
| shoulder_lift | 2 | 1/345 | ✅ |
| elbow_flex | 3 | 1/191 | ✅ |
| wrist_flex | 4 | 1/147 | ✅ |
| wrist_roll | 5 | 1/147 | ✅ |
| gripper | 6 | 1/147 | ✅ |

### Follower arm

| Joint | ID | Gear ratio | Status |
|---|---|---|---|
| shoulder_pan | 1 | 1/345 | ✅ |
| shoulder_lift | 2 | 1/345 | ✅ |
| elbow_flex | 3 | 1/345 | ✅ |
| wrist_flex | 4 | 1/345 | ✅ |
| wrist_roll | 5 | 1/345 | ✅ |
| gripper | 6 | 1/345 | ✅ |

## Ports (this MacBook)

| Arm | Port |
|---|---|
| Leader | `/dev/tty.usbmodem5B910272241` |
| Follower | `/dev/tty.usbmodem5B910436491` |

The names belong to each board, so they normally stay the same. If a command can't find a port,
run `lerobot-find-port` again. To tell the boards apart, unplug one USB cable and see which port disappears.

## Calibration

LeRobot looks calibration up by **id**. Always use `my_follower` and `my_leader`, both when
calibrating and when teleoperating. A different id (or a different laptop) means "no calibration
found", and the follower then moves wrongly. That was the cause of the wrong-direction problem.

LeRobot stores the files in `~/.cache/huggingface/lerobot/calibration/`. A backup is in
[`calibration/`](calibration/) in this repo, with the same folder layout.

**Restore on a new laptop** (instead of recalibrating):
```bash
mkdir -p ~/.cache/huggingface/lerobot/calibration
cp -R calibration/* ~/.cache/huggingface/lerobot/calibration/
```
The ranges are tied to these motors, not to the laptop, so the backup works anywhere for these arms.

**Calibrate from scratch:**
```bash
lerobot-calibrate --robot.type=so101_follower --robot.port=/dev/tty.usbmodem5B910436491 --robot.id=my_follower
lerobot-calibrate --teleop.type=so101_leader --teleop.port=/dev/tty.usbmodem5B910272241 --teleop.id=my_leader
```
1. Middle pose (every joint halfway, as in the video), then ENTER.
2. Move every joint to **both mechanical ends**, then ENTER (wrist_roll is skipped).

**Lessons learned:**
- With LeRobot 0.7's default `use_degrees=true`, a joint's zero is the **middle of its recorded
  range**. If a joint doesn't reach one of its ends, its zero shifts and the follower sits off by
  that amount. (Our leader shoulder_lift first recorded only 768–2481, so the follower's shoulder sat ~36° too high.)
- Lift the leader off the table while calibrating. Its handle hits the table and stops the
  arm from folding fully.
- Close the follower gripper **fully** during calibration. Otherwise "closed" leaves a gap.
- To fix one joint without redoing everything, use `scripts/recalibrate_joint.py` (below).

## Teleoperation

```bash
source ~/miniforge3/bin/activate lerobot && cd ~/so101-robot-arm
lerobot-teleoperate \
  --robot.type=so101_follower --robot.port=/dev/tty.usbmodem5B910436491 --robot.id=my_follower \
  --teleop.type=so101_leader --teleop.port=/dev/tty.usbmodem5B910272241 --teleop.id=my_leader
```
- Start with both arms in the rest pose. The follower jumps to the leader's pose right away.
- Clamp the leader **at the table edge** so the handle hangs freely and the rest poses match.
- Optional speed limit for testing: `--robot.max_relative_target=10`.
- Stop with Ctrl+C. **Hold the follower first**, because it goes limp.

## Scripts

```bash
# Read-only check of the single connected motor (no writes, no movement)
python scripts/motor_readonly_test.py /dev/tty.usbmodemXXXX

# Give ONE Leader motor its ID (writes ID + baud to the motor's EEPROM, no movement)
python scripts/set_one_motor_id.py /dev/tty.usbmodemXXXX wrist_roll

# Do Leader and Follower joints turn the same way? (read-only, raw encoders, guided)
python scripts/check_directions.py <leader_port> <follower_port> [joint ...]

# Live raw positions of both arms side by side (read-only, Ctrl+C to stop)
python scripts/live_positions.py <leader_port> <follower_port> [joint ...]

# Re-record ONE joint's range, keep every other joint (torque off, saves a .bak)
python scripts/recalibrate_joint.py leader|follower <port> <joint>
```

Joints: `shoulder_pan` (1), `shoulder_lift` (2), `elbow_flex` (3), `wrist_flex` (4), `wrist_roll` (5), `gripper` (6).
`set_one_motor_id.py` uses the Leader's ID table. Follower motors are set up with the official
`lerobot-setup-motors --robot.type=so101_follower --robot.port=...` instead.

After any recalibration, update the backup in this repo and commit it:
`rsync -a --exclude='*.bak' ~/.cache/huggingface/lerobot/calibration/ calibration/`

## Next steps

1. Add cameras and record a first dataset (`lerobot-record`).
2. Train a first policy (e.g. ACT) on the recorded episodes.

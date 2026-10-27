# Football Camera Workflow

Personal football-video workflow: ball detections -> target selection -> smoothed
digital follow -> candidate goal clips for manual review.

Based on the MIT-licensed Roboflow Sports ball tracker; attribution and exact
upstream revision are in THIRD_PARTY.md. This is a prototype, not a claim of
reliable goal recognition or real-device validation.

## Run

Python 3.10+; install requirements.txt in an isolated virtual environment.

```powershell
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python football_workflow.py --video match.mp4 --detections balls.jsonl --goal-roi 0.8 0.2 1 0.8 --output outputs/run1
.venv/Scripts/python -m unittest -v
```

Each JSONL record contains a zero-based frame index and ball-center candidates:

```json
{"frame": 0, "balls": [[0.42, 0.53], [0.9, 0.1]]}
{"frame": 1, "balls": [[0.43, 0.53]]}
{"frame": 2, "balls": []}
```

Coordinates are normalized to the ORIGINAL input frame. Filter detections to
the ball class and sort candidates by confidence before export. An external
detector supplies these records; the repository does not yet run a learned
detector or download model weights. Missing frames mean no detection.

## Outputs

- follow.mp4: bounded, smoothed virtual-camera crop, not physical camera motion.
- tracking.csv: observed ball position, crop center, normalized preview velocity.
  These are NOT calibrated motor commands and are never sent to hardware.
- events.json: candidate times and merged clip windows.
- candidate_*.mp4: original-frame clips, five seconds before to three after an event.

The goal region must be manually calibrated for a fixed camera. An event requires
the selected ball to move from outside into the region and remain for three
observations. It can confuse shots, occlusions, false detections and actual goals.
Moving source cameras require a field-coordinate transform, not a static ROI.
Use constant-frame-rate footage. OpenCV exports omit AUDIO. Output directories
must be empty to prevent accidental replacement. Real footage stays local and
is ignored by Git. Obtain participants' permission before sharing recordings.

## Next integration steps

Connect a licensed ball detector, test on actual match footage, calibrate field
geometry, then evaluate false positives and missed events. Physical follow needs
the exact gimbal protocol, mechanical limits, emergency stop and latency testing.
Do not connect preview velocities directly to motors.

## Validation and license

Six local tests passed, including synthetic video processing and clip decoding;
see VALIDATION.md for the scope and remaining gaps. Code is MIT licensed;
upstream attribution is preserved in THIRD_PARTY.md.

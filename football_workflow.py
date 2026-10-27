"""Offline football tracking and candidate-highlight workflow. No hardware actuation."""
import argparse
import csv
import json
import math
from collections import deque
from pathlib import Path


class BallTracker:
    """Adapted from Roboflow Sports BallTracker (MIT); see THIRD_PARTY.md."""

    def __init__(self, buffer_size=10, max_missing=10):
        self.history = deque(maxlen=buffer_size)
        self.max_missing = max_missing
        self.missing = 0

    def update(self, candidates):
        if not candidates:
            self.missing += 1
            if self.missing > self.max_missing:
                self.history.clear()
            return None
        self.missing = 0
        # Unlike upstream, retain only the selected target, not every distractor.
        if self.history:
            center = tuple(sum(p[i] for p in self.history) / len(self.history)
                           for i in (0, 1))
            point = min(candidates, key=lambda p: math.dist(p, center))
        else:
            point = candidates[0]
        self.history.append(point)
        return point


class SmoothFollow:
    def __init__(self, alpha=0.2, max_speed=0.4, deadband=0.02):
        self.alpha, self.max_speed, self.deadband = alpha, max_speed, deadband
        self.position = (0.5, 0.5)

    def update(self, target, dt):
        if target is None:
            return self.position, (0.0, 0.0)
        previous = self.position
        result = []
        for old, goal in zip(previous, target):
            error = goal - old
            step = 0 if abs(error) < self.deadband else self.alpha * error
            step = max(-self.max_speed * dt, min(self.max_speed * dt, step))
            result.append(max(0.0, min(1.0, old + step)))
        self.position = tuple(result)
        return self.position, tuple((a - b) / dt for a, b in zip(result, previous))


class GoalCandidate:
    """Flag consecutive observations entering a fixed image ROI, not confirmed goals."""

    def __init__(self, roi, dwell=3, cooldown=5.0):
        self.roi, self.dwell, self.cooldown = roi, dwell, cooldown
        self.count, self.last = 0, -math.inf
        self.was_outside = False

    def update(self, point, time):
        if point is None:
            self.count = 0
            self.was_outside = False
            return False
        x1, y1, x2, y2 = self.roi
        inside = x1 <= point[0] <= x2 and y1 <= point[1] <= y2
        if not inside:
            self.count = 0
            self.was_outside = True
            return False
        self.count += 1
        if self.was_outside and self.count >= self.dwell and time - self.last >= self.cooldown:
            self.last = time
            self.was_outside = False
            return True
        return False


def load_detections(path):
    rows = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        frame, balls = row["frame"], row["balls"]
        if not isinstance(frame, int) or isinstance(frame, bool) or frame < 0 or frame in rows:
            raise ValueError("Frame IDs must be unique nonnegative integers")
        points = []
        for point in balls:
            if len(point) != 2 or any(not isinstance(v, (float, int)) or not math.isfinite(v)
                                      or not 0 <= v <= 1 for v in point):
                raise ValueError("Ball centers must be finite normalized [x,y] coordinates")
            points.append(tuple(point))
        rows[frame] = points
    return rows


def merge_windows(times, duration, before=5.0, after=3.0):
    windows = []
    for t in sorted(times):
        start, end = max(0.0, t - before), min(duration, t + after)
        if windows and start <= windows[-1][1]:
            windows[-1][1] = max(windows[-1][1], end)
        else:
            windows.append([start, end])
    return windows


def run(args):
    try:
        import cv2
    except ImportError as exc:
        raise SystemExit("Install requirements.txt in a project virtual environment first") from exc
    source = Path(args.video).resolve()
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise ValueError("Use an empty output directory; existing results are never overwritten")
    detections = load_detections(args.detections)
    cap = cv2.VideoCapture(str(source))
    if not cap.isOpened():
        raise ValueError("Cannot open input video")
    writer = None
    events = []
    frame_index = 0
    try:
        fps = cap.get(cv2.CAP_PROP_FPS)
        if not math.isfinite(fps) or fps <= 0:
            raise ValueError("Input must have a valid constant frame rate")
        tracker = BallTracker(max_missing=max(1, round(fps / 2)))
        follow = SmoothFollow()
        goal = GoalCandidate(args.goal_roi)
        with (output / "tracking.csv").open("w", newline="", encoding="utf-8") as file:
            log = csv.writer(file)
            log.writerow(["frame", "seconds", "ball_x", "ball_y", "crop_x", "crop_y",
                          "pan_preview", "tilt_preview", "candidate"])
            while True:
                ok, frame = cap.read()
                if not ok:
                    break
                height, width = frame.shape[:2]
                if writer is None:
                    crop_w, crop_h = max(2, int(width * args.crop) // 2 * 2), max(2, int(height * args.crop) // 2 * 2)
                    writer = cv2.VideoWriter(str(output / "follow.mp4"), cv2.VideoWriter_fourcc(*"mp4v"), fps, (crop_w, crop_h))
                    if not writer.isOpened():
                        raise ValueError("Cannot create MP4 writer")
                point = tracker.update(detections.get(frame_index, []))
                center, velocity = follow.update(point, 1 / fps)
                candidate = goal.update(point, frame_index / fps)
                if candidate:
                    events.append(frame_index / fps)
                left = max(0, min(width - crop_w, round(center[0] * width - crop_w / 2)))
                top = max(0, min(height - crop_h, round(center[1] * height - crop_h / 2)))
                writer.write(frame[top:top + crop_h, left:left + crop_w])
                log.writerow([frame_index, frame_index / fps, *(point or ("", "")), *center, *velocity, int(candidate)])
                frame_index += 1
    finally:
        cap.release()
        if writer is not None:
            writer.release()
    if not frame_index:
        raise ValueError("Input contains no decodable frames")
    if detections and max(detections) >= frame_index:
        raise ValueError("Detection frame IDs exceed decoded video length")
    windows = merge_windows(events, frame_index / fps)
    (output / "events.json").write_text(json.dumps({"candidate_seconds": events, "clip_windows": windows,
        "confirmed_goals": False, "audio_preserved": False}, indent=2), encoding="utf-8")
    for index, (start, end) in enumerate(windows):
        export_clip(cv2, source, output / f"candidate_{index + 1:03d}.mp4", start, end, fps)
    print(f"Processed {frame_index} frames; {len(windows)} candidate clips. Review manually.")


def export_clip(cv2, source, destination, start, end, fps):
    cap = cv2.VideoCapture(str(source))
    writer = None
    try:
        # Sequential decoding avoids keyframe-dependent seek offsets.
        index = 0
        while True:
            ok, frame = cap.read()
            if not ok or index / fps >= end:
                break
            if index / fps >= start:
                if writer is None:
                    h, w = frame.shape[:2]
                    writer = cv2.VideoWriter(str(destination), cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
                    if not writer.isOpened():
                        raise ValueError("Cannot create candidate clip")
                writer.write(frame)
            index += 1
    finally:
        cap.release()
        if writer is not None:
            writer.release()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video", required=True)
    parser.add_argument("--detections", required=True, help="JSONL ball centers from an external detector")
    parser.add_argument("--output", required=True)
    parser.add_argument("--goal-roi", type=float, nargs=4, required=True, metavar=("X1", "Y1", "X2", "Y2"))
    parser.add_argument("--crop", type=float, default=0.65)
    args = parser.parse_args()
    x1, y1, x2, y2 = args.goal_roi
    if not (0 <= x1 < x2 <= 1 and 0 <= y1 < y2 <= 1 and 0 < args.crop <= 1):
        parser.error("ROI must be ordered and normalized; crop must be in (0,1]")
    run(args)


if __name__ == "__main__":
    main()

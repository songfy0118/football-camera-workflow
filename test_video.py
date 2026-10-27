"""Synthetic integration check; does not measure real-football detection accuracy."""
import argparse
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from football_workflow import run


@unittest.skipUnless(importlib.util.find_spec("cv2"), "OpenCV is not installed")
class VideoIntegrationTests(unittest.TestCase):
    def test_crop_and_candidate_clip_are_decodable(self):
        import cv2
        import numpy as np

        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            video = root / "synthetic.mp4"
            writer = cv2.VideoWriter(str(video), cv2.VideoWriter_fourcc(*"mp4v"), 10, (320, 180))
            self.assertTrue(writer.isOpened())
            rows = []
            try:
                for index in range(40):
                    x = 0.4 if index < 20 else 0.9
                    frame = np.zeros((180, 320, 3), dtype=np.uint8)
                    cv2.circle(frame, (round(x * 320), 90), 8, (255, 255, 255), -1)
                    writer.write(frame)
                    rows.append(json.dumps({"frame": index, "balls": [[x, 0.5]]}))
            finally:
                writer.release()
            detections = root / "balls.jsonl"
            detections.write_text("\n".join(rows), encoding="utf-8")
            output = root / "results"
            args = argparse.Namespace(video=str(video), detections=str(detections),
                                      output=str(output), goal_roi=(0.8, 0.2, 1, 0.8), crop=0.65)
            run(args)
            events = json.loads((output / "events.json").read_text())
            self.assertEqual(len(events["candidate_seconds"]), 1)
            for name in ("follow.mp4", "candidate_001.mp4"):
                cap = cv2.VideoCapture(str(output / name))
                try:
                    ok, frame = cap.read()
                    self.assertTrue(ok, name)
                    self.assertGreater(frame.max(), 0, name)
                finally:
                    cap.release()
            with self.assertRaises(ValueError):
                run(args)


if __name__ == "__main__":
    unittest.main()

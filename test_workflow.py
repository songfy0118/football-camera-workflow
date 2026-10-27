import math
import tempfile
import unittest
from pathlib import Path
from football_workflow import BallTracker, SmoothFollow, GoalCandidate, merge_windows, load_detections


class WorkflowTests(unittest.TestCase):
    def test_tracking_ignores_distractor_and_expires(self):
        tracker = BallTracker(max_missing=1)
        self.assertEqual(tracker.update([(0.2, 0.2)]), (0.2, 0.2))
        self.assertEqual(tracker.update([(0.9, 0.9), (0.21, 0.2)]), (0.21, 0.2))
        self.assertIsNone(tracker.update([]))
        tracker.update([])
        self.assertEqual(tracker.update([(0.9, 0.9)]), (0.9, 0.9))

    def test_smoothing_rate_and_stop(self):
        follow = SmoothFollow()
        position, speed = follow.update((1, 1), 0.1)
        self.assertLessEqual(speed[0], 0.400001)
        self.assertEqual(follow.update(None, 0.1), (position, (0, 0)))

    def test_candidate_requires_entry_and_continuity(self):
        goal = GoalCandidate((0.8, 0.2, 1, 0.8), dwell=2)
        self.assertFalse(goal.update((0.9, 0.5), 0))
        goal.update((0.5, 0.5), 1)
        self.assertFalse(goal.update((0.9, 0.5), 2))
        self.assertTrue(goal.update((0.9, 0.5), 3))
        self.assertFalse(goal.update((0.9, 0.5), 4))
        goal.update(None, 5)
        self.assertFalse(goal.update((0.9, 0.5), 6))

    def test_merge_clamped_windows(self):
        self.assertEqual(merge_windows([2, 4, 19], 20), [[0, 7], [14, 20]])

    def test_invalid_detection_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "test.jsonl"
            for text in ['{"frame":0,"balls":[[2,0]]}', '{"frame":0,"balls":[[NaN,0]]}',
                         '{"frame":0,"balls":[]}\n{"frame":0,"balls":[]}']:
                path.write_text(text)
                with self.assertRaises(ValueError):
                    load_detections(path)


if __name__ == "__main__":
    unittest.main()

# Validation status

Local check, 2026-10-27:

- Five stdlib unit tests passed: target choice/history expiration, bounded
  smoothing/lost-target stop, candidate ROI entry/continuity, merged clip
  windows, invalid coordinates/duplicate frames.
- All six tests passed in the isolated project virtual environment.
- Synthetic video integration passed with 40 input frames and one candidate
  clip. Both the smoothed crop and the candidate clip decoded successfully
  and contained nonzero pixels. Reusing an output directory was rejected.
- Tested packages: numpy 2.5.4 and opencv-python-headless 4.14.0.94.
- The video test skips explicitly if OpenCV is unavailable; a skip on another
  environment must not be mistaken for passed video validation.
- Real football recordings, detector quality, audio retention and physical
  gimbal operation have NOT been verified in this revision.
- No performance or goal-detection accuracy is claimed.

Run `python -m unittest -v` in the same environment used for the workflow.

# Open-source provenance

BallTracker is adapted from Roboflow Sports, sports/common/ball.py:
https://github.com/roboflow/sports/blob/42c80c06b6b65a7f89455b89fe31cdf4c38ba227/sports/common/ball.py

The upstream centroid-nearest candidate selection is retained. This version
accepts normalized Python tuples without supervision/numpy dependencies, retains
selected positions only, and resets history after missing detections. Other
workflow code is new. No upstream weights or datasets are distributed.

## Upstream MIT notice

MIT License

Copyright (c) 2024 Roboflow

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

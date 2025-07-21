# IntelliTrack

This repository contains a minimal Python package used for demonstration
purposes.

## Running tests

1. Install the development dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the test suite using `pytest`:
   ```bash
   pytest
   ```

The configuration for `pytest` is stored in `pyproject.toml` and tests live
under the `tests/` directory.
=======
A minimal application demonstrating object tracking with PTZ control.

## Requirements

Install dependencies:
=======
This repository contains small experimental tools. The `src/ndi_viewer.py` script provides a PyQt-based viewer for NDI streams.

## Usage

First install the required dependencies, typically via pip:

```bash
pip install -r requirements.txt
```

## Usage

Run the video tracker:

```bash
python -m src.video_tracker
```

Select a region of interest to start tracking. Use the toggle button to enable or disable PTZ tracking.
=======
Then run the viewer:

```bash
python src/ndi_viewer.py
```

A window will appear with a dropdown listing discovered NDI sources. Selecting a source will display the live video in real time.

For a PySide6-based viewer run:

```bash
python src/ndi_viewer_pyside6.py
```

This version uses PySide6 and OpenCV to preview the selected NDI source.

=======
IntelliTrack aims to build a cross-platform PTZ camera tracking application that runs on both Windows and macOS. The goal is to provide a simple tool for discovering cameras, previewing video in real time and controlling PTZ functions while tracking objects automatically.

## Key Features

- **NDI discovery** for automatically finding network cameras.
- **Real-time video** preview using OpenCV.
- **PTZ control** to manage pan, tilt and zoom operations.
- **Object tracking** to keep the camera focused on moving subjects.

## Setup

1. Install Python 3.8 or later.
2. Install the required dependencies:
   ```bash
   pip install PyQt5 opencv-python
   ```
3. Additional modules for NDI and camera control will be added as the project develops.

### Frameworks

- [PyQt5](https://pypi.org/project/PyQt5/) provides the cross-platform GUI.
- [OpenCV](https://pypi.org/project/opencv-python/) handles video capture and processing.

### Supported Operating Systems

- Windows
- macOS

More details will be documented as IntelliTrack progresses.

# IntelliTrack

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

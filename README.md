# IntelliTrack

A minimal set of tools for experimenting with NDI video sources and PTZ camera tracking.

## Requirements

* **Python 3.10** – the NDI Python bindings currently fail to build on newer Python releases.
* [PySide6](https://pypi.org/project/PySide6/) and [OpenCV](https://pypi.org/project/opencv-python/).
* [`ndi-python`](https://pypi.org/project/ndi-python/) from the official [NDI SDK](https://www.ndi.tv/sdk/).

Install everything with:

```bash
pip install -r requirements.txt
```

On **Windows** you may need to install the NDI SDK first and then install the wheel:

```bash
pip install ndi-python
```

## Running

Make sure the desired NDI sources are visible on your network. No IP configuration is required.

Set `PYTHONPATH` to the project root and launch the viewer:

```powershell
$env:PYTHONPATH = ""
python -m gui.main_window
```

The application lists all discovered NDI sources and shows a live preview when one is selected.

## Additional tools

The repository also contains simple viewers using PyQt5 (`src/ndi_viewer.py`) and PySide6 (`src/ndi_viewer_pyside6.py`) as well as an experimental object tracker.

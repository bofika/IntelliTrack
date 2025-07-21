# IntelliTrack

This repository contains small experimental tools. The `src/ndi_viewer.py` script provides a PyQt-based viewer for NDI streams.

## Usage

First install the required dependencies, typically via pip:

```bash
pip install -r requirements.txt
```

Then run the viewer:

```bash
python src/ndi_viewer.py
```

A window will appear with a dropdown listing discovered NDI sources. Selecting a source will display the live video in real time.


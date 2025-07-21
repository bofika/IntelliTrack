import sys
from PyQt5 import QtWidgets, QtGui, QtCore
import numpy as np
import cv2

try:
    import NDIlib as ndi  # ndi-python module
except ImportError:  # pragma: no cover - running without ndi-python installed
    ndi = None


class NDIViewer(QtWidgets.QWidget):
    """Simple viewer that lists NDI sources and displays the selected one."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("NDI Viewer")
        self.image_label = QtWidgets.QLabel(alignment=QtCore.Qt.AlignCenter)
        self.source_selector = QtWidgets.QComboBox()
        self.refresh_button = QtWidgets.QPushButton("Refresh")

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.source_selector)
        layout.addWidget(self.refresh_button)
        layout.addWidget(self.image_label)

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self._update_frame)
        self.refresh_button.clicked.connect(self._refresh_sources)
        self.source_selector.currentIndexChanged.connect(self._connect_source)

        self.finder = None
        self.receiver = None
        self.current_source = None

        if ndi is not None:
            if not ndi.initialize():
                raise RuntimeError("Cannot initialize NDI")
        self._refresh_sources()
        self.timer.start(30)

    def closeEvent(self, event):
        self.timer.stop()
        if self.receiver is not None:
            ndi.recv_destroy(self.receiver)
        if self.finder is not None:
            ndi.find_destroy(self.finder)
        if ndi is not None:
            ndi.destroy()
        super().closeEvent(event)

    # NDI handling ---------------------------------------------------------
    def _refresh_sources(self):
        """Discover available NDI sources."""
        if ndi is None:
            self.source_selector.clear()
            self.source_selector.addItem("ndi-python not installed")
            return

        if self.finder is None:
            self.finder = ndi.find_create_v2()
        ndi.find_wait_for_sources(self.finder, 1000)
        sources = ndi.find_get_current_sources(self.finder)
        self.sources = list(sources)

        self.source_selector.blockSignals(True)
        self.source_selector.clear()
        for src in self.sources:
            self.source_selector.addItem(src.ndi_name)
        self.source_selector.blockSignals(False)

        if self.sources:
            self._connect_source(0)

    def _connect_source(self, index):
        if ndi is None or not self.sources:
            return
        source = self.sources[index]
        if self.receiver is None:
            self.receiver = ndi.recv_create_v3()
        ndi.recv_connect(self.receiver, source)
        self.current_source = source

    def _update_frame(self):
        if self.receiver is None:
            return
        # Capture a frame from NDI. We use timeout 0 to return immediately.
        video_frame = ndi.VideoFrameV2()
        t, _a, _b = ndi.recv_capture_v2(self.receiver, video_frame, None, None, 0)
        if t == ndi.FRAME_TYPE_VIDEO:
            height = video_frame.yres
            width = video_frame.xres
            data = np.frombuffer(video_frame.data, dtype=np.uint8)
            data = data.reshape(height, video_frame.line_stride_in_bytes // 4, 4)
            # Convert BGRA to RGB for Qt
            frame = cv2.cvtColor(data, cv2.COLOR_BGRA2RGB)
            image = QtGui.QImage(
                frame.data, width, height, QtGui.QImage.Format_RGB888
            )
            pix = QtGui.QPixmap.fromImage(image)
            self.image_label.setPixmap(pix)
            ndi.recv_free_video_v2(self.receiver, video_frame)


def main():
    app = QtWidgets.QApplication(sys.argv)
    viewer = NDIViewer()
    viewer.resize(640, 480)
    viewer.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

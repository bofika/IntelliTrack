import sys
import numpy as np
import cv2
from PySide6 import QtCore, QtGui, QtWidgets

try:
    import NDIlib as ndi
except ImportError:  # pragma: no cover - NDI may not be installed
    ndi = None


class NDIViewer(QtWidgets.QMainWindow):
    """PySide6-based viewer for NDI sources."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("NDI Viewer")

        central = QtWidgets.QWidget()
        self.setCentralWidget(central)

        self.combo = QtWidgets.QComboBox()
        self.refresh_btn = QtWidgets.QPushButton("Refresh")
        self.video_label = QtWidgets.QLabel(alignment=QtCore.Qt.AlignCenter)
        self.video_label.setMinimumSize(320, 240)

        top_row = QtWidgets.QHBoxLayout()
        top_row.addWidget(self.combo)
        top_row.addWidget(self.refresh_btn)

        layout = QtWidgets.QVBoxLayout(central)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        layout.addLayout(top_row)
        layout.addWidget(self.video_label)

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self._update_frame)
        self.refresh_btn.clicked.connect(self._refresh_sources)
        self.combo.currentIndexChanged.connect(self._connect_source)

        self.finder = None
        self.receiver = None
        self.sources = []

        if ndi is not None and ndi.initialize():
            self._refresh_sources()
        else:
            self.combo.addItem("ndi-python not available")

        self.timer.start(30)

    # ------------------------------------------------------------------
    def closeEvent(self, event):
        self.timer.stop()
        if self.receiver is not None:
            ndi.recv_destroy(self.receiver)
            self.receiver = None
        if self.finder is not None:
            ndi.find_destroy(self.finder)
            self.finder = None
        if ndi is not None:
            ndi.destroy()
        super().closeEvent(event)

    # ------------------------------------------------------------------
    def _refresh_sources(self):
        """Find NDI sources on the network."""
        if ndi is None:
            return

        if self.finder is None:
            self.finder = ndi.find_create_v2()
            if self.finder is None:
                QtWidgets.QMessageBox.critical(self, "Error", "Failed to create NDI finder")
                return

        ndi.find_wait_for_sources(self.finder, 1000)
        self.sources = list(ndi.find_get_current_sources(self.finder))

        self.combo.blockSignals(True)
        self.combo.clear()
        for src in self.sources:
            name = src.ndi_name
            ip = src.url_address if src.url_address else ""
            display = f"{name} ({ip})" if ip else name
            self.combo.addItem(display)
        self.combo.blockSignals(False)

        if not self.sources:
            self.video_label.setText("No NDI sources found")
            self._disconnect_receiver()
        else:
            self._connect_source(self.combo.currentIndex())

    def _disconnect_receiver(self):
        if self.receiver is not None:
            ndi.recv_destroy(self.receiver)
            self.receiver = None

    def _connect_source(self, index):
        if ndi is None or not self.sources:
            return

        if index < 0 or index >= len(self.sources):
            self._disconnect_receiver()
            return

        source = self.sources[index]

        if self.receiver is None:
            self.receiver = ndi.recv_create_v3()
            if self.receiver is None:
                QtWidgets.QMessageBox.critical(self, "Error", "Failed to create NDI receiver")
                return

        ndi.recv_connect(self.receiver, source)

    def _update_frame(self):
        if self.receiver is None:
            return
        video_frame = ndi.VideoFrameV2()
        t, _a, _b = ndi.recv_capture_v2(self.receiver, video_frame, None, None, 0)
        if t == ndi.FRAME_TYPE_VIDEO:
            h = video_frame.yres
            w = video_frame.xres
            data = np.frombuffer(video_frame.data, dtype=np.uint8)
            data = data.reshape(h, video_frame.line_stride_in_bytes // 4, 4)
            frame = cv2.cvtColor(data, cv2.COLOR_BGRA2RGB)
            qimg = QtGui.QImage(frame.data, w, h, QtGui.QImage.Format_RGB888)
            self.video_label.setPixmap(QtGui.QPixmap.fromImage(qimg))
            ndi.recv_free_video_v2(self.receiver, video_frame)
        elif t == ndi.FRAME_TYPE_ERROR:
            self.video_label.setText("Error receiving video")
            self._disconnect_receiver()
        else:
            pass


def main():
    app = QtWidgets.QApplication(sys.argv)
    viewer = NDIViewer()
    viewer.resize(640, 480)
    viewer.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

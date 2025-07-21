import sys
import numpy as np
import cv2
from PySide6 import QtCore, QtGui, QtWidgets

try:
    import NDIlib as ndi
except ImportError:  # pragma: no cover - NDI may not be installed
    ndi = None


class MainWindow(QtWidgets.QMainWindow):
    """Main application window for viewing NDI sources."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("IntelliTrack NDI Viewer")

        central = QtWidgets.QWidget()
        self.setCentralWidget(central)

        self.refresh_btn = QtWidgets.QPushButton("Refresh")
        self.source_combo = QtWidgets.QComboBox()
        self.video_label = QtWidgets.QLabel(alignment=QtCore.Qt.AlignCenter)
        self.video_label.setMinimumSize(320, 240)

        left_layout = QtWidgets.QVBoxLayout()
        left_layout.addWidget(self.refresh_btn)
        left_layout.addWidget(self.source_combo)
        left_layout.addStretch(1)

        main_layout = QtWidgets.QHBoxLayout(central)
        main_layout.addLayout(left_layout)
        main_layout.addWidget(self.video_label, 1)

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self._update_frame)
        self.refresh_btn.clicked.connect(self._refresh_sources)
        self.source_combo.currentIndexChanged.connect(self._connect_source)

        self.finder = None
        self.receiver = None
        self.sources = []

        if ndi is not None and ndi.initialize():
            self._refresh_sources()
        else:
            self.source_combo.addItem("ndi-python not available")

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
        """Discover NDI sources on the local network."""
        if ndi is None:
            return

        if self.finder is None:
            self.finder = ndi.find_create_v2()
            if self.finder is None:
                QtWidgets.QMessageBox.critical(self, "Error", "Failed to create NDI finder")
                return

        ndi.find_wait_for_sources(self.finder, 1000)
        self.sources = list(ndi.find_get_current_sources(self.finder))

        self.source_combo.blockSignals(True)
        self.source_combo.clear()
        for src in self.sources:
            name = src.ndi_name
            ip = src.url_address or ""
            display = f"{name} ({ip})" if ip else name
            self.source_combo.addItem(display)
        self.source_combo.blockSignals(False)

        if not self.sources:
            self.video_label.setText("No NDI sources found")
            self._disconnect_receiver()
        else:
            self._connect_source(self.source_combo.currentIndex())

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
        self._disconnect_receiver()
        self.receiver = ndi.recv_create_v3()
        if self.receiver is None:
            QtWidgets.QMessageBox.critical(self, "Error", "Failed to create NDI receiver")
            return
        ndi.recv_connect(self.receiver, source)

    def _update_frame(self):
        if self.receiver is None or ndi is None:
            return

        frame_type, video_frame, _, _ = ndi.recv_capture_v2(self.receiver, 1000)
        if frame_type == ndi.FRAME_TYPE_VIDEO:
            h = video_frame.yres
            w = video_frame.xres
            data = np.frombuffer(video_frame.data, dtype=np.uint8)
            data = data.reshape(h, video_frame.line_stride_in_bytes // 4, 4)
            frame = cv2.cvtColor(data, cv2.COLOR_BGRA2RGB)
            qimg = QtGui.QImage(frame.data, w, h, QtGui.QImage.Format_RGB888)
            self.video_label.setPixmap(QtGui.QPixmap.fromImage(qimg))
            ndi.recv_free_video_v2(self.receiver, video_frame)
        elif frame_type == ndi.FrameType.ERROR:
            self.video_label.setText("Error receiving video")
            self._disconnect_receiver()


def main():
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

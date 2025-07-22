import sys
import logging

import numpy as np
import cv2
from PySide6 import QtCore, QtGui, QtWidgets

try:
    import NDIlib as ndi
except ImportError:  # pragma: no cover - NDI may not be installed
    ndi = None

logger = logging.getLogger(__name__)


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
        self._last_qimage = None  # prevent QImage from being garbage collected

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

    # ------------------------------------------------------------------
    def _display_qimage(self, qimg: QtGui.QImage) -> None:
        """Display the given QImage on the QLabel.

        Keeping a reference prevents premature garbage collection. If further
        instability arises this method can be invoked via QTimer.singleShot to
        ensure execution on the main thread.
        """

        self._last_qimage = qimg
        self.video_label.setPixmap(QtGui.QPixmap.fromImage(qimg))

    def _update_frame(self):
        try:
            if self.receiver is None or ndi is None:
                return

            timeout = 1000
            while True:
                try:
                    frame_type, video_frame, audio_frame, metadata_frame = ndi.recv_capture_v2(
                        self.receiver, timeout
                    )
                    # subsequent iterations should return immediately
                    timeout = 0

                    logger.info("Received frame type: %s", frame_type)

                    if frame_type == ndi.FRAME_TYPE_VIDEO:
                        logger.info(
                            "Processing video frame %sx%s",
                            video_frame.xres,
                            video_frame.yres,
                        )
                        data = np.frombuffer(video_frame.data, dtype=np.uint8)
                        logger.info("Reshaping video data")
                        data = data.reshape(
                            video_frame.yres,
                            video_frame.line_stride_in_bytes // 4,
                            4,
                        )
                        frame = cv2.cvtColor(data, cv2.COLOR_BGRA2RGB)
                        logger.info("Creating QImage")
                        qimg = QtGui.QImage(
                            frame.data,
                            video_frame.xres,
                            video_frame.yres,
                            QtGui.QImage.Format_RGB888,
                        )
                        try:
                            self._display_qimage(qimg)
                            logger.info("Display updated")
                        except Exception:
                            logger.exception("Error during QLabel update")
                            raise
                        self.repaint()
                        logger.info("Done displaying frame")
                        ndi.recv_free_video_v2(self.receiver, video_frame)
                        break
                    elif frame_type == ndi.FRAME_TYPE_AUDIO:
                        logger.info("Received audio frame")
                        ndi.recv_free_audio_v2(self.receiver, audio_frame)
                        continue
                    elif frame_type == ndi.FRAME_TYPE_METADATA:
                        ndi.recv_free_metadata(self.receiver, metadata_frame)
                        continue
                    elif hasattr(ndi, "FRAME_TYPE_STATUS_CHANGE") and frame_type == ndi.FRAME_TYPE_STATUS_CHANGE:
                        logger.info("Status change event")
                        continue
                    elif frame_type == ndi.FRAME_TYPE_NONE:
                        logger.info("No frame available this loop")
                        break
                    else:
                        logger.warning("Unexpected frame type: %s", frame_type)
                        break
                except Exception:
                    logger.exception("Exception during video frame handling")
                    break
        except Exception as e:
            logger.exception("[FATAL ERROR] Exception in _update_frame: %s", e)


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

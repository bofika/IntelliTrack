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
        """Safely display ``qimg`` on the QLabel.

        A reference to the image is kept to prevent premature garbage
        collection. If this method is called from a thread other than the GUI
        thread it will invoke the update via ``QMetaObject`` using a queued
        connection to avoid crashes.
        """

        self._last_qimage = qimg

        def _set_pixmap() -> None:
            try:
                logger.debug("Converting QImage to QPixmap")
                pix = QtGui.QPixmap.fromImage(qimg)
                self.video_label.setPixmap(pix)
                logger.debug("Pixmap set on QLabel")
            except Exception:
                logger.exception("Failed to update QLabel pixmap")

        if QtCore.QThread.currentThread() != self.thread():
            logger.warning("Display update from non-GUI thread; using invokeMethod")
            QtCore.QMetaObject.invokeMethod(
                self.video_label,
                "setPixmap",
                QtCore.Qt.QueuedConnection,
                QtCore.Q_ARG(QtGui.QPixmap, QtGui.QPixmap.fromImage(qimg)),
            )
        else:
            _set_pixmap()

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
                        width = video_frame.xres
                        height = video_frame.yres
                        logger.info(
                            "Processing video frame %sx%s", width, height
                        )
                        if width <= 0 or height <= 0:
                            logger.error(
                                "Invalid frame dimensions: %sx%s", width, height
                            )
                            ndi.recv_free_video_v2(self.receiver, video_frame)
                            break

                        expected_size = (
                            video_frame.line_stride_in_bytes * video_frame.yres
                        )
                        data = np.frombuffer(
                            video_frame.data, dtype=np.uint8, count=expected_size
                        )
                        logger.debug(
                            "Raw data len=%s stride=%s", len(data), video_frame.line_stride_in_bytes
                        )
                        try:
                            data = data.reshape(
                                height, video_frame.line_stride_in_bytes // 4, 4
                            )
                        except Exception:
                            logger.exception(
                                "Failed to reshape video data: expected %s bytes", expected_size
                            )
                            ndi.recv_free_video_v2(self.receiver, video_frame)
                            break

                        logger.debug(
                            "Frame numpy shape=%s dtype=%s first_bytes=%s",
                            data.shape,
                            data.dtype,
                            data.flat[:8].tolist(),
                        )
                        try:
                            frame = cv2.cvtColor(data, cv2.COLOR_BGRA2RGB)
                        except Exception:
                            logger.exception("cv2.cvtColor failed")
                            ndi.recv_free_video_v2(self.receiver, video_frame)
                            break

                        try:
                            qimg = QtGui.QImage(
                                frame.data,
                                width,
                                height,
                                QtGui.QImage.Format_RGB888,
                            )
                        except Exception:
                            logger.exception("Failed to create QImage")
                            ndi.recv_free_video_v2(self.receiver, video_frame)
                            break

                        try:
                            self._display_qimage(qimg)
                            logger.info("Display updated")
                        except Exception:
                            logger.exception("Error during QLabel update")
                            ndi.recv_free_video_v2(self.receiver, video_frame)
                            break

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

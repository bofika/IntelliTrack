import sys

from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout


def main():
    app = QApplication(sys.argv)
    window = QWidget()
    window.setWindowTitle("IntelliTrack")
    layout = QVBoxLayout()
    label = QLabel("Hello, IntelliTrack!")
    layout.addWidget(label)
    window.setLayout(layout)
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

import cv2
from tkinter import Tk, Label, Button
from PIL import Image, ImageTk
from .ptz_controller import PTZController


class VideoTracker:
    def __init__(self, source=0, ptz_ip="127.0.0.1", ptz_port=52381):
        self.cap = cv2.VideoCapture(source)
        self.ptz = PTZController(ptz_ip, ptz_port)
        self.tracker = None
        self.tracking_enabled = False
        self.bbox = None

        self.root = Tk()
        self.root.title("IntelliTrack")
        self.panel = Label(self.root)
        self.panel.pack()
        Button(self.root, text="Select ROI", command=self.select_roi).pack(side="left")
        self.toggle_btn = Button(
            self.root, text="Tracking OFF", command=self.toggle_tracking
        )
        self.toggle_btn.pack(side="left")

    def select_roi(self):
        ret, frame = self.cap.read()
        if not ret:
            return
        bbox = cv2.selectROI("Select ROI", frame, fromCenter=False, showCrosshair=True)
        cv2.destroyWindow("Select ROI")
        if bbox and bbox[2] > 0 and bbox[3] > 0:
            self.tracker = cv2.TrackerCSRT_create()
            self.tracker.init(frame, bbox)
            self.tracking_enabled = True
            self.toggle_btn.config(text="Tracking ON")

    def toggle_tracking(self):
        self.tracking_enabled = not self.tracking_enabled
        self.toggle_btn.config(text="Tracking ON" if self.tracking_enabled else "Tracking OFF")

    def update(self):
        ret, frame = self.cap.read()
        if not ret:
            self.root.after(10, self.update)
            return
        if self.tracker is not None:
            success, box = self.tracker.update(frame)
            if success:
                x, y, w, h = [int(v) for v in box]
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                if self.tracking_enabled:
                    self.send_ptz(x + w / 2, y + h / 2, frame.shape[1], frame.shape[0])

        img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        imgtk = ImageTk.PhotoImage(image=img)
        self.panel.imgtk = imgtk
        self.panel.config(image=imgtk)
        self.root.after(10, self.update)

    def send_ptz(self, cx, cy, fw, fh):
        offset_x = (cx - fw / 2) / (fw / 2)
        offset_y = (cy - fh / 2) / (fh / 2)
        pan_speed = int(offset_x * 10)
        tilt_speed = int(offset_y * -10)
        self.ptz.pan_tilt(pan_speed, tilt_speed)

    def run(self):
        self.update()
        self.root.mainloop()
        self.cap.release()
        self.ptz.close()


def main():
    tracker = VideoTracker()
    tracker.run()


if __name__ == "__main__":
    main()

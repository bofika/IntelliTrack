class PTZController:
    """Simple VISCA-over-IP controller for PTZ cameras."""
    def __init__(self, ip: str, port: int = 52381):
        import socket
        self.address = (ip, port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def pan_tilt(self, pan_speed: int, tilt_speed: int) -> None:
        """Send pan/tilt command based on speed.

        Positive values pan right/tilt up, negative values pan left/tilt down.
        Speed range is clamped to VISCA limits.
        """
        pan_speed = int(max(min(pan_speed, 0x18), -0x18))
        tilt_speed = int(max(min(tilt_speed, 0x14), -0x14))

        h_speed = max(min(abs(pan_speed), 0x18), 1)
        v_speed = max(min(abs(tilt_speed), 0x14), 1)

        if pan_speed > 0:
            pan_dir = 0x02  # right
        elif pan_speed < 0:
            pan_dir = 0x01  # left
        else:
            pan_dir = 0x03  # stop

        if tilt_speed > 0:
            tilt_dir = 0x01  # up
        elif tilt_speed < 0:
            tilt_dir = 0x02  # down
        else:
            tilt_dir = 0x03  # stop

        cmd = bytes([0x81, 0x01, 0x06, 0x01, h_speed, v_speed, pan_dir, tilt_dir, 0xFF])
        try:
            self.sock.sendto(cmd, self.address)
        except OSError:
            pass

    def close(self) -> None:
        self.sock.close()

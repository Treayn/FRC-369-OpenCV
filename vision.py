import cv2
import queue
import threading
import time

from cube_vision import CubeVision
from tape_vision import TapeVision

class Vision(threading.Thread):
    def __init__(self, terminated: threading.Event, port: int, width: int, height: int):
        super().__init__()
        self._configure_camera(port, width, height)

        self.ready = threading.Event()
        self.terminated = terminated

        self.data = queue.Queue()
        
        self.active_pipeline = CubeVision(width/2, height/2)
    
    def __del__(self):
        self.camera.release()

    def _capture_frame(self) -> None:
        """Get a frame from the camera."""
        _, frame = self.camera.read()
        return frame
    
    def _configure_camera(self, port: int, width: int, height: int) -> None:
        # Set camera port.
        self.camera = cv2.VideoCapture(port)

        # Set camera resolution.
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    
    def disable_vision(self) -> None:
        self.ready.clear()

    def enable_vision(self) -> None:
        self.ready.set()
    
    def get_data(self) -> float:
        return self.data.get_nowait()
    
    def has_data(self) -> bool:
        return not self.data.empty()
    
    def is_enabled(self) -> bool:
        return self.ready.is_set()

    def run(self) -> None:
        self.ready.wait()
        while not self.terminated.is_set():
            frame = self._capture_frame()
            pid_error = self.active_pipeline.process(frame)
            self.data.put(pid_error)
            time.sleep(0.05)
            self.ready.wait()
        
    
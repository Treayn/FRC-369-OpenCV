import cv2
import queue
import threading

from cube_vision import CubeVision
from tape_vision import TapeVision

class Vision(threading.Thread):
    def __init__(self, port: int, width: int, height: int):
        super().__init__()
        self._configure_camera(port, width, height)

        self.ready = threading.Event()
        self.mutex = threading.RLock()

        self.data = queue.Queue()
        self.feed = queue.Queue()
        
        self.vision_pipeline = {
            "Cube": CubeVision(width/2, height/2),
            "Tape": TapeVision(width/2, height/2)
        }
        
        self.active_pipeline = None
    
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
    
    def disable_vision(self):
        self.ready.clear()

    def enable_vision(self):
        self.ready.set()
    
    def get_data(self):
        return self.data.get_nowait()

    def get_feed(self):
        return self.feed.get_nowait()
    
    def run(self):
        self.ready.wait()
        while True:
            frame = self._capture_frame()
            _, jpeg = cv2.imencode('.jpg', frame)
            self.feed.put(jpeg.tobytes())

            if not self.active_pipeline is None:
                pid_error = self.active_pipeline.process(frame)
                self.data.put(pid_error)
            
            self.ready.wait()
    
    def set_vision_type(self, vision_type: str):
        with self.mutex:
            if vision_type is None:
                self.active_pipeline = None
            elif self.active_pipeline is self.vision_pipeline[type]:
                self.active_pipeline = self.vision_pipeline[type]
        
    
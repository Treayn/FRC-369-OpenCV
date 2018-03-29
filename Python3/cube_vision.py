import cv2
import numpy as np

class CubeVision(object):
    def __init__(self, port: int, width: int, height: int):
        # Set camera port.
        self.camera = cv2.VideoCapture(port)
        
        # Set camera resolution.
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        
        # Center of camera is our target position.
        self.target_position = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH)/2)
        self.height = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT)/2)
        
        self.kernel = {
            "outer": cv2.getStructuringElement(cv2.MORPH_RECT,(10, 10)),
            "inner": cv2.getStructuringElement(cv2.MORPH_RECT,(100, 100))
        }

        # Set bounds for color filtering.
        self.bounds = {
            "upper": np.array([90, 255, 255]),
            "lower": np.array([20, 192, 128])
        }
        
        # List for running average, 4 indexes, each initialized to 0.
        self.samples = [0] * 4
    
    def _capture_frame(self) -> None:
        """Get a frame from the camera."""
        _, self.frame = self.camera.read()
    
    def _overlay_target(self) -> None:
        """Add a green target circle on the GUI."""
        cv2.circle(self.frame, (self.target_position, self.height), 7, (0, 255, 0), -1)
        cv2.putText(self.frame, "Robot Center", (self.target_position, self.height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    
    def _threshold_image(self) -> None:
        """Filter and clean image."""
        # Convert image to HSV & filter by color.
        hsv = cv2.cvtColor(self.frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.bounds["lower"], self.bounds["upper"])

        # Filter image further by removing small black & white spots (visual noise) from the mask.
        opening = cv2.morphologyEx(mask, cv2.MORPH_OPEN, self.kernel["outer"])
        closing = cv2.morphologyEx(opening, cv2.MORPH_CLOSE, self.kernel["inner"])

        # Expand the mask slightly.
        dilation = cv2.dilate(closing, self.kernel["inner"], iterations=1)
        self.filtered_mask = dilation

        # Create image to display.
        self.masked_image = cv2.bitwise_and(self.frame, self.frame, mask=self.filtered_mask)
    
    def _get_contours(self) -> None:
        """Find contours, specifically the largest one"""
        bw, contours, hierarchy = cv2.findContours(self.filtered_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        # Get the largest contour and fill in evrything inside it.
        self.largest_contour = max(contours, key=cv2.contourArea)
        cv2.drawContours(self.masked_image, self.largest_contour, -1, (0, 255, 0), -1)
    
    def _get_centers(self) -> None:
        """Get the contour moments/centers"""
        M = cv2.moments(self.largest_contour)
        self.current_position = int(round(M['m10']/M['m00']))
        print('Current position: ' + str(self.current_position))
        print('Target position: ' + str(self.target_position))
    
    def _overlay_actual(self) -> None:
        cv2.circle(self.frame, (self.current_position, self.height), 7, (0, 0, 255), -1)
        cv2.putText(self.frame, "Target Position", (self.current_position, self.height + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
    
    def _display_results(self) -> None:
        cv2.imshow('Raw', self.frame)
        cv2.imshow('Mask', self.masked_image)
        cv2.waitKey(1)
    
    def _filter_results(self):
        """Camera data is very noisy & jumpy. Smooth it out using a running average."""
        # Get rid of the oldest error sample.
        del self.samples[0]

        # Add the most current error sample to the list.
        self.samples.append(self.current_position - self.target_position)

        # Get the error, averaged over the last 4 samples.
        self.dx = np.mean(self.samples)
        self.filtered_position = int(round(self.dx + self.target_position))
    
    def _overlay_filtered(self):
        cv2.circle(self.frame, (self.filtered_position, self.height), 7, (255, 0, 0), -1)
        cv2.putText(self.frame, "Target Filtered", (self.filtered_position + 20, self.height), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

    def _get_error(self) -> int:
        return self.dx

    def process(self):
        self._capture_frame()
        self._threshold_image()
        try:
            self._get_contours()
            self._get_centers()
        except ValueError:
            # If no contours spotted, hold the current heading/position
            self.current_position = self.target_position
        self._filter_results()
        self._overlay_actual()
        self._overlay_filtered()
        self._overlay_target()
        self._display_results()
        return self._get_error()
import cv2
import numpy as np
import time

class CubeVision(object):
    def __init__(self, x_center: float, y_center: float):
        # Center of camera is our target position.
        self.target_position = x_center
        self.current_position = self.target_position
        self.height = int(y_center)

        # Set bounds for color filtering.
        self.bounds = {
            "upper": np.array([90, 255, 255]),
            "lower": np.array([20, 192, 128])
        }
        
        # List for running average, 4 indexes, each initialized to 0.
        self.samples = [0] * 4
    
    def _overlay_target(self, frame) -> None:
        """Add a green target circle on the GUI."""
        cv2.circle(frame, (int(self.target_position), self.height), 7, (0, 255, 0), -1)
        cv2.putText(frame, "Robot Center", (int(self.target_position), self.height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    
    def _threshold_image(self, frame) -> None:
        """Filter and clean image."""
        # Convert image to HSV & filter by color.
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        self.mask = cv2.inRange(hsv, self.bounds["lower"], self.bounds["upper"])

        # Create image to display.
        self.masked_image = cv2.bitwise_and(frame, frame, mask=self.mask)
    
    def _get_contours(self) -> None:
        """Find contours, specifically the largest one"""
        bw, contours, hierarchy = cv2.findContours(self.mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_TC89_KCOS)
        hulls = [cv2.convexHull(contour) for contour in contours]

        # Get the largest contour and fill in everything inside it.
        self.largest_contour = max(hulls, key=cv2.contourArea)
        cv2.drawContours(self.masked_image, self.largest_contour, -1, (0, 255, 0), -1)
    
    def _get_centers(self) -> None:
        """Get the contour moments/centers"""
        M = cv2.moments(self.largest_contour)
        self.current_position = round(M['m10']/M['m00'])
    
    def _overlay_actual(self, frame) -> None:
        cv2.circle(frame, (int(self.current_position), self.height), 7, (0, 0, 255), -1)
        cv2.putText(frame, "Target Position", (int(self.current_position), self.height + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
    
    def _display_results(self, frame) -> None:
        cv2.imshow('Raw', frame)
        cv2.imshow('Mask', self.masked_image)
        cv2.waitKey(1)
    
    def _filter_results(self) -> None:
        """Camera data is very noisy & jumpy. Smooth it out using a running average."""
        # Get rid of the oldest error sample.
        del self.samples[0]

        # Add the most current error sample to the list.
        self.samples.append(self.current_position - self.target_position)

        # Get the error, averaged over the last 4 samples.
        self.dx = np.mean(self.samples)
        self.filtered_position = round(self.dx + self.target_position)
    
    def _print_results(self) -> None:
        print('Current position: ' + str(self.current_position))
        print('Target position: ' + str(self.target_position))

    def _overlay_filtered(self, frame) -> None:
        cv2.circle(frame, (int(self.filtered_position), self.height), 7, (255, 0, 0), -1)
        cv2.putText(frame, "Target Filtered", (int(self.filtered_position) + 20, self.height), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

    def _get_error(self) -> float:
        return self.dx

    def process(self, frame) -> float:
        self._threshold_image(frame)
        try:
            self._get_contours()
            self._get_centers()
        except (ValueError, ZeroDivisionError) as e:
            # If no contours spotted sustain current heading, but decay to zero error.
            self.current_position -= min(50, max(-50, self.current_position - self.target_position))
        self._filter_results()
        self._print_results()
        #self._overlay_actual(frame)
        #self._overlay_filtered(frame)
        #self._overlay_target(frame)
        #self._display_results(frame)
        return self._get_error()
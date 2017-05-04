import cv2
import numpy as np

class Camera(object):
    def __init__(self, width, height):
        self.camera = cv2.VideoCapture(0)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.targetPosition = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH)/2)
        self.height = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT)/2)
        self.kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(5,5))
        self.upperBound = np.array([150, 32, 255])
        self.lowerBound = np.array([90, 0, 224])
        self.results = [0] * 4

        #self.fourcc = cv2.VideoWriter_fourcc(*'DIV4')
        #self.output = cv2.VideoWriter('output.mp4', self.fourcc, 20.0, (int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH)), int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))))
    
    def _captureFrame(self):
        _, self.frame = self.camera.read()
    
    def _overlayTarget(self):
        cv2.circle(self.frame, (self.targetPosition, self.height), 7, (0, 255, 0), -1)
        cv2.putText(self.frame, "Robot Center", (self.targetPosition, self.height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    
    def _thresholdImage(self):
        hsv = cv2.cvtColor(self.frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.lowerBound, self.upperBound)
        opening = cv2.morphologyEx(mask, cv2.MORPH_OPEN, self.kernel)
        closing = cv2.morphologyEx(opening, cv2.MORPH_CLOSE, self.kernel)
        self.filteredMask = closing
    
    def _getContours(self):
        bw, self.contours, hierarchy = cv2.findContours(self.filteredMask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        sortedContours = sorted(self.contours, key=lambda contour: cv2.contourArea(contour))
        self.filteredContours = sortedContours[-2:]
        cv2.drawContours(self.frame, self.filteredContours, -1, (0,255,0), 3)
    
    def _getCenters(self):
        contourCenters = list(map(lambda center: cv2.moments(center), self.filteredContours))
        self.contourX = list(map(lambda point: int(point["m10"]/point["m00"]), contourCenters))
        try:
            self.currentPosition = int((self.contourX[0] + self.contourX[1])/2)
            print('Current position: ' + str(self.currentPosition))
            print('Target position: ' + str(self.targetPosition))
        except IndexError:
            self.currentPosition = self.targetPosition
            print('ERROR: No contours detected')
            print('Using default target coordinates:' + str(self.targetPosition))
        
    def _overlayActual(self):
        cv2.circle(self.frame, (self.currentPosition, self.height), 7, (0, 0, 255), -1)
        cv2.putText(self.frame, "Target Position", (self.currentPosition, self.height + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
    
    def _filterResults(self):
        del self.results[0]
        self.results.append(self.currentPosition - self.targetPosition)
        self.dx = np.mean(self.results)
        self.filteredPosition = int(round(self.dx + self.targetPosition))
    
    def _overlayFiltered(self):
        cv2.circle(self.frame, (self.filteredPosition, self.height), 7, (255, 0, 0), -1)
        cv2.putText(self.frame, "Target Filtered", (self.filteredPosition + 20, self.height), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
    
    def _displayResults(self):
        cv2.imshow('Raw', self.frame)
        cv2.waitKey(1)
    
    def _saveFrame(self):
        self.output.write(frame)

    def _getError(self):
        return self.dx
        #return (self.dx*255)/(targetPosition*2)
    
    def freeResources(self):
        self.camera.release()
        self.output.release()
        cv2.destroyAllWindows()

    def process(self):
        self._captureFrame()
        self._overlayTarget()
        self._thresholdImage()
        self._getContours()
        self._getCenters()
        self._overlayActual()
        self._filterResults()
        self._overlayFiltered()
        self._displayResults()
        return self._getError()
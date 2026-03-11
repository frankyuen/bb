import threading
from os import getenv
import logging
import cv2

IMAGE_WIDTH = int(getenv("IMAGE_WIDTH", "1280"))
IMAGE_HEIGHT = int(getenv("IMAGE_HEIGHT", "720"))

frame_moving_object = bool(getenv("FRAME_MOVING_OBJECT", ""))


class WebcamStreamer:
    """Captures frames from a webcam in a background thread.

    Applies MOG2 background subtraction to detect motion and draws green
    bounding rectangles around moving objects. The latest annotated frame
    is stored as JPEG bytes and exposed via get_frame() for the Flask server.
    """

    def __init__(self, webcam_index=0):
        self._webcam_index = webcam_index
        self._cap = None
        self._frame = None  # latest JPEG bytes, shared with Flask thread
        self._lock = threading.Lock()
        self._thread = None
        self._running = False

        if frame_moving_object:
            # MOG2 models the background as a mixture of Gaussians and updates it
            # over time. Pixels that deviate significantly from the model are
            # classified as foreground (motion). Shadow detection is disabled to
            # avoid false positives on shadow regions.
            self._bg_subtractor = cv2.createBackgroundSubtractorMOG2(
                history=500, varThreshold=50, detectShadows=False
            )

    def start(self):
        """Open the webcam and start the capture thread."""
        self._cap = cv2.VideoCapture(self._webcam_index)
        if not self._cap.isOpened():
            raise RuntimeError(f"Cannot open webcam at index {self._webcam_index}")

        # Set resolution
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, IMAGE_WIDTH)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, IMAGE_HEIGHT)

        # If the set resolution exceeds the camera max, it will fallback
        # to the max resolution the camera is capable of
        max_width = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        max_height = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        logging.info("Working resolution: %d x %d", max_width, max_height)

        self._running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Signal the capture thread to stop and release the webcam."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        if self._cap:
            self._cap.release()

    def _capture_loop(self):
        """Main capture loop: runs in a background thread."""
        while self._running:
            ret, frame = self._cap.read()
            if not ret:
                continue

            if frame_moving_object:
                # Compute the foreground mask for this frame. The subtractor
                # updates the background model internally on each call.
                fg_mask = self._bg_subtractor.apply(frame)

                # Find contours of foreground blobs (each blob = a moving region).
                contours, _ = cv2.findContours(
                    fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
                )
                for contour in contours:
                    # Skip small blobs — likely noise or minor lighting changes.
                    if cv2.contourArea(contour) < 1500:
                        continue
                    x, y, w, h = cv2.boundingRect(contour)
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            _, jpeg = cv2.imencode(".jpg", frame)
            with self._lock:
                self._frame = jpeg.tobytes()

    def get_frame(self):
        """Return the latest annotated frame as JPEG bytes (thread-safe)."""
        with self._lock:
            return self._frame

"""Monitor mode: motion detection using frame differencing."""

import logging
import os
import time
from datetime import datetime, timezone
from os import getenv

import cv2

# --- Configuration from environment variables ---

# Number of frames to capture per scan cycle
LOOP_PER_SCAN = int(getenv("LOOP_PER_SCAN", "400"))

# Minimum contour area (pixels²) for a detected region to be considered real motion.
# Smaller contours are treated as noise (sensor noise, minor lighting flicker, etc.).
# Suggested default: 500
NOISE_THRESHOLD = int(getenv("NOISE_THRESHOLD", "500"))

# Path to the file that records alert execution times (one ISO 8601 line per entry).
# The last line is read to determine the most recent alert time.
ALERT_FILE_PATH = getenv("ALERT_FILE_PATH")

# Minimum seconds between email alerts to avoid notification spam
ALERT_INTERVAL_SECS = int(getenv("ALERT_INTERVAL_SECS", "1800"))

# Set this env var (any value) to always save a snapshot, even when no motion is detected
SAVE_SNAPSHOT = bool(getenv("SAVE_SNAPSHOT", ""))

# Directory where snapshot images are saved
IMAGE_DIR = getenv("IMAGE_DIR")

# Seconds to sleep between scan cycles
SCAN_INTERVAL_SECS = int(getenv("SCAN_INTERVAL_SECS", "60"))

IMAGE_WIDTH = int(getenv("IMAGE_WIDTH", "1280"))
IMAGE_HEIGHT = int(getenv("IMAGE_HEIGHT", "720"))


def scan_frames() -> tuple[bool, cv2.typing.MatLike | None]:
    """
    Open the camera, capture LOOP_PER_SCAN frames, and detect motion using
    frame differencing: the absolute pixel difference between consecutive frames
    is thresholded and contoured. Motion is flagged when any contour exceeds
    NOISE_THRESHOLD in area — anything smaller is treated as noise.
    The camera is unconditionally released before returning.

    On motion, bounding rectangles are drawn in-place on the frame where motion
    was first detected; that annotated frame is returned as the snapshot.
    When no motion is detected, the last captured frame is returned for SAVE_SNAPSHOT use.

    Returns:
        (motion_detected, snapshot_frame): detection result and the frame to save.
    """
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        logging.error("Cannot open camera")
        return False, None

    # Set resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, IMAGE_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, IMAGE_HEIGHT)

    # If the set resolution exceeds the camera max, it will fallback
    # to the max resolution the camera is capable of
    max_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    max_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    logging.info("Working resolution: %d x %d", max_width, max_height)

    last_frame = None  # fallback snapshot for SAVE_SNAPSHOT without motion
    motion_frame = None  # annotated frame where motion was first detected
    motion_detected = False
    prev_gray = None

    try:
        for i in range(LOOP_PER_SCAN):
            ret, frame = cap.read()
            if not ret:
                logging.warning("Failed to capture frame %d — skipping", i)
                continue

            last_frame = frame
            curr_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            if prev_gray is not None:
                # Pixel-wise absolute difference between consecutive frames
                diff = cv2.absdiff(prev_gray, curr_gray)

                # Threshold at 25: changes smaller than ~10% intensity are ignored
                th = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)[1]
                contours, _ = cv2.findContours(
                    th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
                )

                for c in contours:
                    if cv2.contourArea(c) > NOISE_THRESHOLD:
                        # Annotate the motion area in-place; frame is not copied
                        x, y, w, h = cv2.boundingRect(c)
                        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                        motion_detected = True

                if motion_detected:
                    motion_frame = frame
                    break  # snapshot captured; no need to read further frames

            prev_gray = curr_gray
    finally:
        # Always release the camera to avoid device lock
        cap.release()

    snapshot_frame = motion_frame if motion_detected else last_frame
    return motion_detected, snapshot_frame


def alert_control() -> None:
    """
    Manage alert dispatch and execution-time logging.

    Reads the last entry in ALERT_FILE_PATH to determine how long ago the last
    alert was sent. Sends an email only if the elapsed time exceeds
    ALERT_INTERVAL_SECS. Unconditionally appends the current time to
    ALERT_FILE_PATH regardless of whether an email was sent.
    """
    last_entry_time = _read_last_alert_time()

    now = datetime.now(timezone.utc)
    elapsed = (now - last_entry_time).total_seconds() if last_entry_time else None
    should_send = elapsed is None or elapsed > ALERT_INTERVAL_SECS

    if should_send:
        try:
            from emailer import send_email

            send_email(
                subject_text="Motion detected",
                body_text="Motion was detected by the camera monitor.",
            )
            logging.info("Alert email sent")
        except Exception as e:
            logging.warning("Failed to send alert email: %s", e)
    else:
        logging.info(
            "Alert suppressed: last alert was %.0f seconds ago (interval: %d s)",
            elapsed,
            ALERT_INTERVAL_SECS,
        )

    # Unconditionally record this execution time so the interval check stays accurate
    _append_alert_time()


def save_snapshot(frame: cv2.typing.MatLike | None) -> None:
    """
    Save a single frame as a JPEG file in IMAGE_DIR.
    The filename is the UTC timestamp at the time of saving.
    """
    if not IMAGE_DIR:
        logging.warning("Snapshot requested but IMAGE_DIR is not configured")
        return
    if frame is None:
        logging.warning("No frame available; cannot save snapshot")
        return

    filename = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S") + ".jpg"
    path = os.path.join(IMAGE_DIR, filename)

    ok = cv2.imwrite(path, frame)
    if ok:
        logging.info("Snapshot saved: %s", path)
    else:
        logging.warning("cv2.imwrite failed for path: %s", path)


def run_monitor(run_once: bool = False) -> None:
    """
    Main monitor loop. Continuously scans for motion, fires alerts on detection,
    and optionally saves snapshots. Runs indefinitely until interrupted, unless
    run_once is True in which case it exits after a single scan cycle.
    """
    logging.info("Monitor mode started%s", " (run-once)" if run_once else "")

    while True:
        logging.info("Starting scan (%d frames) ...", LOOP_PER_SCAN)
        motion_detected, snapshot_frame = scan_frames()

        logging.info(
            "Scan complete — motion: %s", "DETECTED" if motion_detected else "clear"
        )

        if motion_detected:
            alert_control()

        if motion_detected or SAVE_SNAPSHOT:
            save_snapshot(snapshot_frame)

        if run_once:
            break

        logging.info("Sleeping for %d seconds ...", SCAN_INTERVAL_SECS)
        time.sleep(SCAN_INTERVAL_SECS)


# --- Private helpers ---


def _read_last_alert_time() -> datetime | None:
    """
    Read the last non-empty line from ALERT_FILE_PATH and parse it as ISO 8601.
    Returns None if the file does not exist, is empty, or ALERT_FILE_PATH is unset.
    """
    if not ALERT_FILE_PATH:
        return None
    try:
        with open(ALERT_FILE_PATH, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
        last_line = next((line for line in reversed(lines) if line.strip()), None)
        if last_line:
            return datetime.fromisoformat(last_line.strip())
    except FileNotFoundError:
        pass  # Normal on first run
    except Exception as e:
        logging.warning("Failed to read alert file '%s': %s", ALERT_FILE_PATH, e)
    return None


def _append_alert_time() -> None:
    """Append the current UTC time in ISO 8601 format to ALERT_FILE_PATH."""
    if not ALERT_FILE_PATH:
        return
    try:
        with open(ALERT_FILE_PATH, "a", encoding="utf-8") as f:
            f.write(datetime.now(timezone.utc).isoformat() + "\n")
    except Exception as e:
        logging.warning("Failed to write alert file '%s': %s", ALERT_FILE_PATH, e)

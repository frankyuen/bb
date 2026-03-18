# Garden BB

A hobbyist webcam monitor for home use.

---

## About

- A simple, **hobbyist-grade** home security tool — not production software
- Runs on a **Raspberry Pi 4** connected to a USB webcam
- Serves a live video stream and detects motion, saving snapshots and sending email alerts
- **Privacy first:** no cloud dependency, no third-party services — everything stays local
- Intended for **home use only**, best run behind a firewall or accessed through a VPN
- The HTTP stream is unauthenticated — do **not** expose it directly to the internet
- Motion snapshots are stored on local disk; alert emails go through your own SMTP server

---

## Features

### Live Streaming Mode

- Captures frames from the USB webcam in a background thread
- Serves an MJPEG stream over plain HTTP
- Port is configurable via `STREAM_PORT` (default: `8080`)
- Access the stream at `http://<host>:<port>/`

### Monitor Mode

- Captures a configurable number of frames per scan cycle (`LOOP_PER_SCAN`, default: 400)
- Detects motion using frame differencing between consecutive frames
- Filters out sensor noise with a contour-area threshold (`NOISE_THRESHOLD`, default: 500 px²)
- On motion detection:
  - Draws bounding boxes on the motion frame
  - Saves the annotated frame as a timestamped `.jpg` in `IMAGE_DIR`
  - Sends an email alert (rate-limited by `ALERT_INTERVAL_SECS`) via your SMTP server
- When no motion is detected, optionally saves a plain snapshot if `SAVE_SNAPSHOT` is set
- Sleeps between scan cycles (`SCAN_INTERVAL_SECS`, default: 60 s) and repeats
- Supports a `--run-once-only` flag to execute a single scan cycle and exit (useful for cron jobs)

---

## Quick Start

### 1. Install dependencies

```bash
pipenv install
```

### 2. Configure environment

Copy or create a `.env` file in the project directory:

```ini
# --- Live stream ---
STREAM_PORT=8080

# --- Monitor ---
LOOP_PER_SCAN=400          # frames captured per scan cycle
NOISE_THRESHOLD=500        # minimum contour area (px²) to count as motion
SCAN_INTERVAL_SECS=60      # seconds to sleep between scan cycles
IMAGE_DIR=/path/to/images  # directory for saved snapshots
SAVE_SNAPSHOT=             # set to any value to save snapshots even without motion
IMAGE_WIDTH=1280           # capture resolution width
IMAGE_HEIGHT=720           # capture resolution height

# --- Alerts ---
ALERT_FILE_PATH=/path/to/alert_log.txt  # log file for alert timestamps
ALERT_INTERVAL_SECS=1800                # minimum seconds between email alerts
EMAIL_SERVER=smtp.example.com           # SMTP host (no auth, plain SMTP)
SENDER=sender@example.com
RECIPIENT=recipient@example.com
```

### 3. Run

**Live streaming mode** — serves the webcam stream over HTTP:

```bash
pipenv run python main.py --mode live
```

**Monitor mode** — continuous motion detection loop:

```bash
pipenv run python main.py --mode monitor
```

**Monitor mode, single scan** — run one cycle and exit (suitable for cron):

```bash
pipenv run python main.py --mode monitor --run-once-only
```

### Command-line options

| Option            | Mode    | Description                        |
| ----------------- | ------- | ---------------------------------- |
| `--mode live`     | —       | Start the HTTP live stream server  |
| `--mode monitor`  | —       | Start the motion detection monitor |
| `--run-once-only` | monitor | Run a single scan cycle then exit  |

---

## Hardware

- Raspberry Pi 4 Model B (8 GB RAM recommended)
- USB webcam (or any V4L2-compatible camera at `/dev/video0`)
- 50+ GB free disk space for snapshot storage

## Software

- Raspberry Pi OS (Debian 12)
- Python 3.11+
- `pipenv` for dependency management
- `opencv-python-headless` (headless, no GUI required)

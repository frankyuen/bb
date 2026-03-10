# Project Specification

## Project Goal

This goal of this project/app is to provide the following features:

- a live video streaming server with the use of a USB webcam
- detect motions and take still photo

## Hardware

The app targets to run using the following hardware configuration

- Raspberry Pi 4 Model B with 8 GB of RAM
- Free disk space more than 50 GB for the app to run
- Logitech C310 webcam connected via USB

## Software

- Raspberry Pi OS of Debian version 12
- Python version 3.11
- Use `pipenv` as the Python package manager
- The server runs headless (no display/GUI); use `opencv-python-headless` instead of `opencv-python`

## Runtime

- The app is designed to be able to run on Python version 3.11 or later

## Features

The app should be designed to start in one of the two modes, controlled by passing a command line argument:

- live webcam video streaming mode
- monitor mode

### Live Webcam Video Streaming Mode

- Since the app use `pipenv`, this mode should be started using the command `pipenv run python main.py --mode live`
- The app should read `.env` when starting
- In this mode, the app serves the live stream over HTTP on a port configurable by an env var (`STREAM_PORT`)

### Monitor Mode

- Since the app use `pipenv`, this mode should be started using the command `pipenv run python main.py --mode monitor`
- The app should read `.env` when starting
- The monitoring logic is as follows:
  - capture a number of frames as determined by an env var `LOOP_PER_SCAN`, default to an integer of 400
  - detect any motion among the captured frames, filter out noise by applying a threshold configurable by an env var `NOISE_THRESHOLD` with an integer value, suggest a default
  - if any motion above the threshold is detected, call an alert control function
  - the alert control function will do the following:
    - read the last line of a local file, with the path configurable in an env var `ALERT_FILE_PATH`. Each line of the file is the time in ISO 8601 when the monitor logic was run. Reading the last line will get the most recent execution time of the monitor logic
    - only if the time delta between the system time and the last execution time exceeds a configurable threshold in seconds (env var `ALERT_INTERVAL_SECS` with an integer value), send an email alert by using the module `emailer.py`. `subject_text` should be the string "Motion detected" and `body_text` should be a summary text of the detected motion
    - unconditionally append a line to that local file with the system time in ISO 8601 format
  - if either any motion above the threshold is detected, or if an env var `SAVE_SNAPSHOT` is set, save the middle frame as a `.jpg` file with the filename as evaluated to `datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")` in a directory configurable by an env var `IMAGE_DIR`
  - unconditionally release the camera
  - sleep for a duration configurable in an env var `SCAN_INTERVAL_SECS` with an integer value
  - then repeat the monitoring logic

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

TBC

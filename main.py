"""
Entry point for Garden BB. Start the app in one of two modes:

  pipenv run python main.py --mode live     # HTTP live webcam stream
  pipenv run python main.py --mode monitor  # Motion detection monitor
"""

import argparse
from os import getenv
from dotenv import load_dotenv
import logging


def config_logger():
    logging.basicConfig(
        format="[%(asctime)s][%(levelname)s] - %(message)s", level=logging.INFO
    )


def main():
    config_logger()

    load_dotenv()

    parser = argparse.ArgumentParser(description="Garden BB")
    parser.add_argument(
        "--mode",
        choices=["live", "monitor"],
        required=True,
        help="Operating mode",
    )
    args = parser.parse_args()

    if args.mode == "live":
        port = int(getenv("STREAM_PORT", "8080"))
        from streamer import WebcamStreamer
        from server import run_server

        streamer = WebcamStreamer()
        streamer.start()
        logging.info("*** Live stream started on http://0.0.0.0:%s ***", port)
        try:
            run_server(streamer, port)
        except KeyboardInterrupt:
            pass
        finally:
            streamer.stop()
            logging.info("Streamer stopped")

    elif args.mode == "monitor":
        from monitor import run_monitor

        try:
            run_monitor()
        except KeyboardInterrupt:
            pass
        finally:
            logging.info("Monitor stopped")


if __name__ == "__main__":
    main()

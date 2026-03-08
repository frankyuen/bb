import time
from flask import Flask, Response

app = Flask(__name__)
_streamer = None

_VIEWER_HTML = """<!DOCTYPE html>
<html>
<head><title>Live Stream</title></head>
<body style="margin:0;background:#000;display:flex;justify-content:center;align-items:center;height:100vh;">
  <img src="/stream" style="max-width:100%;max-height:100vh;">
</body>
</html>"""


@app.route("/")
def index():
    return _VIEWER_HTML


@app.route("/stream")
def stream():
    return Response(_generate(), mimetype="multipart/x-mixed-replace; boundary=frame")


def _generate():
    while True:
        frame = _streamer.get_frame()
        if frame is None:
            time.sleep(0.01)
            continue
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
        )


def run_server(streamer, port):
    global _streamer
    _streamer = streamer
    app.run(host="0.0.0.0", port=port, threaded=True)

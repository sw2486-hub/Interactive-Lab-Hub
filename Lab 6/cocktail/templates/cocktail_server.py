#!/usr/bin/env python3
"""Local Flask + MQTT-to-SSE bridge for Color Cocktail Bar.

Place this file in Lab 6/cocktail/ and the HTML in cocktail/templates/.
Activate Lab 6/.venv and run: python cocktail_server.py
Open http://<Pi-IP>:8000 and select Live sensors > Connect.

Input topics: IDD/sw2486/cocktail/input/A (or /B, /C)
Payload: {"station":"A","color":"RED","rgb":[131,44,36]}
Publish non-retained heartbeats every 0.5-1 second.
Valid colors: RED, GREEN, BLUE, NONE, UNKNOWN.

Optional environment: COCKTAIL_TEAM, MQTT_HOST, MQTT_PORT, MQTT_USER,
MQTT_PASSWORD, COCKTAIL_PORT. All players must use the same team name.
This is a local classroom development server.
"""
import json
import logging
import math
import os
from pathlib import Path
import queue
import re
import threading
import uuid

from flask import Flask, Response, jsonify, render_template
import paho.mqtt.client as mqtt

TEAM = os.environ.get("COCKTAIL_TEAM", "sw2486")
if not re.fullmatch(r"[A-Za-z0-9_-]{1,48}", TEAM):
    raise ValueError("COCKTAIL_TEAM must contain 1-48 letters, digits, underscores or hyphens")
TOPIC_PREFIX = f"IDD/{TEAM}/cocktail/input/"
MQTT_HOST = os.environ.get("MQTT_HOST", "farlab.infosci.cornell.edu")
MQTT_PORT = int(os.environ.get("MQTT_PORT", "1883"))
PORT = int(os.environ.get("COCKTAIL_PORT", "8000"))
app = Flask(__name__, template_folder=str(Path(__file__).resolve().parent / "templates"))
listeners = set()
listeners_lock = threading.Lock()
connection = threading.Event()
log = logging.getLogger("cocktail")


def validate_message(topic, payload, retained=False):
    """Reject malformed, retained, wrong-topic and mismatched-station messages."""
    if retained or not topic.startswith(TOPIC_PREFIX):
        return None
    station = topic[len(TOPIC_PREFIX):]
    if station not in ("A", "B", "C") or len(payload) > 4096:
        return None
    try:
        data = json.loads(payload)
    except (ValueError, UnicodeError, TypeError):
        return None
    if not isinstance(data, dict) or data.get("station") != station:
        return None
    if data.get("color") not in ("RED", "GREEN", "BLUE", "NONE", "UNKNOWN"):
        return None
    clean = {"station": station, "color": data["color"]}
    rgb = data.get("rgb")
    if (isinstance(rgb, list) and len(rgb) == 3
            and all(type(n) in (int, float) and math.isfinite(n) and 0 <= n <= 65535 for n in rgb)):
        clean["rgb"] = rgb
    return clean


def broadcast(data):
    encoded = json.dumps(data, separators=(",", ":"), allow_nan=False)
    with listeners_lock:
        for mailbox in tuple(listeners):
            try:
                mailbox.put_nowait(encoded)
            except queue.Full:
                # Drop queued old readings rather than replaying a stale selection.
                try:
                    while True:
                        mailbox.get_nowait()
                except queue.Empty:
                    pass
                mailbox.put_nowait(encoded)


def on_connect(client, userdata, flags, rc, *extra):
    if rc == 0:
        connection.set()
        client.subscribe(TOPIC_PREFIX + "+", qos=0)
        log.info("MQTT connected; listening on %s+", TOPIC_PREFIX)
    else:
        connection.clear()
        log.error("MQTT connection rejected: %s", rc)


def on_disconnect(client, userdata, *args):
    connection.clear()
    log.warning("MQTT disconnected; automatic reconnect enabled")
    # Immediately clear browser selections. Missing heartbeats also expire after 5s.
    for station in ("A", "B", "C"):
        broadcast({"station": station, "color": "UNKNOWN"})


def on_message(client, userdata, message):
    data = validate_message(message.topic, message.payload, message.retain)
    if data is not None:
        broadcast(data)


@app.get("/")
def index():
    return render_template("color_cocktail_bar.html")


@app.get("/api/health")
def health():
    return jsonify(team=TEAM, mqtt_connected=connection.is_set(), input_topic=TOPIC_PREFIX + "+")


@app.get("/api/events")
def events():
    mailbox = queue.Queue(maxsize=32)
    # Register before returning; no old readings are cached or replayed.
    with listeners_lock:
        listeners.add(mailbox)

    def stream():
        try:
            yield ": connected\n\n"
            while True:
                try:
                    yield "data: " + mailbox.get(timeout=2) + "\n\n"
                except queue.Empty:
                    yield ": keepalive\n\n"
        finally:
            with listeners_lock:
                listeners.discard(mailbox)

    response = Response(stream(), mimetype="text/event-stream", headers={
        "Cache-Control": "no-cache, no-store",
        "X-Accel-Buffering": "no",
    })
    response.call_on_close(lambda: remove_listener(mailbox))
    return response


def remove_listener(mailbox):
    with listeners_lock:
        listeners.discard(mailbox)


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    # Keyword arguments work with both the installed Paho 1.6 and Paho 2.x.
    client = mqtt.Client(client_id="cocktail-web-" + uuid.uuid4().hex[:10], clean_session=True)
    client.username_pw_set(os.environ.get("MQTT_USER", "idd"),
                           os.environ.get("MQTT_PASSWORD", "device@theFarm"))
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    client.reconnect_delay_set(min_delay=1, max_delay=15)
    client.connect_async(MQTT_HOST, MQTT_PORT, keepalive=30)
    client.loop_start()
    print(f"\nColor Cocktail Bar - team {TEAM}")
    print(f"Open http://<your-Pi-IP>:{PORT}")
    print("Select Live sensors, then Connect. Ctrl+C to stop.\n", flush=True)
    try:
        app.run(host="0.0.0.0", port=PORT, threaded=True, debug=False, use_reloader=False)
    finally:
        client.disconnect()
        client.loop_stop()


if __name__ == "__main__":
    main()

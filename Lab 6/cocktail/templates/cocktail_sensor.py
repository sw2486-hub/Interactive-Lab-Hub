#!/usr/bin/env python3
"""APDS-9960 input for Color Cocktail Bar.

Run in Lab 6/.venv:
  python cocktail_sensor.py --station A

Team default: sw2486 (must match cocktail_server.py).
The built-in calibration is for Shenye's tested sensor and color objects ONLY.
Other Pis should use --calibration their-own-colors.json.
Calibration JSON shape:
 {"RED":[131,45,36],"GREEN":[52,82,51],
  "BLUE":[353,434,370],"NONE":[1037,889,661]}
Values are raw RGB means; they are normalized automatically.

MQTT topic: IDD/<team>/cocktail/input/<station>
Non-retained heartbeat every 0.5s; 3 consistent samples confirm a change.
"""
import argparse
import json
import math
import os
from pathlib import Path
import re
import time
import uuid

DEFAULT_REFERENCES = {
    "RED": (0.620, 0.211, 0.169),
    "GREEN": (0.277, 0.454, 0.269),
    "BLUE": (0.299, 0.390, 0.311),
    "NONE": (0.402, 0.344, 0.254),
}


def normalize_rgb(values):
    if not isinstance(values, (list, tuple)) or len(values) != 3:
        raise ValueError("RGB must contain three numbers")
    if not all(type(n) in (int, float) and math.isfinite(n) and n >= 0 for n in values):
        raise ValueError("RGB must contain finite non-negative numbers")
    total = sum(values)
    if total <= 0:
        raise ValueError("RGB total must be positive")
    return tuple(n / total for n in values)


def load_references(path):
    if path is None:
        return DEFAULT_REFERENCES
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or set(data) != set(DEFAULT_REFERENCES):
        raise ValueError("Calibration requires exactly RED, GREEN, BLUE and NONE")
    return {name: normalize_rgb(data[name]) for name in data}


def classify(rgb, light, references):
    if light <= 5:
        return "UNKNOWN"
    try:
        normalized = normalize_rgb(rgb)
    except ValueError:
        return "UNKNOWN"
    scores = sorted(
        (math.sqrt(sum((x - y) ** 2 for x, y in zip(normalized, reference))), label)
        for label, reference in references.items()
    )
    if scores[0][0] < 0.07 and scores[1][0] - scores[0][0] > 0.02:
        return scores[0][1]
    return "UNKNOWN"


class StableColor:
    def __init__(self, samples=3):
        self.samples = samples
        self.candidate = None
        self.count = 0
        self.color = "UNKNOWN"

    def update(self, label):
        if label == self.candidate:
            self.count += 1
        else:
            self.candidate, self.count = label, 1
        if self.count >= self.samples:
            self.color = label
        return self.color


def main():
    parser = argparse.ArgumentParser(description="Send calibrated sensor colors to the cocktail bar")
    parser.add_argument("--station", required=True, choices=("A", "B", "C"))
    parser.add_argument("--team", default=os.environ.get("COCKTAIL_TEAM", "sw2486"))
    parser.add_argument("--calibration", help="JSON file with this Pi's own color samples")
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,48}", args.team):
        parser.error("Team must contain 1-48 letters, digits, underscores or hyphens")
    references = load_references(args.calibration)

    import board
    import busio
    from adafruit_apds9960.apds9960 import APDS9960
    import paho.mqtt.client as mqtt

    topic = f"IDD/{args.team}/cocktail/input/{args.station}"
    i2c = busio.I2C(board.SCL, board.SDA)
    sensor = APDS9960(i2c)
    sensor.enable_color = True
    time.sleep(1)
    client = mqtt.Client(client_id="cocktail-" + args.station + "-" + uuid.uuid4().hex[:8], clean_session=True)
    client.username_pw_set(os.environ.get("MQTT_USER", "idd"),
                           os.environ.get("MQTT_PASSWORD", "device@theFarm"))
    empty = json.dumps({"station": args.station, "color": "UNKNOWN"})
    client.will_set(topic, payload=empty, qos=0, retain=False)

    def on_connect(client, userdata, flags, rc, *extra):
        print("MQTT connected" if rc == 0 else f"MQTT connection rejected: {rc}", flush=True)

    def on_disconnect(client, userdata, *extra):
        print("MQTT disconnected; retrying automatically", flush=True)

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.reconnect_delay_set(min_delay=1, max_delay=15)
    client.connect_async(os.environ.get("MQTT_HOST", "farlab.infosci.cornell.edu"),
                         int(os.environ.get("MQTT_PORT", "1883")), keepalive=15)
    client.loop_start()
    stable = StableColor()
    last_publish = -1.0
    failed = False
    print(f"Station {args.station} | Team {args.team} | {topic}", flush=True)
    if not args.calibration:
        print("Using Shenye's calibration. Other Pis need their own samples.", flush=True)
    print("Show RED, GREEN or BLUE. Remove the card to clear. Ctrl+C to stop.", flush=True)
    try:
        while True:
            try:
                r, g, b, light = sensor.color_data
                rgb = [r, g, b]
                color = stable.update(classify(rgb, light, references))
                if failed:
                    print("Sensor recovered", flush=True)
                failed = False
            except (OSError, RuntimeError) as error:
                if not failed:
                    print(f"Sensor error: {error}", flush=True)
                failed = True
                stable = StableColor()
                color, rgb = "UNKNOWN", None
            now = time.monotonic()
            if now - last_publish >= 0.5:
                payload = {"station": args.station, "color": color}
                if rgb is not None:
                    payload["rgb"] = rgb
                if client.is_connected():
                    result = client.publish(topic, json.dumps(payload), qos=0, retain=False)
                    state = "SENT" if result.rc == mqtt.MQTT_ERR_SUCCESS else "SEND ERROR"
                else:
                    state = "WAITING FOR MQTT"
                print(f"{state} | {args.station} | {color} | RGB={rgb}", flush=True)
                last_publish = now
            time.sleep(0.15)
    except KeyboardInterrupt:
        print("\nStopping sensor publisher.", flush=True)
    finally:
        if client.is_connected():
            result = client.publish(topic, empty, qos=0, retain=False)
            try:
                result.wait_for_publish(timeout=1)
            except RuntimeError:
                pass
        client.disconnect()
        client.loop_stop()
        try:
            sensor.enable_color = False
        finally:
            i2c.deinit()


if __name__ == "__main__":
    main()

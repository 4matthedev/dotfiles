#!/usr/bin/env python3
import json, os, time, subprocess

IFACE = "enp3s0"
CACHE = os.path.expanduser("~/.cache/network-waybar.json")
ICON = "\uf0ac"

def read_bytes():
    with open("/proc/net/dev") as f:
        for line in f:
            if ":" in line:
                name, rest = line.split(":", 1)
                name = name.strip()
                if name == IFACE:
                    vals = rest.split()
                    return int(vals[0]), int(vals[8])  # rx bytes, tx bytes
    return 0, 0

# IP
try:
    ip = subprocess.check_output(["ip", "-4", "addr", "show", IFACE], text=True).split()
    ip = [x for x in ip if "/" in x][0].split("/")[0]
except Exception:
    ip = "?"

rx, tx = read_bytes()
now = time.time()
prev = None
try:
    import json as _j
    with open(CACHE) as f:
        prev = _j.load(f)
except Exception:
    pass

down_mbps = 0.0
up_mbps = 0.0
if prev:
    dt = now - prev["t"]
    if dt > 0:
        down_mbps = (rx - prev["rx"]) * 8 / dt / 1e6
        up_mbps = (tx - prev["tx"]) * 8 / dt / 1e6
        if down_mbps < 0: down_mbps = 0
        if up_mbps < 0: up_mbps = 0

with open(CACHE, "w") as f:
    json.dump({"t": now, "rx": rx, "tx": tx}, f)

tooltip = f"Interface: {IFACE}\nIP: {ip}\nDown: {down_mbps:.2f} Mbps\nUp: {up_mbps:.2f} Mbps"
print(json.dumps({"text": ICON, "tooltip": tooltip}))

#!/usr/bin/env python3
import json, urllib.request, os, struct, glob

URL = "http://127.0.0.1:8080"
MODELS_DIR = os.path.expanduser("~/models")
PRESET = os.path.join(MODELS_DIR, "models.ini")
import configparser
def load_preset():
    cp = configparser.ConfigParser()
    if os.path.exists(PRESET):
        cp.read(PRESET)
    return cp
PRESET_CFG = load_preset()
FILE_TYPE_MAP = {
    0:"F32",1:"F16",2:"Q4_0",3:"Q4_1",7:"Q8_0",8:"Q5_0",9:"Q5_1",
    10:"Q2_K",11:"Q3_K_S",12:"Q3_K_M",13:"Q3_K_L",14:"Q4_K_S",15:"Q4_K_M",
    16:"Q5_K_S",17:"Q5_K_M",18:"Q6_K",19:"IQ2_XXS",20:"IQ2_XS",21:"IQ3_XXS",
    22:"IQ1_S",23:"IQ4_NL",24:"IQ3_S",25:"IQ2_S",26:"IQ4_XS",27:"I8",28:"I16",
    29:"I32",30:"I64",31:"F64",32:"IQ1_M",33:"BF16",34:"Q4_0_4_4",35:"Q4_0_4_8",
    36:"Q4_0_8_8",37:"TQ1_0",38:"TQ2_0",
    143:"PTQ1_0",
}

def read_str(f):
    (n,) = struct.unpack("<Q", f.read(8))
    return f.read(n).decode("utf-8", "replace")

def read_val(f, vtype):
    if vtype == 0: return struct.unpack("<B", f.read(1))[0]
    if vtype == 1: return struct.unpack("<b", f.read(1))[0]
    if vtype == 2: return struct.unpack("<H", f.read(2))[0]
    if vtype == 3: return struct.unpack("<h", f.read(2))[0]
    if vtype == 4: return struct.unpack("<I", f.read(4))[0]
    if vtype == 5: return struct.unpack("<i", f.read(4))[0]
    if vtype == 6: return struct.unpack("<f", f.read(4))[0]
    if vtype == 7: return bool(struct.unpack("<B", f.read(1))[0])
    if vtype == 8: return read_str(f)
    if vtype == 9:
        (atype,) = struct.unpack("<I", f.read(4))
        (n,) = struct.unpack("<Q", f.read(8))
        return [read_val(f, atype) for _ in range(n)]
    if vtype == 10: return struct.unpack("<Q", f.read(8))[0]
    if vtype == 11: return struct.unpack("<q", f.read(8))[0]
    if vtype == 12: return struct.unpack("<d", f.read(8))[0]
    raise ValueError(f"unknown type {vtype}")

def parse_gguf(path):
    with open(path, "rb") as f:
        if f.read(4) != b"GGUF": return {}
        (ver,) = struct.unpack("<I", f.read(4))
        (nt,) = struct.unpack("<Q", f.read(8))
        (nkv,) = struct.unpack("<Q", f.read(8))
        meta = {}
        for _ in range(nkv):
            key = read_str(f)
            (vt,) = struct.unpack("<I", f.read(4))
            meta[key] = read_val(f, vt)
    return meta

def human(n):
    for u in ["B","KB","MB","GB","TB"]:
        if n < 1024: return f"{n:.2f} {u}"
        n /= 1024
    return f"{n:.2f} PB"


def bar(pct, width=20):
    pct = max(0, min(100, pct))
    filled = int(round(width * pct / 100))
    return "[" + "#" * filled + "-" * (width - filled) + f"] {pct:.0f}%"

out = {"text": "󰧑", "tooltip": "", "class": "inactive"}

# health
try:
    with urllib.request.urlopen(URL + "/health", timeout=2) as r:
        health = json.load(r)
except Exception:
    out["text"] = "󰧑 off"
    out["tooltip"] = "llama.cpp server not running"
    print(json.dumps(out)); raise SystemExit(0)

# props
try:
    with urllib.request.urlopen(URL + "/props", timeout=2) as r:
        props = json.load(r)
except Exception:
    props = {}

# models from router
try:
    with urllib.request.urlopen(URL + "/v1/models", timeout=3) as r:
        models = json.load(r).get("data", [])
except Exception:
    models = []

lines = []
lines.append("llama.cpp — Prism ML fork")
lines.append(f"Health: {health.get('status','?')}")
lines.append(f"Role: {props.get('role','?')}  |  max instances: {props.get('max_instances','?')}")
lines.append(f"Models dir: {MODELS_DIR}")
lines.append("")

# nvidia-smi info
try:
    import subprocess
    gpu_raw = subprocess.check_output(
        ["nvidia-smi","--query-gpu=name,memory.total,memory.used,memory.free,utilization.gpu","--format=csv,noheader"],
        text=True, timeout=3).strip()
    lines.append("GPU:")
    for g in gpu_raw.splitlines():
        parts = [x.strip() for x in g.split(",")]
        # name, mem total, mem used, mem free, util
        name = parts[0]
        mem_total = float(parts[1].split()[0])
        mem_used = float(parts[2].split()[0])
        mem_free = float(parts[3].split()[0])
        util = float(parts[4].split()[0]) if len(parts) > 4 and parts[4] else 0
        vram_pct = mem_used / mem_total * 100 if mem_total else 0
        lines.append(f"  {name}")
        lines.append(f"  VRAM: {mem_used:.0f}/{mem_total:.0f} MiB  {bar(vram_pct)}")
        lines.append(f"  GPU util: {bar(util)}")
    # process memory
    proc_out = subprocess.check_output(
        ["nvidia-smi","--query-compute-apps=pid,used_memory","--format=csv,noheader"],
        text=True, timeout=3).strip()
    llama_vram = "none (model not loaded / CPU only)"
    for row in proc_out.splitlines():
        parts = [x.strip() for x in row.split(",")]
        if len(parts) >= 2 and parts[0] in (str(os.getpid()),): pass
    # find llama-server pid
    try:
        pids = subprocess.check_output(["pgrep","-f","llama-server"], text=True, timeout=3).split()
    except Exception:
        pids = []
    for row in proc_out.splitlines():
        parts = [x.strip() for x in row.split(",")]
        if len(parts) >= 2 and parts[0] in pids:
            llama_vram = parts[1]
    lines.append(f"  llama-server VRAM: {llama_vram}")
    # RSS of llama-server process
    try:
        pids = subprocess.check_output(["pgrep","-f","llama-server"], text=True, timeout=3).split()
        rss = 0
        for pid in pids:
            try:
                with open(f"/proc/{pid}/statm") as fh:
                    rss_pages = int(fh.read().split()[1])
                rss += rss_pages * 4096
            except Exception:
                pass
        if rss:
            lines.append(f"  llama-server RAM (RSS): {human(rss)}")
    except Exception:
        pass
except Exception as e:
    lines.append(f"GPU info unavailable: {e}")
lines.append("")

gguf_files = sorted(glob.glob(os.path.join(MODELS_DIR, "*.gguf")))
if not models and not gguf_files:
    lines.append("No models found.")
else:
    lines.append("Models:")
    for m in (models if models else []):
        mid = m.get("id", "?")
        st = m.get("status", {}).get("value", "?")
        ctx = m.get("context_length", "?")
        sec = mid if PRESET_CFG.has_section(mid) else None
        cfg_ctx = PRESET_CFG.get(sec, "ctx-size", fallback=None) if sec else None
        cfg_kv = PRESET_CFG.get(sec, "cache-type-k", fallback=None) if sec else None
        path = os.path.join(MODELS_DIR, mid + ".gguf")
        meta = parse_gguf(path) if os.path.exists(path) else {}
        arch = meta.get("general.architecture", "?")
        name = meta.get("general.name", mid)
        ftype = meta.get("general.file_type")
        quant = FILE_TYPE_MAP.get(ftype, str(ftype)) if ftype is not None else "?"
        size = human(os.path.getsize(path)) if os.path.exists(path) else "?"
        lines.append(f"  • {name}  [{mid}]")
        lines.append(f"      status: {st}")
        lines.append(f"      quant: {quant}  |  size: {size}")
        if cfg_ctx:
            lines.append(f"      context window: {cfg_ctx} (configured)  [max {ctx}]")
        else:
            lines.append(f"      context window: {ctx}")
        if cfg_kv:
            lines.append(f"      KV cache: {cfg_kv}")
        lines.append(f"      GPU offload: {'yes' if st=='loaded' else 'n/a (not loaded)'}")
        lines.append("")

# set text/class based on loaded models
loaded_ids = [m.get("id") for m in models if m.get("status", {}).get("value") == "loaded"]
if loaded_ids:
    out["text"] = "󰧑 " + loaded_ids[0]
    out["class"] = "active"
elif models:
    out["text"] = "󰧑 " + str(len(models))
    out["class"] = "idle"
else:
    out["text"] = "󰧑 0"
    out["class"] = "idle"

import html as _html
out["tooltip"] = _html.escape("\n".join(lines))
print(json.dumps(out))

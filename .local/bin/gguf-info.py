#!/usr/bin/env python3
import struct, sys, os, json

def read_str(f):
    (n,) = struct.unpack("<Q", f.read(8))
    return f.read(n).decode("utf-8", "replace")

def read_val(f, vtype):
    if vtype == 0:  # UINT8
        return struct.unpack("<B", f.read(1))[0]
    if vtype == 1:  # INT8
        return struct.unpack("<b", f.read(1))[0]
    if vtype == 2:  # UINT16
        return struct.unpack("<H", f.read(2))[0]
    if vtype == 3:  # INT16
        return struct.unpack("<h", f.read(2))[0]
    if vtype == 4:  # UINT32
        return struct.unpack("<I", f.read(4))[0]
    if vtype == 5:  # INT32
        return struct.unpack("<i", f.read(4))[0]
    if vtype == 6:  # FLOAT32
        return struct.unpack("<f", f.read(4))[0]
    if vtype == 7:  # BOOL
        return bool(struct.unpack("<B", f.read(1))[0])
    if vtype == 8:  # STRING
        return read_str(f)
    if vtype == 9:  # ARRAY
        (atype,) = struct.unpack("<I", f.read(4))
        (n,) = struct.unpack("<Q", f.read(8))
        return [read_val(f, atype) for _ in range(n)]
    if vtype == 10:  # UINT64
        return struct.unpack("<Q", f.read(8))[0]
    if vtype == 11:  # INT64
        return struct.unpack("<q", f.read(8))[0]
    if vtype == 12:  # FLOAT64
        return struct.unpack("<d", f.read(8))[0]
    raise ValueError(f"unknown type {vtype}")

def parse(path):
    with open(path, "rb") as f:
        magic = f.read(4)
        if magic != b"GGUF":
            raise ValueError("not GGUF")
        (ver,) = struct.unpack("<I", f.read(4))
        if ver not in (2,3):
            raise ValueError(f"version {ver}")
        (ntensors,) = struct.unpack("<Q", f.read(8))
        (nkv,) = struct.unpack("<Q", f.read(8))
        meta = {}
        for _ in range(nkv):
            key = read_str(f)
            (vtype,) = struct.unpack("<I", f.read(4))
            meta[key] = read_val(f, vtype)
        # tensor info not needed
    return ver, ntensors, meta

def human(n):
    for u in ["B","KB","MB","GB","TB"]:
        if n < 1024: return f"{n:.2f} {u}"
        n /= 1024
    return f"{n:.2f} PB"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: gguf-info.py <file.gguf> [--json]", file=sys.stderr); sys.exit(1)
    path = sys.argv[1]
    ver, ntensors, meta = parse(path)
    if "--json" in sys.argv:
        # convert non-serializable? all basic
        out = {"file": path, "version": ver, "tensors": ntensors, "metadata": meta}
        print(json.dumps(out, indent=2, default=str))
    else:
        print(f"File: {path}")
        print(f"Size: {human(os.path.getsize(path))}")
        print(f"GGUF version: {ver}")
        print(f"Tensors: {ntensors}")
        print(f"Metadata entries: {len(meta)}")
        print("")
        # print sorted keys
        for k in sorted(meta):
            v = meta[k]
            if isinstance(v, list):
                if len(v) > 8:
                    v = f"[{len(v)} items] " + ", ".join(str(x) for x in v[:8]) + "..."
            print(f"{k}: {v}")

#!/usr/bin/env bash
for f in /home/turker/models/*.gguf; do
  echo "============================================================"
  python3 /home/turker/.local/bin/gguf-info.py "$f"
  echo
done
echo "Press Enter to close..."
read -r

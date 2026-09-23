#!/usr/bin/env bash

VOICES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/voices"

python3 -m piper \
  --model en_US-lessac-medium \
  --data-dir "$VOICES_DIR" \
  --output-raw \
  -- "wo yao shuo zang hua" \
  | aplay -r 22050 -f S16_LE -t raw -

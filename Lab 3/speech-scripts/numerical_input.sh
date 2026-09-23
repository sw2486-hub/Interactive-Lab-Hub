#!/usr/bin/env bash

VOICES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/voices"

# Ask the user for a numerical input
python3 -m piper \
  --model en_US-lessac-medium \
  --data-dir "$VOICES_DIR" \
  --output-raw \
  -- "What is your five digit ZIP code?" \
  | aplay -D plughw:4,0 -r 22050 -f S16_LE -t raw -

# Give the user a moment to answer
sleep 1

# Record the answer for 5 seconds
arecord -D plughw:3,0 \
  -f S16_LE \
  -r 16000 \
  -c 1 \
  -d 5 \
  numerical_answer.wav

echo "Answer saved as numerical_answer.wav"

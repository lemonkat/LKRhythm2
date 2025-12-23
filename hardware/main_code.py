"""
Main input controller for LKRhythm2 hardware pads.

This script runs on a CircuitPython-compatible board (CPX or CPB) and 
translates physical touch pad inputs into HID keyboard signals ('a', 's', 'w', 'd').
It uses debouncing to ensure clean signals even with high-latency touch sensors.
"""
import board
import touchio
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
from adafruit_debouncer import Debouncer

# --- Configuration ---

THRESHOLD = 3000  # Raw touch value threshold for a "press"
DELAY = 0.005     # Debounce interval in seconds

# 1. Initialize the Keyboard device via USB HID
kbd = Keyboard(usb_hid.devices)

# 2. Define our 4 pads (Rhythm Game Layout)
# We will create a list of debouncer-wrapped pad objects for easy iteration.
DEBOUNCERS = []

# --- 3. Pad Setup & Hardware Detection ---

CPX_ID = "circuitplayground_express"
CPB_ID = "circuitplayground_bluefruit"

if board.board_id == CPB_ID:
    pads = [
        ("A1", touchio.TouchIn(board.A1)),
        ("A2", touchio.TouchIn(board.A2)),
        ("A5", touchio.TouchIn(board.A5)),
        ("A6", touchio.TouchIn(board.A6)),
    ]
else:
    pads = [
        ("A5", touchio.TouchIn(board.A5)),
        ("A7", touchio.TouchIn(board.A7)),
        ("A3", touchio.TouchIn(board.A3)),
        ("A1", touchio.TouchIn(board.A1)),
    ]

# Setup individual pads with their respective key mappings
# --- Pad 1 (Up/W) ---
touch_in_w = pads[0][1]
touch_in_w.threshold = THRESHOLD
DEBOUNCERS.append({
    "name": "Up (W)",
    "pad": Debouncer(touch_in_w, interval=DELAY),
    "key": Keycode.W
})

# --- Pad 2 (Left/A) ---
touch_in_a = pads[1][1]
touch_in_a.threshold = THRESHOLD
DEBOUNCERS.append({
    "name": "Left (A)",
    "pad": Debouncer(touch_in_a, interval=DELAY),
    "key": Keycode.A
})

# --- Pad 3 (Down/S) ---
touch_in_s = pads[2][1]
touch_in_s.threshold = THRESHOLD
DEBOUNCERS.append({
    "name": "Down (S)",
    "pad": Debouncer(touch_in_s, interval=DELAY),
    "key": Keycode.S
})

# --- Pad 4 (Right/D) ---
touch_in_d = pads[3][1]
touch_in_d.threshold = THRESHOLD
DEBOUNCERS.append({
    "name": "Right (D)",
    "pad": Debouncer(touch_in_d, interval=DELAY),
    "key": Keycode.D
})


print("--- CPX/CPB Pad Controller ---")
print("Native HID device initialized. Ready for input.")
print("Note: Ensure user is connected to the common ground pad.")
print("Mode: Debounced Tap-Only")

# --- Main Logic Loop ---
# This loop polls sensors as fast as possible to minimize input latency.
while True:
    for item in DEBOUNCERS:
        
        pad = item["pad"]
        
        # Poll the sensor state via the debouncer
        pad.update()

        # Check for a transition from "untouched" to "touched"
        # Since touchio values drop on touch, we use .fell for a "press"
        if pad.fell:
            
            # Print feedback to the serial console
            print(f"TAP: {item['name']}")
            
            # Send an immediate tap event to the host computer
            kbd.press(item["key"])
            kbd.release(item["key"])


# input CircuitPython script for an AdaFruit CPX or CPB

import board
import touchio
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
from adafruit_debouncer import Debouncer

# --- Configuration ---

THRESHOLD = 3000
DELAY = 0.002

# 1. Initialize the Keyboard device
kbd = Keyboard(usb_hid.devices)

# 2. Define our 4 pads (Rhythm Game Layout)
# We will create a list of debouncer objects.
# The Debouncer library handles all the complex timing and state.
DEBOUNCERS = []

# --- 3. Pad Setup & Manual Thresholds ---
# We create the TouchIn object, set its threshold,
# and then pass it to a Debouncer.

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
        ("A4", touchio.TouchIn(board.A4)),
        ("A5", touchio.TouchIn(board.A5)),
        ("A6", touchio.TouchIn(board.A6)),
        ("A7", touchio.TouchIn(board.A7)),
    ]

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


print("--- CPX DDR Pad Controller ---")
print("Native HID device initialized. Ready for input.")
print("Remember: Player must be connected to GND pad.")
print("Mode: Tap-Only (Debouncer Library)")

# --- Main Loop ---
# This loop runs as fast as possible for minimum latency.
while True:
    # Loop through all 4 of our configured pads
    for item in DEBOUNCERS:
        
        pad = item["pad"]
        
        # 1. Update the debouncer state
        # This MUST be called on every loop
        pad.update()

        # 2. Check for a NEW PRESS (Foot Down)
        # 'pad.rose' is True for only one loop when the
        # debounced state changes from False to True.
        # This inherently handles all press AND release bounce.
        if pad.fell:
            
            # --- This is a VALID new press ---
            
            print(f"TAP: {item['name']}")
            
            # 3. Send the key press
            kbd.press(item["key"])
            kbd.release(item["key"])
        
        # 'pad.fell' (True on release) is also available,
        # but we don't need it for this logic.a


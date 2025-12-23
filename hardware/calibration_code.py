"""
Calibration utility for LKRhythm2 hardware pads.

This script helps users find the optimal touch sensitivity thresholds 
for their physical pads when using a CircuitPython device (CPX or CPB).
It prints raw sensor values for each pad in a real-time loop.
"""
import time
import board
import touchio

# Hardware platform identifiers
CPX_ID = "circuitplayground_express"
CPB_ID = "circuitplayground_bluefruit"

# Initialize touch pads based on the detected board
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

print("--- CPX/CPB Pad Calibration Tool ---")
print("Connect all pads. Do not touch them.")
print("Watch the 'UNTOUCHED' values.")
print("Then, touch each pad with the GND clip and note the 'TOUCHED' value.")
print("Pick a new threshold safely between the two.")
print("\n")

while True:
    # Print a header and the raw sensor values for comparison
    header = ""
    values = ""
    for name, pad_obj in pads:
        header += f"{name}\t\t"
        values += f"{pad_obj.raw_value}\t\t"
    
    print(header)
    print(values)
    print("-" * 30)
    
    time.sleep(0.2)
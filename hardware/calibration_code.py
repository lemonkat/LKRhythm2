# calibration CircuitPython script for an AdaFruit CPX or CPB

import time
import board
import touchio

# This script helps you find the correct threshold values for your pads.

# 1. Set up all the pads we are using (A4, A5, A6, A7)
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

print("--- CPX Pad Calibration Tool ---")
print("Connect all pads. Do not touch them.")
print("Watch the 'UNTOUCHED' values.")
print("Then, touch each pad with the GND clip and note the 'TOUCHED' value.")
print("Pick a new threshold safely between the two.")
print("\n")

while True:
    # Print a header
    header = ""
    values = ""
    for name, pad_obj in pads:
        header += f"{name}\t\t"
        values += f"{pad_obj.raw_value}\t\t" # .raw_value gives the number
    
    print(header)
    print(values)
    print("-" * 30)
    
    time.sleep(0.2)
import time
from evdev import InputDevice, list_devices, ecodes
from gpiozero import Motor
from select import select

print("Starting...")

drive = Motor(forward="BOARD11", backward="BOARD13")

HOLD_TO_QUIT = 2.0 # seconds to hold B to quit

def find_controller():
	for path in list_devices():
		dev = InputDevice(path)
		if "xbox" in dev.name.lower():
			return dev
		return None

pad = find_controller()
if pad is None:
	raise SystemExit("No Xbox controller found. Press the Xbox buttont to connect it.")

print("Using:", pad.name)
caps = pad.capabilities().get(ecodes.EV_ABS, [])
codes = [c[0] if isinstance(c, tuple) else c for c in caps]
print("Axes available:", [ecodes.ABS.get(c,c) for c in codes])

RT = ecodes.ABS_GAS # Right trigger
LT = ecodes.ABS_BRAKE # left trigger
rt_max = pad.absinfo(RT).max
lt_max = pad.absinfo(LT).max
rt = lt = 0.0
b_down_since = None

try:
	while True:
		ready, _, _ = select([pad.fd], [], [], 0.1)
		if ready:
			for event in pad.read():
				if event.type == ecodes.EV_KEY and event.code == ecodes.BTN_EAST:
					if event.value == 1:
						b_down_since = time.monotonic()
					elif event.value == 0:
						b_down_since = None
				
				elif event.type == ecodes.EV_ABS:
					if event.code == RT:
						rt = event.value / rt_max
					elif event.code == LT:
						lt = event.value / lt_max
					else:
						continue

				speed = rt - lt

				if abs(speed) < 0.05:
					drive.stop()
				elif speed > 0:
					drive.forward(min(speed, 1))
				else:
					drive.backward(min(-speed,1))

		if b_down_since is not None and time.monotonic() - b_down_since >= HOLD_TO_QUIT:
			print("B held for 2 seconds, quitting...")
			break

except KeyboardInterrupt:
	pass

finally:
	drive.stop()

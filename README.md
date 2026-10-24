# Bluetooth RC Car (Raspberry Pi Zero 2 W + DRV8833)

A toy RC car rebuilt around a Raspberry Pi Zero 2 W. The car's original receiver board is replaced by a DRV8833 motor driver, and an Xbox One S controller (model 1708) connects directly to the Pi over Bluetooth. The right trigger drives forward, the left trigger drives in reverse, and holding **B** for 5 seconds quits the program.

Current status: rear (drive) motor works with the controller. Steering (front) motor is wired but not yet implemented in the control script.

## Hardware

| Part | Notes |
|---|---|
| Raspberry Pi Zero 2 W | With 40-pin header soldered on |
| DRV8833 motor driver breakout | Header pins must be **soldered** to the board |
| RC car with two brushed DC motors | Rear drive motor, front steering motor |
| 3x AA battery pack (about 4.5V) | Powers the motors through the DRV8833 |
| Xbox One S controller (model 1708) | Xbox Series X/S controllers also work |
| 5V supply for the Pi | Wall supply, or a USB power bank on the car |
| Breadboard and jumper wires | Signal wires only |

## Wiring

### Car wires

| Car wire | Label | Connects to |
|---|---|---|
| Red | B+ | DRV8833 **VM** |
| Black | B- | DRV8833 **GND** |
| Yellow | FM (rear motor A) | DRV8833 **AOUT1** |
| Blue | BM (rear motor B) | DRV8833 **AOUT2** |
| White | LM (front motor A) | DRV8833 **BOUT1** |
| Green | RM (front motor B) | DRV8833 **BOUT2** |

### Raspberry Pi to DRV8833

| DRV8833 pin | Pi physical pin | GPIO |
|---|---|---|
| nSLEEP | Pin 1 | 3.3V |
| AIN1 (IN1) | Pin 11 | GPIO17 |
| AIN2 (IN2) | Pin 13 | GPIO27 |
| BIN1 (IN3) | Pin 15 | GPIO22 |
| BIN2 (IN4) | Pin 16 | GPIO23 |
| GND | Pin 6 | Ground |

Notes:
- Pi GND, DRV8833 GND, and the battery black wire must share one ground.
- The Pi is powered separately from the motors (do not power the Pi from its GPIO pins through the motor battery without a proper 5V converter).
- Keep the DRV8833 VM input at 10.8V or less.
- The scripts use physical pin numbers via gpiozero's `BOARD` prefix (`"BOARD11"`), not GPIO numbers.
- High-current motor and battery wires need solid joints. Solder them to jumper ends or header pins rather than pushing bare wire into a breadboard.

## Pi setup

1. Flash **Raspberry Pi OS Lite (64-bit)** with Raspberry Pi Imager. In the settings, set a hostname, username, password, Wi-Fi (2.4 GHz) and country, and enable SSH with password authentication.
2. If your router offers it, set Wi-Fi security to **WPA2 only**. The Zero 2 W often fails to join WPA3 or WPA2/WPA3 mixed networks.
3. Boot the Pi, find its IP address (router app or `arp -a`), and connect:
   ```
   ssh YOURUSER@PI_IP
   ```
4. Update and install dependencies:
   ```
   sudo apt update && sudo apt full-upgrade -y
   sudo apt install -y bluez python3-evdev evtest
   sudo rfkill unblock bluetooth
   sudo systemctl enable --now bluetooth
   ```

## Bluetooth controller setup (one time)

The Xbox One S controller needs ERTM disabled to stay connected on Linux:

```
echo 1 | sudo tee /sys/module/bluetooth/parameters/disable_ertm
echo "options bluetooth disable_ertm=1" | sudo tee /etc/modprobe.d/bluetooth-ertm.conf
```

Pair the controller:

```
bluetoothctl
power on
agent on
default-agent
scan on
```

Hold the Xbox button to turn the controller on, then hold the small pair button on top until the light flashes rapidly. When `Xbox Wireless Controller` appears:

```
pair AA:BB:CC:DD:EE:FF
trust AA:BB:CC:DD:EE:FF
connect AA:BB:CC:DD:EE:FF
scan off
exit
```

Verify input with `sudo evtest` and pull the triggers.

## Running the car

Put the car on blocks with the wheels off the ground for the first test, then:

```
python3 xbox_drive.py
```

Turn on the controller by pressing the **Xbox button**, either before or within 60 seconds after starting the script. The script connects automatically, and you do not need to use `bluetoothctl` again.

### Controls

| Input | Action |
|---|---|
| Right trigger | Forward (speed proportional to pull) |
| Left trigger | Reverse (speed proportional to pull) |
| Hold **B** for 5 seconds | Stop the motor and quit |
| Ctrl+C | Quit from the terminal |

If the controller disconnects, the motor stops and the program exits.

## Project files

| File | Purpose |
|---|---|
| `xbox_drive.py` | Main control script: Bluetooth connect, trigger driving, hold-B quit |
| `test.py` | Basic motor test (drive and steering) without a controller |

## Troubleshooting

| Symptom | Likely cause and fix |
|---|---|
| Pi never appears on the network | Router set to WPA3 or mixed mode. Use WPA2 only, 2.4 GHz |
| SSH "connection refused" | SSH not enabled in `user-data` (`enable_ssh: true`), or you used the wrong IP |
| SSH "host identification has changed" | Run `ssh-keygen -R PI_IP`, then reconnect |
| Script prints messages but motors do nothing | Unsoldered header pins, loose motor or battery joints, nSLEEP not high, or no shared ground |
| Motor only works at high trigger values | Normal at 4.5V. Toy motors need some voltage to start |
| Right stick moves wheels, not triggers | Wrong axis codes. The script uses `ABS_GAS` (right trigger) and `ABS_BRAKE` (left trigger) |
| Controller connects, then drops | Disable ERTM (see above), update controller firmware with the Xbox Accessories app |
| `SyntaxError: expected 'except' or 'finally'` | A paste dropped part of the `bt()` function. Check with `python3 -m py_compile xbox_drive.py` |
| "No Xbox controller found" | Controller is off or not connected. Press the Xbox button and rerun |

## Safety

- Test with the wheels off the ground first.
- Unplug the battery if anything smells hot or smokes.
- The DRV8833 handles about 1.5A continuous per channel. A stalled motor can trip its thermal shutdown.
- Do not connect the battery's VM line to any Pi pin.

## Roadmap

- Add steering control (left stick) using the BIN1 and BIN2 channel
- Run the script on boot with a systemd service so the car works without SSH
- Power the Pi from the car (power bank, or a boost converter from the battery pack)
- Auto-reconnect if the controller drops mid-drive
- Mount the Pi, driver and battery securely on the chassis

# Industrial Safety Monitor

## What It Does
This system monitors temperature, vibration, and sound to detect safety hazards. It shows data on an LCD screen and sends information to a computer for ML analysis.

## Hardware Required
- Arduino Uno
- DHT22 (temperature sensor)
- MPU6050 (vibration sensor)
- KY-037 (sound sensor)
- 16x2 LCD Display
- Jumper wires and breadboard

## Wiring Connections

DHT22:
- VCC → 5V
- DATA → Pin 9
- GND → GND

MPU6050:
- VCC → 5V
- GND → GND
- SCL → A5
- SDA → A4

KY-037:
- VCC → 5V
- GND → GND
- A0 → A0

LCD 16x2:
- RS → Pin 12
- E → Pin 11
- D4 → Pin 5
- D5 → Pin 4
- D6 → Pin 3
- D7 → Pin 2
- VSS → GND
- VDD → 5V

## How to Use

1. Install Arduino IDE
2. Install libraries:
   - DHT sensor library
   - MPU6050_light
   - LiquidCrystal (built-in)
3. Upload code to Arduino
4. Open Serial Monitor (9600 baud)
5. Keep sensor still for first 2 seconds (calibration)

## What You See

LCD Display Shows:
- Row 1: Temperature (T:25.0°C) and Sound (S:512)
- Row 2: Vibration (V:0.045) and Status (OK)

When Anomaly Detected:
- LCD shows "!!! ALERT !!!"
- Alert message shows the problem

## Serial Output (for ML)

Format: temperature,vibration,sound
Example: 25.3,0.045,512

## Anomaly Thresholds

- Temperature: Below 10°C or Above 40°C
- Vibration: Above 0.2g
- Sound: Above 700

## Troubleshooting

MPU6050 Error:
- Check SDA/A4 and SCL/A5 connections
- Restart Arduino

No Temperature Reading:
- Add 10k resistor between DATA and VCC
- Check wiring

LCD Blank:
- Adjust contrast potentiometer
- Check backlight connection

## Files in This Project

- safety_monitor.ino - Main Arduino code
- wokwi/ - Virtual simulation files
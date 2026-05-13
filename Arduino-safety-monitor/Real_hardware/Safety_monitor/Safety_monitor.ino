#include <DHT.h>
#include <Wire.h>
#include <LiquidCrystal.h>
#include <MPU6050_light.h>

// ============================================
// Pin Definitions
// ============================================
#define DHTPIN 9
#define DHTTYPE DHT22
#define SOUND_ANALOG_PIN A0

// LCD Pins
LiquidCrystal lcd(12, 11, 5, 4, 3, 2);

// ============================================
// Objects
// ============================================
DHT dht(DHTPIN, DHTTYPE);
MPU6050 mpu(Wire);

// ============================================
// Variables
// ============================================
float temperature = 0;
float vibration = 0;
int sound = 0;

// Vibration detection
float vibrationMagnitude = 0;
float VIBRATION_THRESHOLD = 0.2;  // Changed from const to regular variable

// Simple anomaly detection
bool anomalyDetected = false;

unsigned long lastRead = 0;
unsigned long lastMPUUpdate = 0;
const long interval = 2000;  // Read DHT and sound every 2 seconds
const long mpuInterval = 50;  // Update MPU every 50ms

// MPU setup flag
bool mpuWorking = false;

// ============================================
// Setup
// ============================================
void setup() {
  Serial.begin(9600);
  
  // Initialize LCD
  lcd.begin(16, 2);
  lcd.print("Safety Monitor");
  lcd.setCursor(0, 1);
  lcd.print("Initializing...");
  delay(2000);
  
  // Initialize DHT22
  dht.begin();
  
  // Initialize sound sensor pin
  pinMode(SOUND_ANALOG_PIN, INPUT);
  
  // Initialize MPU6050
  lcd.clear();
  lcd.print("MPU6050 init...");
  Wire.begin();
  
  byte status = mpu.begin();
  Serial.print(F("MPU6050 status: "));
  Serial.println(status);
  
  if (status == 0) {
    lcd.setCursor(0, 1);
    lcd.print("Calculating...   ");
    delay(1000);
    mpu.calcOffsets();  // Calibrate - DO NOT MOVE sensor during this!
    mpuWorking = true;
    Serial.println(F("MPU6050 Ready!"));
  } else {
    lcd.setCursor(0, 1);
    lcd.print("MPU6050 ERROR!   ");
    mpuWorking = false;
    delay(2000);
  }
  
  // Ready message
  lcd.clear();
  lcd.print("System Ready!");
  delay(1000);
  lcd.clear();
  
  Serial.println("temperature,vibration,sound");
}

// ============================================
// Main Loop
// ============================================
void loop() {
  unsigned long current = millis();
   
  // Update MPU frequently for good vibration detection
  if (mpuWorking && (current - lastMPUUpdate >= mpuInterval)) {
    lastMPUUpdate = current;
    readVibration();
  }
  
  // Read DHT and sound at slower interval
  if (current - lastRead >= interval) {
    lastRead = current;
    
    // Read sensors
    readTemperature();
    readSound();
    
    // Simple anomaly detection
    detectAnomaly();
    
    // Update LCD
    updateLCD();
    
    // Send to Serial
    sendToSerial();
  }
}

// ============================================
// Read Temperature from DHT22
// ============================================
void readTemperature() {
  float t = dht.readTemperature();
  if (!isnan(t)) {
    temperature = t;
    // Debug output removed for cleaner serial
  } else {
    Serial.println("DHT22 Failed");
  }
}

// ============================================
// Read Sound Sensor (Analog)
// ============================================
void readSound() {
  // Take multiple readings and average for stability
  int sum = 0;
  for (int i = 0; i < 10; i++) {
    sum += analogRead(SOUND_ANALOG_PIN);
    delayMicroseconds(100);
  }
  sound = sum / 10;
}

// ============================================
// Read Vibration from MPU6050
// ============================================
void readVibration() {
  // Update MPU data
  mpu.update();
  
  // Get raw acceleration in 'g' units for all three axes
  float ax = mpu.getAccX();
  float ay = mpu.getAccY();
  float az = mpu.getAccZ();
  
  // Calculate vibration magnitude (removing 1g gravity from Z-axis)
  // This gives near-zero when sensor is still
  float vibration_magnitude_sq = ax*ax + ay*ay + (az-1.0)*(az-1.0);
  vibrationMagnitude = sqrt(vibration_magnitude_sq);
  
  // Apply a simple moving average filter to smooth the reading
  static float filteredVibration = 0;
  filteredVibration = filteredVibration * 0.8 + vibrationMagnitude * 0.2;
  vibration = filteredVibration;
}

// ============================================
// Detect Anomalies
// ============================================
void detectAnomaly() {
  anomalyDetected = false;
  
  if (temperature > 40 || temperature < 10) {
    anomalyDetected = true;
  }
  if (sound > 700) {
    anomalyDetected = true;
  }
  if (vibration > VIBRATION_THRESHOLD) {
    anomalyDetected = true;
  }
}

// ============================================
// Update LCD Display
// ============================================
void updateLCD() {
  // Clear screen each time
  lcd.clear();
  
  if (anomalyDetected) {
    // Show alert
    lcd.setCursor(0, 0);
    lcd.print("!!! ALERT !!!");
    lcd.setCursor(0, 1);
    
    if (temperature > 40) {
      lcd.print("TEMP HIGH!    ");
    } else if (temperature < 10) {
      lcd.print("TEMP LOW!     ");
    } else if (sound > 700) {
      lcd.print("SOUND HIGH!   ");
    } else if (vibration > VIBRATION_THRESHOLD) {
      lcd.print("VIBRATION!    ");
    }
  } else {
    // Normal display - Temperature
    lcd.setCursor(0, 0);
    lcd.print("T:");
    lcd.print(temperature, 1);
    lcd.print((char)223);
    lcd.print("C");
    
    // Sound on same line
    lcd.setCursor(9, 0);
    lcd.print("S:");
    if (sound < 1000) lcd.print(" ");
    if (sound < 100) lcd.print(" ");
    if (sound < 10) lcd.print(" ");
    lcd.print(sound);
    
    // Second row - Vibration
    lcd.setCursor(0, 1);
    lcd.print("V:");
    
    // Format vibration for display (3 decimal places or fewer)
    if (vibration < 0.01) {
      lcd.print("0.000");
    } else if (vibration < 0.1) {
      lcd.print(vibration, 4);
    } else {
      lcd.print(vibration, 3);
    }
    
    // Status on second row
    lcd.setCursor(10, 1);
    lcd.print("OK");
  }
}

// ============================================
// Send Data to Serial
// ============================================
void sendToSerial() {
  Serial.print(temperature, 1);
  Serial.print(",");
  Serial.print(vibration, 3);
  Serial.print(",");
  Serial.println(sound);
}
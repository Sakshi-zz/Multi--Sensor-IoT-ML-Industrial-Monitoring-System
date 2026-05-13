/*
 * Smart Industrial Safety & Hazard Monitoring System
 * WOKWI COMPATIBLE VERSION
 * 
 * Sensors: DHT22 (Temperature), MPU6050 (Vibration), KY-037 (Sound)
 * Output: CSV format over Serial + 16x2 LCD Display
 */

#include <DHT.h>
#include <MPU6050.h>  
#include <Wire.h>
#include <LiquidCrystal.h>

// ============================================
// Pin Definitions
// ============================================
#define DHTPIN 9
#define DHTTYPE DHT22
#define SOUND_ANALOG_PIN A0
#define SOUND_DIGITAL_PIN 8

// LCD Pin Definitions
#define LCD_RS 12
#define LCD_E 11
#define LCD_D4 5
#define LCD_D5 4
#define LCD_D6 3
#define LCD_D7 2

// ============================================
// Object Initialization
// ============================================
DHT dht(DHTPIN, DHTTYPE);
MPU6050 mpu;  
LiquidCrystal lcd(LCD_RS, LCD_E, LCD_D4, LCD_D5, LCD_D6, LCD_D7);

// ============================================
// Global Variables
// ============================================
unsigned long previousMillis = 0;
const long interval = 1000;

float temperature = 25.0;  // Default value
float vibrationRMS = 0.05;
int soundLevel = 200;
bool soundTriggered = false;
int riskLevel = 1;

int displayMode = 0;
unsigned long lastDisplayChange = 0;
const long displayInterval = 3000;

int peakSoundLevel = 0;
unsigned long lastPeakReset = 0;

int highTempCount = 0;
int highVibCount = 0;
int highSoundCount = 0;

unsigned long lastMPURead = 0;
float simulatedVibration = 0.05;

// ============================================
// Setup Function
// ============================================
void setup() {
  Serial.begin(9600);
  
  // Initialize I2C
  Wire.begin();
  
  // Initialize LCD
  lcd.begin(16, 2);
  lcd.setCursor(0, 0);
  lcd.print("Industrial");
  lcd.setCursor(0, 1);
  lcd.print("Safety Monitor");
  delay(2000);
  
  // Initialize DHT sensor
  dht.begin();
  
  // Initialize sound sensor pin
  pinMode(SOUND_DIGITAL_PIN, INPUT);
  
  // Initialize MPU6050
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Init MPU6050...");
  
  // Try to initialize MPU
  if (!mpu.testConnection()) {
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("MPU6050 Not Found");
    lcd.setCursor(0, 1);
    lcd.print("Using Sim Data");
    delay(2000);
  } else {
    mpu.initialize();
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("MPU6050 Ready");
    delay(1000);
  }
  
  // Ready message
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("System Ready");
  lcd.setCursor(0, 1);
  lcd.print("Risk: LOW");
  delay(1500);
  
  // CSV Header
  Serial.println(F("timestamp_ms,temp_c,vibration_g,sound_intensity,sound_triggered,risk_level"));
  
  lcd.clear();
}

// ============================================
// Main Loop
// ============================================
void loop() {
  unsigned long currentMillis = millis();
  
  // Read sensors at interval
  if (currentMillis - previousMillis >= interval) {
    previousMillis = currentMillis;
    
    readAllSensors();
    calculateRiskLevel();
    sendSerialData();
    updateLCD();
    checkEmergencyAlerts();
  }
  
  // Change display mode
  if (currentMillis - lastDisplayChange >= displayInterval) {
    lastDisplayChange = currentMillis;
    displayMode = (displayMode + 1) % 5;
    lcd.clear();
  }
  
  // Reset peak sound
  if (currentMillis - lastPeakReset >= 5000) {
    peakSoundLevel = 0;
    lastPeakReset = currentMillis;
  }
}

// ============================================
// Read All Sensors 
// ============================================
void readAllSensors() {
  
  // ----- READ TEMPERATURE from DHT22 -----
  float tempReading = dht.readTemperature();
  if (!isnan(tempReading)) {
    temperature = tempReading;
  } else {
    // Keep previous value if read fails
    static int failCount = 0;
    failCount++;
    if (failCount > 3) {
      temperature = 25.0;
    }
  }
  
  // ----- READ VIBRATION from MPU6050 -----
  readVibrationWokwi();
  
  // ----- READ SOUND from KY-037 -----
  int rawSound = analogRead(SOUND_ANALOG_PIN);
  soundTriggered = digitalRead(SOUND_DIGITAL_PIN);
  
  // Track peak sound
  if (rawSound > peakSoundLevel) {
    peakSoundLevel = rawSound;
  }
  
  // Apply smoothing filter
  static int filteredSound = 0;
  filteredSound = filteredSound * 0.7 + rawSound * 0.3;
  soundLevel = filteredSound;
}

// ============================================
// Vibration Reading 
// ============================================
void readVibrationWokwi() {
  // Try to read real MPU data
  int16_t ax, ay, az;
  mpu.getAcceleration(&ax, &ay, &az);
  
  // Convert to g (scale: 16384 LSB/g for ±2g range)
  float accX = ax / 16384.0;
  float accY = ay / 16384.0;
  float accZ = az / 16384.0;
  
  // Check if values are valid (not all zeros)
  if (accX != 0 || accY != 0 || accZ != 0) {
    // Calculate magnitude and remove gravity
    float magnitude = sqrt(accX * accX + accY * accY + accZ * accZ);
    vibrationRMS = abs(magnitude - 1.0);
    
    // Apply filter
    static float filteredVibration = 0.0;
    filteredVibration = filteredVibration * 0.7 + vibrationRMS * 0.3;
    vibrationRMS = filteredVibration;
  } else {

    // Creates realistic-looking data that varies over time
    unsigned long now = millis();
    if (now - lastMPURead > 50) {
      lastMPURead = now;
      
      // Sinusoidal pattern with random noise
      float pattern = sin(now / 1000.0) * 0.1;
      float noise = (random(0, 100) / 1000.0) * 0.05;
      simulatedVibration = simulatedVibration * 0.8 + (abs(pattern) + noise) * 0.2;
      
      // Occasional spikes to simulate impact
      if (random(0, 100) > 97) {
        simulatedVibration = random(200, 600) / 1000.0;
      }
      
      vibrationRMS = simulatedVibration;
    }
  }
  
  // Cap at reasonable values
  vibrationRMS = constrain(vibrationRMS, 0.01, 1.5);
}

// ============================================
// Calculate Risk Level
// ============================================
void calculateRiskLevel() {
  int riskScore = 0;
  
  // Temperature contribution
  if (temperature > 50) {
    riskScore += 3;
    highTempCount++;
  } else if (temperature > 40) {
    riskScore += 2;
    highTempCount++;
  } else if (temperature > 35) {
    riskScore += 1;
  } else {
    highTempCount = max(0, highTempCount - 1);
  }
  
  // Vibration contribution
  if (vibrationRMS > 0.5) {
    riskScore += 3;
    highVibCount++;
  } else if (vibrationRMS > 0.3) {
    riskScore += 2;
    highVibCount++;
  } else if (vibrationRMS > 0.15) {
    riskScore += 1;
  } else {
    highVibCount = max(0, highVibCount - 1);
  }
  
  // Sound contribution
  if (soundLevel > 800 || soundTriggered) {
    riskScore += 3;
    highSoundCount++;
  } else if (soundLevel > 600) {
    riskScore += 2;
    highSoundCount++;
  } else if (soundLevel > 400) {
    riskScore += 1;
  } else {
    highSoundCount = max(0, highSoundCount - 1);
  }
  
  // Determine overall risk
  if (riskScore >= 7) {
    riskLevel = 3;
  } else if (riskScore >= 4) {
    riskLevel = 2;
  } else {
    riskLevel = 1;
  }
}

// ============================================
// Send Serial Data
// ============================================
void sendSerialData() {
  Serial.print(millis());
  Serial.print(",");
  Serial.print(temperature, 1);
  Serial.print(",");
  Serial.print(vibrationRMS, 3);
  Serial.print(",");
  Serial.print(soundLevel);
  Serial.print(",");
  Serial.print(soundTriggered ? 1 : 0);
  Serial.print(",");
  Serial.println(riskLevel);
}

// ============================================
// Emergency Alerts
// ============================================
void checkEmergencyAlerts() {
  if (highTempCount >= 3 || highVibCount >= 3 || highSoundCount >= 3) {
    static unsigned long lastAlert = 0;
    if (millis() - lastAlert > 5000) {
      lastAlert = millis();
      
      Serial.print("⚠️ EMERGENCY ALERT: ");
      if (highTempCount >= 3) Serial.print("HIGH TEMPERATURE! ");
      if (highVibCount >= 3) Serial.print("EXCESSIVE VIBRATION! ");
      if (highSoundCount >= 3) Serial.print("DANGEROUS SOUND LEVEL! ");
      Serial.println();
      
      for (int i = 0; i < 3; i++) {
        lcd.noDisplay();
        delay(150);
        lcd.display();
        delay(150);
      }
    }
  }
}

// ============================================
// Update LCD Display
// ============================================
void updateLCD() {
  
  switch(displayMode) {
    
    case 0:  // All parameters
      lcd.setCursor(0, 0);
      lcd.print("T:");
      lcd.print(temperature, 1);
      lcd.print("C V:");
      lcd.print(vibrationRMS, 2);
      
      lcd.setCursor(0, 1);
      lcd.print("S:");
      lcd.print(soundLevel);
      lcd.print(" ");
      lcd.print(soundTriggered ? "!" : " ");
      lcd.print(" R:");
      printRiskLevel();
      break;
    
    case 1:  // Temperature only
      lcd.setCursor(0, 0);
      lcd.print("TEMPERATURE     ");
      lcd.setCursor(0, 1);
      lcd.print(temperature, 1);
      lcd.print(" C");
      
      lcd.setCursor(8, 1);
      if (temperature > 45) {
        lcd.print("CRIT!");
      } else if (temperature > 35) {
        lcd.print("HIGH ");
      } else if (temperature < 10) {
        lcd.print("LOW  ");
      } else {
        lcd.print("OK   ");
      }
      break;
    
    case 2:  // Vibration only
      lcd.setCursor(0, 0);
      lcd.print("VIBRATION       ");
      lcd.setCursor(0, 1);
      lcd.print(vibrationRMS, 3);
      lcd.print(" G");
      
      int vibBars;
      if (vibrationRMS > 0.5) vibBars = 16;
      else if (vibrationRMS > 0.4) vibBars = 12;
      else if (vibrationRMS > 0.3) vibBars = 8;
      else if (vibrationRMS > 0.15) vibBars = 4;
      else vibBars = 1;
      
      lcd.setCursor(10, 1);
      for (int i = 0; i < vibBars; i++) {
        lcd.print("|");
      }
      break;
    
    case 3:  // Sound only
      lcd.setCursor(0, 0);
      lcd.print("SOUND LEVEL     ");
      lcd.setCursor(0, 1);
      
      int soundBars = map(constrain(soundLevel, 0, 1023), 0, 1023, 0, 16);
      for (int i = 0; i < 16; i++) {
        lcd.setCursor(i, 1);
        if (i < soundBars) {
          lcd.print((char)255);
        } else {
          lcd.print(" ");
        }
      }
      
      lcd.setCursor(0, 1);
      lcd.print(soundLevel);
      lcd.print(" ");
      if (soundTriggered) {
        lcd.print("TRIG");
      }
      break;
    
    case 4:  // Risk level
      lcd.setCursor(0, 0);
      lcd.print("RISK LEVEL      ");
      lcd.setCursor(0, 1);
      
      switch(riskLevel) {
        case 1:
          lcd.print("LOW - SAFE");
          break;
        case 2:
          lcd.print("MEDIUM - CAUTION");
          break;
        case 3:
          lcd.print("HIGH - DANGER");
          break;
      }
      
      lcd.setCursor(0, 1);
      if (temperature > 45) {
        lcd.print("HOT");
      } else if (vibrationRMS > 0.4) {
        lcd.print("VIB");
      } else if (soundLevel > 700) {
        lcd.print("LOUD");
      }
      break;
  }
}

// ============================================
// Helper Functions
// ============================================
void printRiskLevel() {
  switch(riskLevel) {
    case 1:
      lcd.print("LOW");
      break;
    case 2:
      lcd.print("MED");
      break;
    case 3:
      lcd.print("HIGH");
      break;
  }
}
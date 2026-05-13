#include "wokwi-api.h"
#include <stdio.h>
#include <stdlib.h>

typedef struct {
  pin_t pin_d0;
  pin_t pin_a0;
  uint32_t threshold_attr;
  timer_t timer;
  float time_counter;
} chip_state_t;

void chip_timer_callback(void *user_data) {
  chip_state_t *chip = (chip_state_t*)user_data;
  
  // Read threshold from slider
  float threshold = attr_read_float(chip->threshold_attr);
  
  // Generate random sound level that varies over time
  chip->time_counter += 0.05;
  
  // Create varying sound pattern
  int pattern = (int)(chip->time_counter * 10) % 200;
  float sound_level;
  
  if (pattern < 10) {
    // Sudden loud sound (like a clap)
    sound_level = 70 + (rand() % 30);  // 70-100%
  } else if (pattern < 30) {
    // Medium sound
    sound_level = 40 + (rand() % 40);  // 40-80%
  } else {
    // Background noise
    sound_level = 10 + (rand() % 25);  // 10-35%
  }
  
  // Update analog output (0-1023)
  uint32_t analog_value = (uint32_t)((sound_level / 100.0) * 1023);
  pin_dac_write(chip->pin_a0, analog_value);
  
  // Update digital output (HIGH when sound exceeds threshold)
  uint32_t digital_value = (sound_level >= threshold) ? 1 : 0;
  pin_write(chip->pin_d0, digital_value);
  
  // Print to console occasionally
  static int counter = 0;
  counter++;
  if (counter >= 20) {  // Every ~1 second
    counter = 0;
    if (digital_value) {
      printf("SOUND DETECTED! Level: %.0f%% | Threshold: %.0f%% | Analog: %d\n", 
             sound_level, threshold, analog_value);
    } else {
      printf("Quiet: %.0f%% | Threshold: %.0f%%\n", 
             sound_level, threshold);
    }
  }
}

void chip_init() {
  setvbuf(stdout, NULL, _IOLBF, 1024);
  
  printf("\n=================================\n");
  printf("KY-037 Sound Sensor\n");
  printf("=================================\n");
  printf("Sensor simulating sound detection!\n");
  printf("=================================\n\n");
  
  chip_state_t *chip = malloc(sizeof(chip_state_t));
  
  // Initialize pins
  chip->pin_d0 = pin_init("D0", OUTPUT);
  chip->pin_a0 = pin_init("A0", ANALOG);
  
  // Initialize threshold attribute (slider)
  chip->threshold_attr = attr_init("threshold", 50);
  
  chip->time_counter = 0;
  
  // Set initial pin states
  pin_write(chip->pin_d0, LOW);
  pin_dac_write(chip->pin_a0, 0);
  
  // Start timer
  const timer_config_t timer_config = {
    .callback = chip_timer_callback,
    .user_data = chip,
  };
  
  chip->timer = timer_init(&timer_config);
  timer_start(chip->timer, 50000, true);  // 50ms interval
  
  printf("Sensor ready!\n");
  printf("Connect D0 -> Digital Pin, A0 -> Analog Pin\n\n");
}
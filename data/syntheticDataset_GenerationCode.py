import numpy as np
import pandas as pd

np.random.seed(42)
n_samples = 20000
time = np.arange(n_samples)

# BASE SENSOR PARAMETERS
base_temp = 30
base_sound = 45
vibration_amplitude = 1.0
# Noise levels
temp_noise_std = 0.5
vibration_noise_std = 0.2
sound_noise_std = 0.8

# BASE SIGNALS (STABLE BEHAVIOR)

# Temperature signal(slow drift + noise)
temperature = base_temp + 0.0015 * time + np.random.normal(0, temp_noise_std, n_samples)

# Vibration Signal(periodic machine vibration + noise)
frequency = 0.05
vibration = vibration_amplitude * np.sin(2 * np.pi * frequency * time)\
    + np.random.normal(0, vibration_noise_std, n_samples)

# Sound signal(steady background noise + small oscillation)
sound = base_sound + 1.5 *(np.sin(2 * np.pi * 0.02 * time)) + np.random.normal(0, sound_noise_std, n_samples)

# OPERATING CONDITION VARIATION
load = np.ones(n_samples)
# medium load period
load[6000:10000] = 1.2
# heavy load period
load[10000:13000] = 1.4

temperature += 0.7 * (load - 1)
vibration += 0.25 * (load - 1)
sound += 1.5 * (load - 1)

# ANOMALY INJECTION
anomaly = np.zeros(n_samples)

# Random Spike anomaly(micro faults)
spike_indices = np.random.choice(range(4000, 10000), 100, replace= False)
for idx in spike_indices:
    vibration[idx] += np.random.uniform(0.8, 1.5)
    sound[idx] += np.random.uniform(3, 6)
    temperature[idx] += np.random.uniform(1, 2)
    anomaly[idx] = 1

# Sensor drift(gradual calibration shift) : the sensor itself slowly becomes inaccurate
temp_sensor_drift = 0.0005 * time
vibration_sensor_drift = 0.0001 * time
sound_sensor_drift = 0.0003 * time

temperature += temp_sensor_drift
vibration += vibration_sensor_drift
sound += sound_sensor_drift

# Random Baseline Drift(very small random walk)
random_drift = np.cumsum(np.random.normal(0, 0.002, n_samples))
temperature += random_drift * 5
vibration += random_drift
sound += random_drift * 3

# Early Degradation Phase
for t in range(12000, 16000):
    temperature[t] += 0.002 + np.random.normal(0, 0.3)
    vibration[t] += 0.001 + np.random.normal(0, 0.05)
    sound[t] += 0.004 + np.random.normal(0, 0.5)

# Failure Phase (Strong Anomaly)
for t in range(16000, n_samples):
    temperature[t] += 0.01 + np.random.normal(0, 0.5)
    vibration[t] += 0.004 + np.random.normal(0, 0.1)
    sound[t] += 0.015 + np.random.normal(0, 0.8)
    anomaly[t] = 1
# Dataset Assembly
data = pd.DataFrame({
    "time": time,
    "temperature": temperature,
    "vibration": vibration,
    "sound": sound,
    "anomaly": anomaly
})

# Save dataset
data.to_csv("Synthetic_industrial_sensor_data_V4.csv", index=False)

print("Dataset generated successfully!")
print(data.head())
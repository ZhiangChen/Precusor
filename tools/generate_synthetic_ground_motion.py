import os
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

# Create a directory called "data" if it doesn't exist
os.makedirs("data", exist_ok=True)

# Parameters for the synthetic ground motion
duration = 3  # Duration of the signal in seconds
sampling_rate = 100  # Sampling rate in Hz (100 samples per second)
time = np.arange(0, duration, 1/sampling_rate)  # Time array

# Generate random frequencies and amplitudes
num_frequencies = np.random.randint(3, 6)  # Random number of frequency components (between 3 and 5)
frequencies = np.random.uniform(0.5, 5.0, num_frequencies)  # Frequencies between 0.5 Hz and 5 Hz
amplitudes = np.random.uniform(0.01, 0.05, num_frequencies)  # Amplitudes between 0.01 and 0.05 meters

# Generate random phase shifts
phases = np.random.uniform(0, 2 * np.pi, num_frequencies)

# Generate a synthetic displacement signal with random frequencies, amplitudes, and phases
displacement = np.zeros_like(time)
for freq, amp, phase in zip(frequencies, amplitudes, phases):
    displacement += amp * np.sin(2 * np.pi * freq * time + phase)

# Add a decaying envelope to simulate how seismic waves taper off over time
decay_rate = np.random.uniform(0.01, 0.05)  # Random decay rate between 0.01 and 0.05
envelope = np.exp(-decay_rate * time)
displacement *= envelope

# Add random noise to simulate real-world variability
noise_amplitude = np.random.uniform(0.002, 0.01)  # Random noise amplitude between 0.002 and 0.01
displacement += noise_amplitude * np.random.randn(len(time))

# Save the synthetic ground motion to a CSV file in the "data" folder
df = pd.DataFrame({
    'Time (s)': time,
    'Displacement (m)': displacement
})

# Save to CSV file in the data folder
csv_filename = "../data/synthetic_ground_motion.csv"
df.to_csv(csv_filename, index=False)
print(f"Saved synthetic ground motion data to {csv_filename}")

# Plot the synthetic ground motion (displacement)
plt.figure(figsize=(10, 6))
plt.plot(time, displacement, label="Synthetic Displacement")
plt.xlabel("Time (s)")
plt.ylabel("Displacement (m)")
plt.title("Synthetic Ground Motion (Displacement Data)")
plt.legend()
plt.grid(True)
plt.tight_layout()

# Save the plot as a PNG file in the "data" folder
plot_filename = "../data/synthetic_ground_motion.png"
plt.savefig(plot_filename)
print(f"Saved plot to {plot_filename}")

# Show the plot
plt.show()

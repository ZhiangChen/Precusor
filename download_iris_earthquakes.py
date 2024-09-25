from obspy.clients.fdsn import Client
from obspy import UTCDateTime
from obspy.geodetics import gps2dist_azimuth
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Initialize a client to download data from IRIS
client = Client("IRIS")

# Specify the earthquake event time (Example: 2010 Chile earthquake)
event_time = UTCDateTime("2010-02-27T06:34:14")

# Fetch the earthquake event information (including hypocenter)
cat = client.get_events(starttime=event_time - 1, endtime=event_time + 1, minmagnitude=8.0)
event = cat[0]
origin = event.origins[0]

# Get earthquake hypocenter (latitude, longitude, depth)
eq_lat = origin.latitude
eq_lon = origin.longitude
eq_depth = origin.depth / 1000  # Depth in km

# Define the station details (ANMO as an example)
network = "IU"
station = "ANMO"
location = "00"
channels = ["BHZ", "BH1", "BH2"]
inv = client.get_stations(network=network, station=station, level="station")
station_lat = inv[0][0].latitude
station_lon = inv[0][0].longitude

# Calculate the distance between the earthquake and the station (in meters)
distance_m, az, baz = gps2dist_azimuth(eq_lat, eq_lon, station_lat, station_lon)
distance_km = distance_m / 1000  # Convert to kilometers

# Assume an average P-wave velocity of 6 km/s
p_wave_velocity = 6.0  # km/s

# Calculate the P-wave travel time (distance / velocity)
p_wave_travel_time = distance_km / p_wave_velocity
p_wave_arrival_time = event_time + p_wave_travel_time

# Print the P-wave travel time and arrival time
print(f"P-wave travel time: {p_wave_travel_time:.2f} seconds")
print(f"P-wave arrival time: {p_wave_arrival_time}")

# Define the pre-filter for response removal (this should match the frequency range of interest)
# The values are usually chosen based on the frequency content of the signal.
pre_filt = (0.01, 0.02, 30.0, 35.0)  # (f1, f2, f3, f4) - lowpass and highpass filter corner frequencies

# Download waveform data for all three channels
start_time = event_time
end_time = p_wave_arrival_time + 60  # 1 minute after P-wave arrival
st = client.get_waveforms(network, station, location, ",".join(channels), start_time, end_time)

# Download the instrument response information
inv = client.get_stations(network=network, station=station, location=location, 
                          channel="BH*", starttime=start_time, endtime=end_time, level="response")

# Remove the instrument response to convert the raw data to acceleration (m/s²)
st.remove_response(inventory=inv, output="ACC", pre_filt=pre_filt)  # Convert to acceleration

# Convert acceleration to displacement by performing double integration
st_disp = st.copy()
st_disp.integrate()  # First integration to get velocity
st_disp.integrate()  # Second integration to get displacement

# Resample the data to 100 Hz (if the original sampling rate is different)
target_sampling_rate = 100.0  # Desired frequency in Hz
for tr in st_disp:
    # Resample to the target frequency (100 Hz)
    tr.resample(sampling_rate=target_sampling_rate)

# Truncate the waveform to 1 minute after the P-wave arrival
for tr in st_disp:
    tr.trim(starttime=p_wave_arrival_time, endtime=p_wave_arrival_time + 60)

# Initialize a dictionary to store displacement data for all channels
displacement_data = {}

# Create CSV for each channel
for tr in st_disp:
    # Get time and displacement data
    time = tr.times(reftime=p_wave_arrival_time)  # Reference time to P-wave arrival
    displacement = tr.data
    
    # Store the data in the dictionary
    displacement_data[tr.stats.channel] = displacement
    
    # Combine time and displacement into a dataframe
    df = pd.DataFrame({
        'Time (s)': time,
        f'Displacement ({tr.stats.channel}) (m)': displacement
    })
    
    # Save to CSV file
    csv_filename = f"truncated_displacement_{tr.stats.channel}.csv"
    # add to a folder called data
    csv_filename = f"data/{csv_filename}"
    df.to_csv(csv_filename, index=False)
    print(f"Saved truncated displacement data to {csv_filename}")

# Plot using Matplotlib for more customization
plt.figure(figsize=(10, 8))

for i, tr in enumerate(st_disp):
    time = tr.times("matplotlib", reftime=p_wave_arrival_time)  # Get time values relative to P-wave
    plt.subplot(3, 1, i + 1)
    plt.plot(time, tr.data, label=f"Displacement {tr.stats.channel} (m)")
    plt.xlabel("Time (s)")
    plt.ylabel("Displacement (m)")
    plt.title(f"{tr.stats.channel} - Displacement 1 minute after P-wave arrival")
    plt.legend()

plt.tight_layout()
# Save the plot as a PNG file
plt.savefig("data/displacement_plot.png")

plt.show()

import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import serial.tools.list_ports
import pandas as pd
import numpy as np
import serial
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import random
import pandas as pd
from obspy.clients.fdsn import Client
from obspy import UTCDateTime
from obspy.geodetics import gps2dist_azimuth

# Initialize global variables
displacement_data = np.array([])  # Array to store displacement data
arduino = None
fig = None
canvas = None
connected = False  # Track connection status
sample_rate = 100  # Default sample rate

pulsePerRev = 200 # Number of steps per revolution
maxRPM = 1200 # Increase maximum speed in RPM
lead = 0.02 # Distance traveled per revolution in meters
maxAcceleration = 1.1 # Maximum acceleration in g
totalLength = 0.6 # Total length of the shakebot in meters


# Function to list available COM ports
def list_ports():
    ports = serial.tools.list_ports.comports()
    return [port.device for port in ports]

# Function to toggle connection to Arduino (connect or disconnect)
def connect_arduino():
    global arduino, connected
    com_port = com_var.get()  # Get the selected COM port
    baud_rate = baud_var.get()  # Get the selected baud rate

    if not connected:  # If not connected, try to connect
        try:
            # Step 1: Connect to Arduino using the selected baud rate
            arduino = serial.Serial(com_port, baudrate=int(baud_rate), timeout=1)
            messagebox.showinfo("Connection", f"Connected to {com_port} at {baud_rate} baud rate.")

            # Step 2: Send the new baud rate to the Arduino
            arduino.write(f"BR:{baud_rate}\n".encode())  # Send "BR:<new_baud_rate>" command

            # Step 3: Reconnect with the new baud rate
            time.sleep(0.1)  # Short delay to ensure the Arduino receives the baud rate change
            arduino.close()  # Close the current connection
            arduino = serial.Serial(com_port, baudrate=int(baud_rate), timeout=1)  # Reopen with the new baud rate

            # Step 4: Send the shakebot parameters to Arduino
            send_parameters()

            # Step 5: Update the status and button
            connected = True
            update_status_light("green")  # Change status light to green
            connect_button.config(text="Disconnect")  # Update button text to "Disconnect"

            # Start reading serial data
            read_serial_data()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to connect: {e}")
    else:  # If already connected, disconnect
        if arduino:
            arduino.close()  # Close the connection
        messagebox.showinfo("Disconnection", "Arduino disconnected.")
        connected = False
        update_status_light("red")  # Change status light back to red
        connect_button.config(text="Connect to Arduino")  # Update button text to "Connect to Arduino"

def send_parameters():
    global arduino
    try:
        # Create a parameter string in the format:
        # SET_PARAMS pulsePerRev=<value> maxRPM=<value> lead=<value> maxAcceleration=<value> totalLength=<value>
        param_str = f"SET_PARAMS pulsePerRev={pulsePerRev} maxRPM={maxRPM} lead={lead} maxAcceleration={maxAcceleration} totalLength={totalLength}\n"
        arduino.write(param_str.encode())
    except Exception as e:
        messagebox.showerror("Error", f"Failed to send parameters: {e}")

# Function to read serial data from Arduino and display it in the text widget
def read_serial_data():
    if arduino and arduino.is_open:
        try:
            data = arduino.readline().decode('utf-8').strip()  # Read a line of serial data
            if data:
                serial_text.insert(tk.END, data + "\n")  # Insert the data into the Text widget
                serial_text.see(tk.END)  # Scroll to the end of the Text widget
        except Exception as e:
            print(f"Error reading serial data: {e}")

    # Call this function again after 100 ms to continuously check for new serial data
    if connected:
        serial_text.after(100, read_serial_data)

# Function to update the status light
def update_status_light(color):
    status_light.delete("all")  # Clear existing content
    status_light.create_oval(10, 10, 30, 30, fill=color)  # Draw circle with the specified color

# Function to generate cosine displacement data
def generate_cosine_displacement():
    global displacement_data
    try:
        pgv = float(velocity_entry.get())
        pga = float(acceleration_entry.get())
        cycle_number = int(cycles_entry.get())

        if pga == 0:
            messagebox.showerror("Error", "Peak Ground Acceleration cannot be zero.")
            return

        PGV_2_PGA = pgv / pga
        F = 1./(2*np.pi*PGV_2_PGA)
        A = 9.807*pga/(4*np.pi**2*F**2)
        T = 1./F
        global sample_rate
        # Generate time vector and scale it to the period
        time_steps = np.linspace(0, T * cycle_number, int(sample_rate * cycle_number * T))
        # Generate cosine displacement using the provided parameters: D = A - A*cos(2*pi*t/T)
        displacement_data = A - A * np.cos(2 * np.pi * time_steps / T)
        # combine the time steps and displacement data
        displacement_data = np.column_stack((time_steps, displacement_data))
        plot_data(displacement_data)
    except ValueError:
        messagebox.showerror("Error", "Please enter valid numerical values for the parameters.")

# Function to load CSV ground motion displacement file
def load_csv_file():
    global displacement_data
    file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    if file_path:
        try:
            # Load the CSV file using pandas
            df = pd.read_csv(file_path)

            # Clean up the headers in case there are extra spaces or invisible characters
            df.columns = df.columns.str.strip()

            # Try to match the columns more flexibly (ignoring spaces and casing issues)
            possible_time_columns = [col for col in df.columns if "time" in col.lower()]
            possible_displacement_columns = [col for col in df.columns if "displacement" in col.lower()]

            # Check if we found valid columns
            if not possible_time_columns or not possible_displacement_columns:
                messagebox.showerror("Error", "Required columns not found.")
                return

            # Use the first matching columns
            time_column = possible_time_columns[0]
            displacement_column = possible_displacement_columns[0]

            # Extract time and displacement values
            time = df[time_column].values
            displacement = df[displacement_column].values

            # Combine time and displacement into a 2D array
            displacement_data = np.column_stack((time, displacement))

            # Plot the loaded data
            plot_data(displacement_data)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load CSV: {e}")


def convert_displacement_to_steps(displacement):
    """
    Convert displacement in meters to motor steps.

    Args:
        displacement (float or np.ndarray): Displacement(s) in meters.

    Returns:
        int or np.ndarray: Corresponding motor step count(s).
    """
    return (displacement / lead * pulsePerRev).astype(int) if isinstance(displacement, np.ndarray) else int(displacement / lead * pulsePerRev)



# Function to send data to Arduino with confirmation before starting the experiment
def send_data():
    global displacement_data
    # Check if there is data to send
    if displacement_data.size == 0:
        messagebox.showwarning("No Data", "No data to send. Please generate or load ground motion data.")
        return

    try:
        # Extract all displacement values from the second column (index 1)
        displacements = displacement_data[:, 1]

        # if displacement exceeds the total length of the shakebot [-0.6, 0.6], show an error message
        if np.any(np.abs(displacements) > totalLength):
            messagebox.showerror("Error", "Displacement exceeds the maximum limit. Please reduce the displacement.")

        # Convert all displacements to step counts
        steps_all = convert_displacement_to_steps(displacements)

        # Ensure steps_all is a NumPy array for vectorized operations
        steps_all = np.array(steps_all)

        # Check if any step count exceeds Arduino's int limit
        if np.any(np.abs(steps_all) > 2147483647):
            messagebox.showerror("Error", "Displacement exceeds the maximum limit. Please reduce the displacement.")
            return

        if arduino and arduino.is_open:
            # Send the step counts to Arduino
            for steps in steps_all:
                arduino.write(f"{steps}\n".encode())
                # Wait for acknowledgment (optional, based on Arduino implementation)
                # ack = arduino.readline().decode().strip()
                # if ack != "STEP_RECEIVED":
                #     messagebox.showwarning("Warning", f"Unexpected acknowledgment: {ack}")
                #     break
                time.sleep(0.001)  # 1 ms delay for high baud rates

            # After sending all step counts, prompt for confirmation to start the experiment
            response = messagebox.askyesno(
                "Confirmation",
                "Data sent to Arduino successfully.\nDo you want to start the experiment?"
            )

            if response:
                # User confirmed to start the experiment
                arduino.write("START\n".encode())
            else:
                # User canceled the experiment start
                arduino.write("CANCEL\n".encode())
        else:
            messagebox.showerror("Error", "Arduino is not connected.")

    except Exception as e:
        messagebox.showerror("Error", f"Failed to send data: {e}")



# Function to plot the displacement data or display an empty canvas
def plot_data(data=None):
    global fig, canvas
    # Clear the figure if it exists
    if fig:
        fig.clf()

    # Create a new figure and plot the data or an empty plot
    fig = plt.Figure(figsize=(5, 4), dpi=100)
    ax = fig.add_subplot(111)
    
    if data is None:
        # Display empty plot with title only
        ax.set_title('Ground Motion')
        ax.set_xlabel('Time Steps')
        ax.plot([], [])  # Empty plot
        # set axis limits 0 to 60 seconds
        ax.set_xlim(0, 60)
    else:
        # Plot the provided data
        time_steps = data[:, 0]
        displacement = data[:, 1]
        ax.plot(time_steps, displacement)
        ax.set_title('Ground Motion Displacement')
        ax.set_xlabel('Time Steps (s)')
        ax.set_ylabel('Displacement (m)')


    # add grid with minor ticks and dashed lines
    ax.grid(which='both', linestyle='--')

    # If the canvas already exists, remove it and update with a new plot
    if canvas:
        canvas.get_tk_widget().destroy()

    canvas = FigureCanvasTkAgg(fig, master=plot_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

def send_displacement():
    global arduino
    if arduino and arduino.is_open:
        displacement = displacement_slider.get()
        displacement = convert_displacement_to_steps(displacement / 1000.0)
        # First, write displacement to arduino and then send the command
        arduino.write(f"{displacement}\n".encode())
        time.sleep(0.1)
        arduino.write("SET_DISPLACEMENT\n".encode())
    else:
        messagebox.showerror("Error", "Arduino is not connected.")

def calibrate_displacement():
    global arduino
    if arduino and arduino.is_open:
        displacement = displacement_slider.get()
        displacement = convert_displacement_to_steps(displacement / 1000.0)
        arduino.write(f"{displacement}\n".encode())
        time.sleep(0.1)
        arduino.write("CALIBRATE_DISPLACEMENT\n".encode())
        messagebox.showinfo("Displacement Calibration", "Calibration started. Please wait for the process to complete.")
    else:
        messagebox.showerror("Error", "Arduino is not connected.")

def download_iris_data():
    def fetch_iris_data():
        global displacement_data
        try:
            # Get the duration from the user
            duration = float(duration_entry.get())
            if duration <= 0:
                raise ValueError("Duration must be a positive number.")
            
            # Initialize a client to download data from IRIS
            client = Client("IRIS")

            # Define a random time range for event search (past 5 years)
            end_time = UTCDateTime()  # Current time
            start_time = end_time - (365 * 5 * 24 * 60 * 60)  # 5 years ago

            # Fetch random events in the given time range (min magnitude 6.0 for example)
            cat = client.get_events(starttime=start_time, endtime=end_time, minmagnitude=6.0, limit=50)
            
            if not cat:
                messagebox.showerror("Error", "No events found in the specified time range.")
                return

            # Randomly select an event from the fetched catalog
            event = random.choice(cat)
            origin = event.origins[0]
            event_time = origin.time
            eq_lat = origin.latitude
            eq_lon = origin.longitude
            eq_depth = origin.depth / 1000  # Depth in km
            magnitude = event.magnitudes[0].mag

            print(f"Random Event Selected: Time: {event_time}, Lat: {eq_lat}, Lon: {eq_lon}, Depth: {eq_depth} km, Mag: {magnitude}")

            # Define the station details (ANMO as an example)
            network = "IU"
            station = "ANMO"
            location = "00"
            # Fetch only horizontal components BH1 and BH2
            channels = ["BH1", "BH2"]
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

            # Define the pre-filter for response removal (this should match the frequency range of interest)
            pre_filt = (0.01, 0.02, 30.0, 35.0)  # Lowpass and highpass filter corner frequencies

            # Download waveform data for horizontal components (BH1 and BH2)
            start_time = event_time
            end_time = p_wave_arrival_time + duration  # Dynamic duration based on user input
            st = client.get_waveforms(network, station, location, ",".join(channels), start_time, end_time)

            # Download the instrument response information
            inv = client.get_stations(network=network, station=station, location=location, 
                                      channel="BH*", starttime=start_time, endtime=end_time, level="response")

            # Remove the instrument response to convert the raw data to acceleration (m/s²)
            st.remove_response(inventory=inv, output="ACC", pre_filt=pre_filt)

            # Convert acceleration to displacement by performing double integration
            st_disp = st.copy()
            st_disp.integrate()  # First integration to get velocity
            st_disp.integrate()  # Second integration to get displacement

            # Resample the data to 100 Hz (if the original sampling rate is different)
            target_sampling_rate = 100.0  # Desired frequency in Hz
            for tr in st_disp:
                tr.resample(sampling_rate=target_sampling_rate)

            # Trim the waveform to the duration after the P-wave arrival
            for tr in st_disp:
                tr.trim(starttime=p_wave_arrival_time, endtime=p_wave_arrival_time + duration)

            # Prepare the horizontal displacement data for plotting (BH1 and BH2)
            displacement_data_ = []
            for tr in st_disp:
                time = tr.times(reftime=p_wave_arrival_time)
                displacement = tr.data
                displacement_data_.append([time, displacement])

            # Close the window
            new_window.destroy()

            # Combine the time and displacement data into a single array for plotting
            combined_displacement_data = np.column_stack(displacement_data_[0])  # Assume plotting BH1 channel
            plot_data(combined_displacement_data)
            displacement_data = combined_displacement_data

        except Exception as e:
            messagebox.showerror("Error", f"Failed to download and process data: {e}")

    # Create a new window for the user to input the duration
    new_window = tk.Toplevel(root)
    new_window.title("Download IRIS Data")
    new_window.geometry("300x150")

    # Label and entry for the duration input
    tk.Label(new_window, text="Enter Duration (seconds):").pack(pady=10)
    duration_entry = tk.Entry(new_window)
    duration_entry.pack(pady=5)

    # Button to start the data download process
    fetch_button = tk.Button(new_window, text="Download Data", command=fetch_iris_data)
    fetch_button.pack(pady=10)

def generate_random_data():
    def generate_and_return_data():
        try:
            # Get the duration input from the user
            duration = float(duration_entry.get())
            if duration <= 0:
                raise ValueError("Duration must be a positive number.")
            
            # duration must be less than 150 seconds
            if duration >= 150:
                raise ValueError("Duration must be less than 150 seconds.")
            
            # Parameters for the synthetic ground motion
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

            # Combine time and displacement into a 2D array
            global displacement_data
            displacement_data = np.column_stack((time, displacement))

            # Close the window
            new_window.destroy()

            # Plot the generated data
            plot_data(displacement_data)

        except ValueError:
            messagebox.showerror("Error", "Please enter a valid duration (positive number less than 150 seconds).")

    # Create a new window for duration input
    new_window = tk.Toplevel(root)
    new_window.title("Generate Random Data")
    new_window.geometry("300x150")

    # Label and entry for duration input
    tk.Label(new_window, text="Enter Duration (seconds):").pack(pady=10)
    duration_entry = tk.Entry(new_window)
    duration_entry.pack(pady=5)

    # Generate button in the new window
    generate_button = tk.Button(new_window, text="Generate Data", command=generate_and_return_data)
    generate_button.pack(pady=10)

# Main function to create the GUI
def main():
    global plot_frame, connect_button, status_light, serial_text, displacement_slider, com_combobox, com_var, root

    # Create the main application window
    root = tk.Tk()
    root.title("Seismove Shakebot v2.0")
    root.geometry("1350x700")  # Set the default window size (increased height for the text widget)

    # Configure grid layout weights to allow resizing
    for i in range(20):  # Increased row count for new text widget
        root.grid_rowconfigure(i, weight=1)
    root.grid_columnconfigure(0, weight=1)
    root.grid_columnconfigure(1, weight=1)

    # Left side for controls
    control_frame = tk.Frame(root)
    control_frame.grid(row=0, column=0, rowspan=14, sticky="nswe", padx=10, pady=5)

    # Right side for plotting and serial data
    plot_frame = tk.Frame(root)
    plot_frame.grid(row=2, column=1, rowspan=14, sticky="nswe", padx=10, pady=5)

    # Serial data display
    serial_text_frame = tk.Frame(root)
    serial_text_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=5)
    tk.Label(serial_text_frame, text="Serial Output").pack(anchor="w")
    serial_text = tk.Text(serial_text_frame, height=5, width=60)
    serial_text.pack(fill="both", expand=True)

    # Dropdown menu for COM port selection
    tk.Label(control_frame, text="COM Port:").grid(row=1, column=0, padx=10, pady=5, sticky="ew")
    global com_var
    com_var = tk.StringVar(control_frame)
    com_var.set(list_ports()[-1])  # Set default COM port
    com_dropdown = tk.OptionMenu(control_frame, com_var, *list_ports())
    com_dropdown.grid(row=1, column=1, padx=10, pady=5, sticky="ew")


    # Dropdown menu for baud rate selection
    tk.Label(control_frame, text="Baud Rate:").grid(row=2, column=0, padx=10, pady=5, sticky="ew")
    global baud_var
    baud_var = tk.StringVar(control_frame)
    baud_var.set("250000")  # Default baud rate
    baud_dropdown = tk.OptionMenu(control_frame, baud_var, "9600", "115200", "250000", "500000", "1000000")
    baud_dropdown.grid(row=2, column=1, padx=10, pady=5, sticky="ew")

    # Add the status light (initially red)
    status_light = tk.Canvas(control_frame, width=40, height=40)
    status_light.grid(row=3, column=0, padx=10, pady=5)
    update_status_light("red")  # Initialize the light as red

    # Button to connect to Arduino
    connect_button = tk.Button(control_frame, text="Connect to Arduino", command=connect_arduino)
    connect_button.grid(row=3, column=1, padx=10, pady=5, sticky="ew")

    # Divider for displacement control
    ttk.Separator(control_frame, orient="horizontal").grid(row=4, column=0, columnspan=2, sticky="ew", padx=10, pady=5)

    # Slider from 0 to 600 mm
    tk.Label(control_frame, text="Displacement (mm):").grid(row=5, column=0, padx=10, pady=5, sticky="ew")
    displacement_slider = tk.Scale(control_frame, from_=0, to=600, orient="horizontal", length=200)
    displacement_slider.grid(row=5, column=1, padx=10, pady=5, sticky="ew")

    # Button to send displacement to Arduino
    send_displacement_button = tk.Button(control_frame, text="Send Displacement", command=send_displacement)
    send_displacement_button.grid(row=6, column=0, columnspan=1, padx=10, pady=5, sticky="ew")
    
    # Button to calibrate the displacement
    calibrate_button = tk.Button(control_frame, text="Calibrate Displacement", command=calibrate_displacement)
    calibrate_button.grid(row=6, column=1, columnspan=1, padx=10, pady=5, sticky="ew")


    # Divider for Option 1
    ttk.Separator(control_frame, orient="horizontal").grid(row=8, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
    tk.Label(control_frame, text="Option 1").grid(row=9, column=0, columnspan=2, padx=10, pady=5)

    # Inputs for generating cosine displacement (Option 1)
    tk.Label(control_frame, text="Peak Ground Velocity (m/s):").grid(row=10, column=0, padx=10, pady=5, sticky="ew")
    global velocity_entry
    velocity_entry = tk.Entry(control_frame)
    velocity_entry.grid(row=10, column=1, padx=10, pady=5, sticky="ew")

    tk.Label(control_frame, text="Peak Ground Acceleration (m/s^2):").grid(row=11, column=0, padx=10, pady=5, sticky="ew")
    global acceleration_entry
    acceleration_entry = tk.Entry(control_frame)
    acceleration_entry.grid(row=11, column=1, padx=10, pady=5, sticky="ew")

    tk.Label(control_frame, text="Cycle Number:").grid(row=12, column=0, padx=10, pady=5, sticky="ew")
    global cycles_entry
    cycles_entry = tk.Entry(control_frame)
    cycles_entry.grid(row=12, column=1, padx=10, pady=5, sticky="ew")

    # Button to generate cosine displacement
    generate_button = tk.Button(control_frame, text="Generate Cosine Displacement", command=generate_cosine_displacement)
    generate_button.grid(row=13, column=0, columnspan=2, padx=10, pady=5, sticky="ew")

    # Divider for Option 2
    ttk.Separator(control_frame, orient="horizontal").grid(row=14, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
    tk.Label(control_frame, text="Option 2").grid(row=15, column=0, columnspan=2, padx=10, pady=5)

    # Button to download IRIS earthquake data 
    download_button = tk.Button(control_frame, text="Download IRIS Data", command=download_iris_data)
    download_button.grid(row=16, column=0, columnspan=1, padx=10, pady=5, sticky="ew")

    # Button to generate random earthquake data
    random_button = tk.Button(control_frame, text="Generate Random Data", command=generate_random_data)
    random_button.grid(row=16, column=1, columnspan=1, padx=10, pady=5, sticky="ew")

    # Button to load CSV ground motion file (Option 2)
    load_button = tk.Button(control_frame, text="Load CSV Ground Motion File", command=load_csv_file)
    load_button.grid(row=17, column=0, columnspan=2, padx=10, pady=5, sticky="ew")

    # Button to send data to Arduino
    ttk.Separator(control_frame, orient="horizontal").grid(row=18, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
    send_button = tk.Button(control_frame, text="Send Data to Arduino", command=send_data)
    send_button.grid(row=19, column=0, columnspan=2, padx=10, pady=5, sticky="ew")

    # Initialize an empty plot
    plot_data()

    # Start the Tkinter event loop
    root.mainloop()

# Entry point for the script
if __name__ == "__main__":
    main()
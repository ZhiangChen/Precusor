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

# Initialize global variables
displacement_data = np.array([])  # Array to store displacement data
arduino = None
fig = None
canvas = None
connected = False  # Track connection status
sample_rate = 100  # Default sample rate

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

            # Step 4: Update the status and button
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
            
            # Assuming the CSV has 'Time (s)' and 'Displacement (m)' columns
            time = df['Time (s)'].values
            displacement = df['Displacement (m)'].values

            # Combine time and displacement into a 2D array
            displacement_data = np.column_stack((time, displacement))

            # Plot the loaded data
            plot_data(displacement_data)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load CSV: {e}")


# Function to send data to Arduino
def send_data():
    global displacement_data
    # check if there is data to send, check the shape of the array
    if displacement_data.size == 0:
        messagebox.showwarning("No Data", "No data to send. Please generate or load ground motion data.")
        return

    if arduino and arduino.is_open:
        # Send the displacement data to Arduino
        for displacement in displacement_data[:, 1]:
            arduino.write(f"{displacement}\n".encode())
            time.sleep(1/float(baud_var.get()))  # Set a delay based on the baud rate to ensure proper transmission
        
        messagebox.showinfo("Success", "Data sent to Arduino. Start the experiment.")
        # After sending all data, send a "START" command
        arduino.write("START\n".encode())
    else:
        messagebox.showerror("Error", "Arduino is not connected.")

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
        ax.set_xlabel('Time Steps')

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
    print(f"Displacement set to {displacement} mm.")
    if arduino and arduino.is_open:
        displacement = displacement_slider.get()
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
        arduino.write(f"{displacement}\n".encode())
        time.sleep(0.1)
        arduino.write("CALIBRATE_DISPLACEMENT\n".encode())
        messagebox.showinfo("Displacement Calibration", "Calibration started. Please wait for the process to complete.")
    else:
        messagebox.showerror("Error", "Arduino is not connected.")

# Main function to create the GUI
def main():
    global plot_frame, connect_button, status_light, serial_text, displacement_slider

    # Create the main application window
    root = tk.Tk()
    root.title("Seismove Shakebot v2.0")
    root.geometry("1200x600")  # Set the default window size (increased height for the text widget)

    # Configure grid layout weights to allow resizing
    for i in range(19):  # Increased row count for new text widget
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
    tk.Label(control_frame, text="Displacement (mm):").grid(row=5, column=0, padx=10, pady=5, sticky="w")
    displacement_slider = tk.Scale(control_frame, from_=0, to=600, orient="horizontal", length=200)
    displacement_slider.grid(row=5, column=1, padx=10, pady=5, sticky="ew")

    # Button to send displacement to Arduino
    send_displacement_button = tk.Button(control_frame, text="Send Displacement", command=send_displacement)
    send_displacement_button.grid(row=6, column=1, columnspan=1, padx=10, pady=5, sticky="ew")
    
    # Button to calibrate the displacement
    calibrate_button = tk.Button(control_frame, text="Calibrate Displacement", command=calibrate_displacement)
    calibrate_button.grid(row=7, column=1, columnspan=1, padx=10, pady=5, sticky="ew")


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

    # Button to load CSV ground motion file (Option 2)
    load_button = tk.Button(control_frame, text="Load CSV Ground Motion File", command=load_csv_file)
    load_button.grid(row=16, column=0, columnspan=2, padx=10, pady=5, sticky="ew")

    # Button to send data to Arduino
    ttk.Separator(control_frame, orient="horizontal").grid(row=17, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
    send_button = tk.Button(control_frame, text="Send Data to Arduino", command=send_data)
    send_button.grid(row=18, column=0, columnspan=2, padx=10, pady=5, sticky="ew")

    # Initialize an empty plot
    plot_data()

    # Start the Tkinter event loop
    root.mainloop()

# Entry point for the script
if __name__ == "__main__":
    main()
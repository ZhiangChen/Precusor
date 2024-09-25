#include <AccelStepper.h>
#include <TimerOne.h>

#define STEP_PIN 2  // Pin for step signal
#define DIR_PIN 3   // Pin for direction signal
#define LEFT_LIMIT_PIN 4  // Pin for left limit switch
#define RIGHT_LIMIT_PIN 5  // Pin for right limit switch

AccelStepper stepper(AccelStepper::DRIVER, STEP_PIN, DIR_PIN);  // Use AccelStepper in driver mode

const int pulsePerRev = 200; // Number of steps per revolution
const float maxRPM = 1200;  // Increase maximum speed in RPM
const float lead = 0.02;  // Distance traveled per revolution in meters
const float maxAcceleration = 1.1; // Maximum acceleration in g

const int maxDisplacement = 400;  // Maximum number of displacement points to handle
volatile float displacementData[maxDisplacement];  // Array to store incoming displacement data
volatile int dataSize = 0;  // Number of data points received
volatile int currentIndex = 0;  // Current index in the displacement array
volatile bool executeMotion = false;  // Flag to start executing motion
volatile bool isCalibrating = false;  // Flag to indicate calibration (moving to left limit)

// start time and end time for the motion
unsigned long startTime = 0;
unsigned long endTime = 0;

unsigned long baudRate = 250000;  // Or even higher

void setup() {
  Serial.begin(baudRate);  // Initialize serial communication at default baud rate
  stepper.setMaxSpeed(pulsePerRev * maxRPM);  // Set max speed for the stepper motor (adjust as needed)
  stepper.setAcceleration(int(maxAcceleration * pulsePerRev * 9.8 / lead));  // Set acceleration (adjust as needed)

  pinMode(LEFT_LIMIT_PIN, INPUT_PULLUP);  // Initialize limit switch pin with pullup resistor
  pinMode(RIGHT_LIMIT_PIN, INPUT_PULLUP);  // Initialize right limit switch pin (not used here)

  Timer1.initialize(10000);  // 10 ms timer interrupt (100 Hz)
  Timer1.attachInterrupt(updateMotorPosition);  // Attach the interrupt handler
}

void loop() {
  stepper.run();
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');  // Read a command from the GUI

    // Check if the command is a baud rate change request (e.g., "BR:9600")
    if (command.startsWith("BR:")) {
      long newBaudRate = command.substring(3).toInt();  // Extract the baud rate value
      if (newBaudRate > 0) {
        changeBaudRate(newBaudRate);  // Change the baud rate
      }
    }
    else if (command == "START") {
      Serial.println("Start executing displacement data.");
      executeMotion = true;
    }
    else if (command == "SET_DISPLACEMENT") {
      startCalibration();  // Begin the calibration process
    }
    else {
      receiveDisplacementData(command);  // Process normal displacement data
    }
  }
}

// Function to start calibration (move to left limit)
void startCalibration() {
  // Move the motor slowly to the left until the left limit switch is triggered
  Serial.println("Starting calibration...");
  stepper.setMaxSpeed(100);  // Slow speed for calibration
  stepper.moveTo(-10000);  // Move left indefinitely (until the limit switch is hit)
  isCalibrating = true;  // Set the flag to indicate calibration mode
}

// Function to receive displacement data
void receiveDisplacementData(String dataString) {
  float displacement = dataString.toFloat();
  if (dataSize < maxDisplacement) {
    noInterrupts();
    displacementData[dataSize] = displacement;
    dataSize++;
    interrupts();
  } else {
    Serial.println("Displacement data buffer full.");
  }
}

// Interrupt Service Routine (ISR) to update the motor position at 100 Hz
void updateMotorPosition() {
  // Handle calibration (moving to the left limit switch)
  if (isCalibrating) {
    if (digitalRead(LEFT_LIMIT_PIN) == LOW) {  // If left limit switch is triggered
      stepper.stop();  // Stop the motor
      isCalibrating = false;  // Exit calibration mode
      Serial.println("Calibration complete. Moving to displacementData[0].");

      // Move to the position based on displacementData[0]
      int stepsToMove = convertDisplacementToSteps(displacementData[0]);
      stepper.setMaxSpeed(pulsePerRev * maxRPM);  // Restore max speed
      stepper.moveTo(stepsToMove);  // Move to the first displacement
    }
    return;
  }

  if (dataSize == 0 || !executeMotion) {
    startTime = millis();
    return;  // Do nothing if no data or not started
  }
  float displacement = displacementData[currentIndex];
  int steps = convertDisplacementToSteps(displacement);
  stepper.moveTo(steps);

  currentIndex++;
  if (currentIndex >= dataSize) {
    currentIndex = 0;
    executeMotion = false;  // Stop execution after finishing the current displacement data
    dataSize = 0;  // Reset data size to indicate that no data is left
    endTime = millis();
    Serial.print("Motion completed in ");
    Serial.print(endTime - startTime);
    Serial.println(" milliseconds.");
  }
}

// Function to convert displacement to motor steps
int convertDisplacementToSteps(float displacement) {
  return int(displacement / lead * pulsePerRev);
}

// Function to change the baud rate dynamically
void changeBaudRate(long newBaudRate) {
  Serial.println("Changing baud rate...");
  delay(100);  // Short delay to ensure the message is sent
  Serial.end();  // End the current serial connection

  baudRate = newBaudRate;  // Set the new baud rate
  Serial.begin(baudRate);  // Reinitialize the serial communication with the new baud rate
  Serial.println("Baud rate changed to: " + String(baudRate));
}
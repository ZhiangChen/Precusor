#include <AccelStepper.h>
#include <TimerOne.h>

#define STEP_PIN 2         // Pin for step signal
#define DIR_PIN 3          // Pin for direction signal
#define LEFT_LIMIT_PIN 4   // Pin for left limit switch
#define RIGHT_LIMIT_PIN 5  // Pin for right limit switch

AccelStepper stepper(AccelStepper::DRIVER, STEP_PIN, DIR_PIN);  // Use AccelStepper in driver mode

const int pulsePerRev = 200;        // Number of steps per revolution
const float maxRPM = 1200;          // Increase maximum speed in RPM
const float lead = 0.02;            // Distance traveled per revolution in meters
const float maxAcceleration = 1.1;  // Maximum acceleration in g
const float totalLength = 0.6;      // Total length of the shakebot in meters

const int maxDisplacement = 350;                   // Maximum number of displacement points to handle
volatile float displacementData[maxDisplacement];  // Array to store incoming displacement data
volatile int dataSize = 0;                         // Number of data points received
volatile int currentIndex = 0;                     // Current index in the displacement array
volatile bool executeMotion = false;               // Flag to start executing motion
// start time and end time for the motion
unsigned long startTime = 0;
unsigned long endTime = 0;

bool isSettingDisplacement = false;  // Flag to indicate setting displacement data
bool isCalibrating = false;          // Flag to indicate calibration (moving to left limit)

unsigned long baudRate = 250000;  // Or even higher

void setup() {
  Serial.begin(baudRate);                                                    // Initialize serial communication at default baud rate
  stepper.setMaxSpeed(pulsePerRev * maxRPM);                                 // Set max speed for the stepper motor (adjust as needed)
  stepper.setAcceleration(int(maxAcceleration * pulsePerRev * 9.8 / lead));  // Set acceleration (adjust as needed)

  pinMode(LEFT_LIMIT_PIN, INPUT_PULLUP);   // Initialize limit switch pin with pullup resistor
  pinMode(RIGHT_LIMIT_PIN, INPUT_PULLUP);  // Initialize right limit switch pin

  Timer1.initialize(10000);                     // 10 ms timer interrupt (100 Hz)
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
    } else if (command == "START") {
      // print the number of data points to be executed
      Serial.println("Number of data points to be executed: " + String(dataSize));
      // print all displacement data in mm and steps
      //for (int i = 0; i < dataSize; i++) {
      //  Serial.println("Displacement " + String(i) + ": " + String(displacementData[i]) + " mm (" + String(convertDisplacementToSteps(displacementData[i])) + " steps)");
      //}
      Serial.println("Start executing displacement data.");
      // If we receive the "START" command, set the flag to start executing the motion
      executeMotion = true;
    }
    
    else if (command == "SET_DISPLACEMENT") {
      setDisplacementData();  // Set displacement data
    }
    
    else if (command == "CALIBRATE_DISPLACEMENT") {
      startCalibration();  // Begin the calibration process
    }
    
    else {
      receiveDisplacementData(command);  // Process normal displacement data
    }
  }
}


void setDisplacementData() {
  // Move the motor slowly to the left until the left limit switch is triggered
  Serial.println("Starting moving displacement...");
  stepper.setMaxSpeed(pulsePerRev/2);  // Slow speed for calibration
  stepper.moveTo(-(totalLength / lead + 10)* pulsePerRev);  // Move left indefinitely (until the limit switch is hit)
  isSettingDisplacement = true;  // Set the flag to indicate set_displacement mode
}


void startCalibration() {
  // Move the motor slowly to the left until the left limit switch is triggered
  Serial.println("Starting calibration...");
  stepper.setMaxSpeed(pulsePerRev / 2);  // Slow speed for calibration

  // First, move to the left limit
  Serial.println("Moving to the left limit...");

  stepper.moveTo(- (totalLength / lead + 10) * pulsePerRev);  // Move left indefinitely (until the limit switch is hit)
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
  
    if (isCalibrating) {
      if (digitalRead(LEFT_LIMIT_PIN) == LOW ) {  // If left limit switch is triggered
        stepper.stop();  // Stop the motor
        stepper.setCurrentPosition(0);
        Serial.print("Left limit reached");


        // Now move to the right limit
        Serial.println("Moving to the right limit...");
        stepper.setMaxSpeed(pulsePerRev / 2);  // Slow speed for calibration
        stepper.moveTo((totalLength / lead + 10) * pulsePerRev);  // Move right indefinitely (until the right limit switch is hit)
        return;  // Wait for the next interrupt to check the right limit switch
      }
      
      if (digitalRead(RIGHT_LIMIT_PIN) == LOW) {  // If right limit switch is triggered
        stepper.stop();  // Stop the motor
        int rightLimitSteps = stepper.currentPosition();  // Record the motor position as the right limit
        Serial.print("Right limit reached. Steps: ");
        Serial.println(rightLimitSteps);

        // Move to the position based on displacementData[0]
        int stepsToMove = convertDisplacementToSteps(displacementData[0]);
        stepper.setMaxSpeed(pulsePerRev * maxRPM);  // Restore max speed
        stepper.moveTo(stepsToMove);  // Move to the first displacement
        return;
      }

      if (stepper.distanceToGo() == 0) {
        stepper.stop();  // Stop the motor
        Serial.println("Completed calibration.");
        isCalibrating = false;  // Exit calibration mode
        dataSize = 0; // Reset data size to indicate that no data is left
        stepper.setCurrentPosition(0);
        return;
      }

    }
  
  if (isSettingDisplacement) {
    if (digitalRead(LEFT_LIMIT_PIN) == LOW) {  // If left limit switch is triggered
      stepper.stop();  // Stop the motor
      Serial.println("Moving to displacementData[0].");

      stepper.setCurrentPosition(0);

      // Move to the position based on displacementData[0]
      int stepsToMove = convertDisplacementToSteps(displacementData[0]);
      stepper.setMaxSpeed(pulsePerRev * maxRPM);  // Restore max speed
      stepper.moveTo(stepsToMove);  // Move to the first displacement
      return;  // Do nothing if setting displacement data
    }

    // check if the motor reaches the distance
    if (stepper.distanceToGo() == 0) {
      stepper.stop();  // Stop the motor
      Serial.println("Displacement set.");
      isSettingDisplacement = false;  // Exit setting displacement mode
      dataSize = 0; // Reset data size to indicate that no data is left
      stepper.setCurrentPosition(0);
      return;  // Do nothing if setting displacement data
    }

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
    // Once all data has been executed, reset necessary variables
    currentIndex = 0;
    executeMotion = false;  // Stop execution after finishing the current displacement data
    dataSize = 0;           // Reset data size to indicate that no data is left
    endTime = millis();
    // print the time taken to execute the motion
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
  delay(100);    // Short delay to ensure the message is sent
  Serial.end();  // End the current serial connection

  baudRate = newBaudRate;  // Set the new baud rate
  Serial.begin(baudRate);  // Reinitialize the serial communication with the new baud rate
  Serial.println("Baud rate changed to: " + String(baudRate));
}

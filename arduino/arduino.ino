// #include <AccelStepper.h>
// #include <TimerOne.h>

// #define STEP_PIN 2  // Pin for step signal
// #define DIR_PIN 3   // Pin for direction signal

// AccelStepper stepper(AccelStepper::DRIVER, STEP_PIN, DIR_PIN);  // Use AccelStepper in driver mode

// const int maxDisplacement = 400;  // Maximum number of displacement points to handle
// volatile float displacementData[maxDisplacement];  // Array to store incoming displacement data
// volatile int dataSize = 0;  // Number of data points received
// volatile int currentIndex = 0;  // Current index in the displacement array
// volatile bool executeMotion = false;  // Flag to start executing motion

// unsigned long baudRate = 250000;  // Or even higher

// void setup() {
//   Serial.begin(baudRate);  // Initialize serial communication at default baud rate
//   stepper.setMaxSpeed(1000);  // Set max speed for the stepper motor (adjust as needed)
//   stepper.setAcceleration(500);  // Set acceleration (adjust as needed)

//   Timer1.initialize(10000);  // 10 ms timer interrupt (100 Hz)
//   Timer1.attachInterrupt(updateMotorPosition);  // Attach the interrupt handler
// }

// void loop() {
//   if (Serial.available() > 0) {
//     String command = Serial.readStringUntil('\n');  // Read a command from the GUI

//     // Check if the command is a baud rate change request (e.g., "BR:9600")
//     if (command.startsWith("BR:")) {
//       long newBaudRate = command.substring(3).toInt();  // Extract the baud rate value
//       if (newBaudRate > 0) {
//         changeBaudRate(newBaudRate);  // Change the baud rate
//       }
//     }
//     else if (command == "START") {
//       // If we receive the "START" command, set the flag to start executing the motion
//       executeMotion = true;
//       // print the number of data points to be executed
//       Serial.println("Number of data points to be executed: " + String(dataSize));
//       Serial.println("Start executing displacement data.");
//     }
//     else {
//       receiveDisplacementData(command);  // Process normal displacement data
//     }
//   }
// }

// // Function to receive displacement data
// void receiveDisplacementData(String dataString) {
//   float displacement = dataString.toFloat();
//   if (dataSize < maxDisplacement) {
//     noInterrupts();
//     displacementData[dataSize] = displacement;
//     dataSize++;
//     interrupts();
//   } else {
//     Serial.println("Displacement data buffer full.");
//   }
// }

// // Interrupt Service Routine (ISR) to update the motor position at 100 Hz
// void updateMotorPosition() {
//   if (dataSize == 0 || !executeMotion) return;  // Do nothing if no data or not started

//   float displacement = displacementData[currentIndex];
//   int steps = convertDisplacementToSteps(displacement);
//   stepper.moveTo(steps);
//   stepper.run();

//   currentIndex++;
//   if (currentIndex >= dataSize) {
//     // Once all data has been executed, reset necessary variables
//     currentIndex = 0;  
//     executeMotion = false;  // Stop execution after finishing the current displacement data
//     dataSize = 0;           // Reset data size to indicate that no data is left
//     Serial.println("Displacement execution completed.");
//   }
// }

// // Function to convert displacement to motor steps
// int convertDisplacementToSteps(float displacement) {
//   float stepConversionFactor = 50000.0;
//   return (int)(displacement * stepConversionFactor);
// }

// // Function to change the baud rate dynamically
// void changeBaudRate(long newBaudRate) {
//   Serial.println("Changing baud rate...");
//   delay(100);  // Short delay to ensure the message is sent
//   Serial.end();  // End the current serial connection

//   baudRate = newBaudRate;  // Set the new baud rate
//   Serial.begin(baudRate);  // Reinitialize the serial communication with the new baud rate
//   Serial.println("Baud rate changed to: " + String(baudRate));
// }

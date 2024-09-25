// #include <AccelStepper.h>

// #define STEP_PIN 2  // Pin for step signal
// #define DIR_PIN 3   // Pin for direction signal

// // Create an instance of AccelStepper in DRIVER mode
// AccelStepper stepper(AccelStepper::DRIVER, STEP_PIN, DIR_PIN);

// const int pulsePerRev = 200;  // Number of steps per revolution
// const float maxRPM = 1200;     // Maximum speed in RPM
// unsigned long startTime = 0;  // Variable to store start time
// unsigned long endTime = 0;    // Variable to store end time
// bool motionStarted = false;   // Flag to indicate if the motion has started
// bool motionCompleted = false; // Flag to indicate if the motion has been completed

// void setup() {
//   Serial.begin(115200);  // Start serial communication for debugging
  
//   // Set the maximum speed in steps per second
//   stepper.setMaxSpeed(pulsePerRev * maxRPM / 60);  // Max speed in steps per second
  
//   // Set acceleration to avoid missing steps
//   stepper.setAcceleration(300000 * pulsePerRev);  // Set acceleration

//   Serial.println("Starting the motor...");
// }

// void loop() {
//   // Start motion if it has not started yet
//   if (!motionStarted) {
//     // Store the start time and set the flag
//     startTime = millis();
//     motionStarted = true;
//     motionCompleted = false;

//     // Move the motor to a set position (adjust for testing)
//     stepper.moveTo(pulsePerRev * maxRPM/10);  // Command the motor to rotate 10 revolutions
//   }

//   // Run the motor towards the target
//   stepper.run();

//   // Check if the motor has reached the target position and the motion is not yet marked as completed
//   if (stepper.distanceToGo() == 0 && !motionCompleted) {
//     // Store the end time and calculate the duration
//     endTime = millis();
//     unsigned long duration = endTime - startTime;

//     // Print the time taken
//     Serial.print("Motion completed in ");
//     Serial.print(duration);
//     Serial.println(" milliseconds.");

//     // Set the flag to indicate the motion has been completed
//     motionCompleted = true;
//   }
// }

// #include <AccelStepper.h>
// #include <TimerOne.h>
// #include <math.h>  // For cosine calculations

// #define STEP_PIN 2  // Pin for step signal
// #define DIR_PIN 3   // Pin for direction signal

// // Create an instance of AccelStepper in DRIVER mode
// AccelStepper stepper(AccelStepper::DRIVER, STEP_PIN, DIR_PIN);

// const int pulsePerRev = 200;  // Number of steps per revolution
// const float maxRPM = 1200;     // Maximum speed in RPM
// const float period = 1.0;     // Period of cosine wave in seconds
// const int totalSteps = pulsePerRev;  // Total steps for 1 revolution
// bool motion = true;

// volatile float t = 0;  // Time variable for cosine displacement calculation
// const float timeStep = 0.01;  // Time step for 100 Hz (0.01s = 100 Hz)
// volatile int targetPosition = 0;  // The position we are calculating in the timer callback

// void setup() {
//   Serial.begin(115200);  // Start serial communication for debugging
  
//   // Set the maximum speed in steps per second
//   stepper.setMaxSpeed(pulsePerRev * maxRPM / 60);  // Max speed in steps per second
  
//   // Set acceleration for smoother motion
//   stepper.setAcceleration(10000 * pulsePerRev);  // Acceleration set based on motor's capabilities

//   Serial.println("Starting cosine displacement test for the stepper motor with 100 Hz hardware timer...");

//   // Initialize Timer1 and set it to trigger every 10 ms (100 Hz)
//   Timer1.initialize(10000);  // 10 ms interval (10000 µs = 100 Hz)
//   Timer1.attachInterrupt(timerCallback);  // Attach the interrupt handler
// }

// void loop() {
//   // Move the motor towards the target position set by the timer callback
//   stepper.moveTo(targetPosition);
//   stepper.run();  // Ensure the motor is moving continuously towards the target
// }

// // Interrupt handler called by Timer1 every 10ms (100 Hz)
// void timerCallback() {
//   if (!motion) return;
  
//   // Calculate cosine displacement (angular position) in steps for one full revolution
//   float cosineDisplacement = totalSteps * (1 - cos((2 * PI * t) / period));

//   // Update the target position
//   targetPosition = (int)cosineDisplacement;

//   // Increment time step for the cosine calculation
//   t += timeStep;

//   // Reset `t` if the period has been completed (stop the motion after one cycle)
//   if (t >= period) {
//     t = 0;
//     motion = false;  // Stop the motor after one full cycle
//     Serial.println("Motion complete.");
//   }
// }

#include <AccelStepper.h>
#include <TimerOne.h>
#include <math.h>  // For cosine calculations

#define STEP_PIN 2  // Pin for step signal
#define DIR_PIN 3   // Pin for direction signal

// Create an instance of AccelStepper in DRIVER mode
AccelStepper stepper(AccelStepper::DRIVER, STEP_PIN, DIR_PIN);

const int pulsePerRev = 10000;  // 10,000 pulses per revolution
const float maxRevolutions = 2.0;  // Maximum rotation in revolutions (adjust as needed)
const float period = 5.0;  // Period of cosine wave in seconds (adjust for desired speed)
const float maxRPM = 1500;  // Maximum speed in RPM (adjust as needed)

volatile float t = 0;  // Time variable to calculate the cosine displacement
const float timeStep = 0.001;  // Time step for calculating the next position (in seconds)

// Timer interrupt interval (set for 1 ms or 1000 Hz)
const unsigned long interval = 1000;  // 1 ms = 1000 µs

void setup() {
  Serial.begin(115200);  // Start serial communication for debugging
  stepper.setMaxSpeed(pulsePerRev * maxRPM / 60);  // Set max speed for the stepper motor (adjust as needed)
  stepper.setAcceleration(10000*pulsePerRev);  // Set acceleration (adjust as needed)
  
  Serial.println("Starting cosine displacement test for the stepper motor with hardware timer...");

  // Initialize Timer1 and set it to trigger every 1ms
  //Timer1.initialize(interval);  // 1 ms interval
  //Timer1.attachInterrupt(timerCallback);  // Attach the interrupt handler
}

void loop() {
  // The main loop remains empty as the motor is controlled by the timer interrupt
  stepper.moveTo(10000*2);
  stepper.run();
}

// Interrupt handler called by Timer1 every 1ms (1000 Hz)
void timerCallback() {
  // Calculate cosine displacement (angular position) in revolutions
  float cosineDisplacement = maxRevolutions * (1 - cos((2 * PI * t) / period));

  // Convert the angular displacement to steps
  int targetSteps = (int)(cosineDisplacement * pulsePerRev);

  // Move the stepper motor to the calculated position
  stepper.moveTo(targetSteps);
  stepper.run();  // Ensure the motor moves to the new position

  // Increment time step for the cosine calculation
  t += timeStep;

  // Reset `t` if the period has been completed (start a new cycle)
  if (t >= period) {
    t = 0;
  }
}

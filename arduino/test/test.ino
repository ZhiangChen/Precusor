#include <AccelStepper.h>
#include <DueTimer.h>

#define STEP_PIN 2         // Pin for step signal
#define DIR_PIN 3          // Pin for direction signal
#define LEFT_LIMIT_PIN 4   // Pin for left limit switch; motor is at the left side
#define RIGHT_LIMIT_PIN 5  // Pin for right limit switch

AccelStepper stepper(AccelStepper::DRIVER, STEP_PIN, DIR_PIN);  // Use AccelStepper in driver mode

int pulsePerRev = 200;        // Number of steps per revolution
float maxRPM = 1200;          // Increase maximum speed in RPM
float lead = 0.02;            // Distance traveled per revolution in meters
float maxAcceleration = 1.1;  // Maximum acceleration in g
float totalLength = 0.6;      // Total length of the shakebot in meters

const int maxDisplacement = 100*150;                   // Maximum number of displacement points to handle
volatile int displacementData[maxDisplacement];  // Array to store incoming displacement data
volatile int dataSize = 0;                         // Number of data points received
volatile int currentIndex = 0;                     // Current index in the displacement array
volatile bool executeMotion = false;               // Flag to start executing motion
// start time and end time for the motion
unsigned long startTime = 0;
unsigned long endTime = 0;

bool isSettingDisplacement = false;  // Flag to indicate setting displacement data
bool isCalibrating = false;          // Flag to indicate calibration (moving to left limit)

bool leftLimitReached = false;  // Flag to indicate left limit reached
bool rightLimitReached = false; // Flag to indicate right limit reached

unsigned long baudRate = 250000;  // Or even higher

int cycle = 0;
int cycleCount = 100 * 4;

void setup() {
  Serial.begin(baudRate);                                                    // Initialize serial communication at default baud rate
  stepper.setMaxSpeed(pulsePerRev * maxRPM);                                 // Set max speed for the stepper motor (adjust as needed)
  stepper.setAcceleration(int(maxAcceleration * pulsePerRev * 9.8 / lead));  // Set acceleration (adjust as needed)

  pinMode(LEFT_LIMIT_PIN, INPUT_PULLUP);   // Initialize limit switch pin with pullup resistor
  pinMode(RIGHT_LIMIT_PIN, INPUT_PULLUP);  // Initialize right limit switch pin

  Timer1.attachInterrupt(updateMotorPosition).start(10000);  // 10 ms timer interrupt (100 Hz)
}

void loop() {
  stepper.run();
}

void updateMotorPosition() {
    // set a loop to implement a simple sine wave motion: one step forward, one step backward, one step backward, and step forward
    if (cycle == 0) {
        // print the time 
        Serial.print("Time start: ");
        Serial.println(millis());
    }
    if (cycle < cycleCount) {
        if (cycle % 4 == 0) {
        stepper.moveTo(1);
        } else if (cycle % 4 == 1) {
        stepper.moveTo(-1);
        } else if (cycle % 4 == 2) {
        stepper.moveTo(-1);
        } else if (cycle % 4 == 3) {
        stepper.moveTo(1);
        }
        cycle++;
    }
    if (cycle == cycleCount) {
        // print the time
        Serial.print("Time end: ");
        Serial.println(millis());
        cycle = 0;
    }
}
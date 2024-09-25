#include <SPI.h>

// Define ADXL362 register addresses
#define ADXL362_REG_DEVID_AD        0x00
#define ADXL362_REG_DEVID_MST       0x01
#define ADXL362_REG_XDATA_L         0x0E
#define ADXL362_REG_XDATA_H         0x0F
#define ADXL362_REG_YDATA_L         0x10
#define ADXL362_REG_YDATA_H         0x11
#define ADXL362_REG_ZDATA_L         0x12
#define ADXL362_REG_ZDATA_H         0x13
#define ADXL362_REG_POWER_CTL       0x2D
#define ADXL362_REG_FILTER_CTL      0x2C
#define ADXL362_REG_SELF_TEST       0x2E
#define ADXL362_REG_SOFT_RESET      0x1F

// Define pins
const int CS_PIN = 10;  // Chip Select (CS) pin for SPI

// Variables for offset calibration
float xOffset = 0.0;
float yOffset = 0.0;
float zOffset = 0.0;

// Function prototypes
void setupADXL362();
void calibrateADXL362();
void readAcceleration(float &x, float &y, float &z);
uint8_t readRegister(uint8_t reg);
void writeRegister(uint8_t reg, uint8_t value);
void softResetADXL362();

void setup() {
  // Initialize Serial
  Serial.begin(115200);
  // Initialize SPI and configure settings
  SPI.begin();
  pinMode(CS_PIN, OUTPUT);
  digitalWrite(CS_PIN, HIGH);  // CS pin is idle HIGH

  // Setup the ADXL362
  setupADXL362();

  // Optional: Calibrate ADXL362 to get offsets
  calibrateADXL362();
}

void loop() {
  float xAccel, yAccel, zAccel;

  // Read acceleration data from ADXL362
  readAcceleration(xAccel, yAccel, zAccel);

  // Apply calibration offsets
  xAccel -= xOffset;
  yAccel -= yOffset;
  zAccel -= zOffset;

  // Print the calibrated acceleration values
  Serial.print("X: "); Serial.print(xAccel); Serial.print(" g, ");
  Serial.print("Y: "); Serial.print(yAccel); Serial.print(" g, ");
  Serial.print("Z: "); Serial.print(zAccel); Serial.println(" g");

  delay(500);  // Delay between readings
}

void setupADXL362() {
  // Soft reset the ADXL362
  softResetADXL362();
  delay(10);  // Wait after reset

  // Set the filter control to 4g range and 100 Hz output data rate
  writeRegister(ADXL362_REG_FILTER_CTL, 0x13);

  // Power on the ADXL362 in measurement mode
  writeRegister(ADXL362_REG_POWER_CTL, 0x02);
}

void calibrateADXL362() {
  Serial.println("Calibrating... Keep the sensor stable.");

  // Take 100 samples to calculate offset
  int numSamples = 100;
  float xSum = 0.0, ySum = 0.0, zSum = 0.0;

  for (int i = 0; i < numSamples; i++) {
    float x, y, z;
    readAcceleration(x, y, z);
    xSum += x;
    ySum += y;
    zSum += z;
    delay(10);  // Short delay between samples
  }

  // Calculate average offset
  xOffset = xSum / numSamples;
  yOffset = ySum / numSamples;
  zOffset = (zSum / numSamples) - 1.0;  // Gravity is expected on Z axis

  Serial.println("Calibration complete.");
  Serial.print("X Offset: "); Serial.println(xOffset);
  Serial.print("Y Offset: "); Serial.println(yOffset);
  Serial.print("Z Offset: "); Serial.println(zOffset);
}

void readAcceleration(float &x, float &y, float &z) {
  // Read raw acceleration data from X, Y, Z registers
  int16_t xData = (int16_t)((readRegister(ADXL362_REG_XDATA_H) << 8) | readRegister(ADXL362_REG_XDATA_L));
  int16_t yData = (int16_t)((readRegister(ADXL362_REG_YDATA_H) << 8) | readRegister(ADXL362_REG_YDATA_L));
  int16_t zData = (int16_t)((readRegister(ADXL362_REG_ZDATA_H) << 8) | readRegister(ADXL362_REG_ZDATA_L));

  // Convert raw data to g
  x = xData * 0.001;  // 1 mg/LSB
  y = yData * 0.001;  // 1 mg/LSB
  z = zData * 0.001;  // 1 mg/LSB
}

uint8_t readRegister(uint8_t reg) {
  digitalWrite(CS_PIN, LOW);  // Select the sensor
  SPI.transfer(0x0B);         // Send read command
  SPI.transfer(reg);           // Send register address
  uint8_t data = SPI.transfer(0x00);  // Read register data
  digitalWrite(CS_PIN, HIGH);  // Deselect the sensor
  return data;
}

void writeRegister(uint8_t reg, uint8_t value) {
  digitalWrite(CS_PIN, LOW);  // Select the sensor
  SPI.transfer(0x0A);         // Send write command
  SPI.transfer(reg);           // Send register address
  SPI.transfer(value);         // Write the value
  digitalWrite(CS_PIN, HIGH);  // Deselect the sensor
}

void softResetADXL362() {
  writeRegister(ADXL362_REG_SOFT_RESET, 0x52);  // Soft reset command
}

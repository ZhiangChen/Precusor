#define LEFT_LIMIT_PIN 4  // Pin for left limit switch
#define RIGHT_LIMIT_PIN 5  // Pin for right limit switch

void setup() {
  pinMode(LEFT_LIMIT_PIN, INPUT_PULLUP);
  pinMode(RIGHT_LIMIT_PIN, INPUT_PULLUP);
}

void loop() {
  if (digitalRead(LEFT_LIMIT_PIN) == LOW) {
    Serial.println("Left limit switch triggered.");
  }
  // print out high
  if (digitalRead(LEFT_LIMIT_PIN) == HIGH) {
    Serial.println("Left limit switch not triggered.");
  }
}
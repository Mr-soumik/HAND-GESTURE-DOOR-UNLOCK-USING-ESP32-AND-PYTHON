#include <ESP32Servo.h>

Servo doorServo;

const int servoPin = 18;
const int greenLedPin = 22;  
const int redLedPin = 23;    
const int buzzerPin = 21;    

const int LOCK_ANGLE = 90;
const int UNLOCK_ANGLE = 0;

void setup() {
  Serial.begin(115200);

  pinMode(greenLedPin, OUTPUT);
  pinMode(redLedPin, OUTPUT);
  pinMode(buzzerPin, OUTPUT);

  digitalWrite(greenLedPin, LOW);
  digitalWrite(redLedPin, LOW);
  digitalWrite(buzzerPin, LOW);

  ESP32PWM::allocateTimer(0);
  ESP32PWM::allocateTimer(1);
  ESP32PWM::allocateTimer(2);
  ESP32PWM::allocateTimer(3);

  doorServo.setPeriodHertz(50);
  doorServo.attach(servoPin, 500, 2400);

  doorServo.write(LOCK_ANGLE);
}


void playSuccessTone() {
  digitalWrite(buzzerPin, HIGH);
  delay(100);
  digitalWrite(buzzerPin, LOW);
  delay(80);
  digitalWrite(buzzerPin, HIGH);
  delay(180);
  digitalWrite(buzzerPin, LOW);
}


void playErrorTone() {
  for (int i = 0; i < 3; i++) {
    digitalWrite(buzzerPin, HIGH);
    delay(200);
    digitalWrite(buzzerPin, LOW);
    delay(100);
  }
}


void playLockTone() {
  digitalWrite(buzzerPin, HIGH);
  delay(120);
  digitalWrite(buzzerPin, LOW);
}

void loop() {
  if (Serial.available() > 0) {
    char cmd = Serial.read();

    if (cmd == 'U') {
      digitalWrite(redLedPin, LOW);
      digitalWrite(greenLedPin, HIGH);
      doorServo.write(UNLOCK_ANGLE);
      playSuccessTone();
    } 
    else if (cmd == 'W') {
      digitalWrite(greenLedPin, LOW);
      digitalWrite(redLedPin, HIGH);
      playErrorTone();
      digitalWrite(redLedPin, LOW);
    } 
    else if (cmd == 'L') {
      digitalWrite(greenLedPin, LOW);
      digitalWrite(redLedPin, LOW);
      doorServo.write(LOCK_ANGLE);
      playLockTone();
    }
  }
}

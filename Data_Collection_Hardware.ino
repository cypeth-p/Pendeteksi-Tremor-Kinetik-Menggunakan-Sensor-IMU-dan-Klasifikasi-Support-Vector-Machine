#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>

#define SDA_PIN 8
#define SCL_PIN 9

Adafruit_MPU6050 mpu;

unsigned long lastSampleTime = 0;
const unsigned long interval = 10; // 10ms for 100Hz

void setup() {
  Serial.begin(115200);
  
  Wire.begin(SDA_PIN, SCL_PIN);
  Wire.setClock(400000); 

  if (!mpu.begin()) {
    while (1) { delay(10); }
  }

  // Set sensitivity to maximum
  mpu.setAccelerometerRange(MPU6050_RANGE_2_G);
  mpu.setGyroRange(MPU6050_RANGE_250_DEG);

  /* REMOVED: mpu.setFilterBandwidth(...) 
     The sensor will now operate with its default/raw bandwidth settings.
  */

  Serial.println("time_ms,ax,ay,az,gx,gy,gz");
}

void loop() {
  unsigned long currentMillis = millis();

  // Strict 100Hz timing
  if (currentMillis - lastSampleTime >= interval) {
    lastSampleTime = currentMillis;

    sensors_event_t a, g, temp;
    mpu.getEvent(&a, &g, &temp);

    Serial.print(currentMillis);
    Serial.print(",");
    Serial.print(a.acceleration.x, 4);
    Serial.print(",");
    Serial.print(a.acceleration.y, 4);
    Serial.print(",");
    Serial.print(a.acceleration.z, 4);
    Serial.print(",");
    Serial.print(g.gyro.x, 4);
    Serial.print(",");
    Serial.print(g.gyro.y, 4);
    Serial.print(",");
    Serial.println(g.gyro.z, 4);
  }
}
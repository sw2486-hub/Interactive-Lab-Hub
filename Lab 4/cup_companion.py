import time
import qwiic_proximity
import pi_servo_hat

CUP_ON = 40
CUP_OFF = 20
SERVO_CH = 0

REST_ANGLE = 1
WAVE_ANGLE = 40

sensor = qwiic_proximity.QwiicProximity()

if not sensor.connected:
    raise SystemExit("Sensor not connected. Check the Qwiic cable.")

sensor.begin()

servo = pi_servo_hat.PiServoHat()
servo.restart()
servo.move_servo_position(SERVO_CH, REST_ANGLE)
time.sleep(0.5)

cup_present = False
on_count = 0
off_count = 0

print("Cup Companion ready. Press Ctrl+C to stop.")

try:
    while True:
        value = sensor.get_proximity()
        print("Proximity Value:", value)

        if not cup_present:
            on_count = on_count + 1 if value >= CUP_ON else 0

            if on_count >= 3:
                cup_present = True
                on_count = 0
                print("Cup detected! Waving.")

                for _ in range(3):
                    servo.move_servo_position(SERVO_CH, WAVE_ANGLE)
                    time.sleep(0.3)
                    servo.move_servo_position(SERVO_CH, REST_ANGLE)
                    time.sleep(0.3)

        else:
            off_count = off_count + 1 if value <= CUP_OFF else 0

            if off_count >= 3:
                cup_present = False
                off_count = 0
                print("Cup removed. Ready again.")

        time.sleep(0.1)

except KeyboardInterrupt:
    print("\nStopped.")

finally:
    servo.move_servo_position(SERVO_CH, REST_ANGLE)

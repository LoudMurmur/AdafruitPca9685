
import time

from random import randint
from pca9685lib import PCA9685, Servo

"""
This will make the laser turret move a little bit like the turret in the portal game
"""

PRESCALER_FOR_60Hz = 102 #this is different (+/- 10%) for each pca9685 

pca9685 = PCA9685()
pca9685.set_pwm_freq_precisely(PRESCALER_FOR_60Hz)

servoX = Servo(0, 60.1, 140, 650)
servoY = Servo(1, 60., 200, 780)

pca9685.set_pulse_length(servoX.channel, servoX.getMiddle())
pca9685.set_pulse_length(servoY.channel, servoY.getMiddle())
time.sleep(1)

counter = 0
while True:
    pca9685.set_pulse_length(servoX.channel, randint(servoX.getMiddle()-75, servoX.getMiddle()+75))
    pca9685.set_pulse_length(servoY.channel, randint(servoY.getMiddle()-75, servoY.getMiddle()+75))
    time.sleep(0.2)
    counter = counter + 1
    if counter > 10:
        print "sleeping"
        time.sleep(2)
        counter = 0
        print "going back to moving like crazy"

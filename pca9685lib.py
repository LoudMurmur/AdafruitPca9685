from __future__ import division
import time
import math
import Adafruit_GPIO.FT232H as FT232H

"""
The PCA9685 has an internal oscillator with a nominal frequency of 25MHz, driving an 8-bit prescale counter. For every N ticks of the 25MHz clock, the PWM clock ticks once.

The prescale register can hold 256 values (but only values larger than 3 will work), so there are 252 possible PWM frequencies.

The chip's internal oscillator is probably a basic RC timer. Those are usually accurate to about +/-5% without special trimming, and their frequency drifts by about 0.5%.

The information about the prescaler is on page 25 of the datasheet:
"""

class Servo():
    def __init__(self, channel, current_frequency, servomin, servomax):
        """
            channel : (int) the channel number of your servon on the pca9685 board
            current_frequency : (float) the current pc9685 pwm frequency
            servomin : (int) the required pulse lenght for the 0 degree position
            servomax : (int) the require pulse length for the 180 defree prosition
        """
        self.channel = channel
        self.servomin = servomin
        self.servomax = servomax

    def getMiddle(self):
        """
            Return the middle value of servomin/servomax which should be the 90 degree position
            return : (int) the pulse length for the 90 degree position 
        """
        zeroed_range = self.servomax - self.servomin
        zeroed_middle = zeroed_range/2
        true_middle = zeroed_middle + self.servomin
        print "Middle position for servo on channel {} is {} quantum".format(self.channel, true_middle)
        return int(true_middle)

class PCA9685():
    
    def __init__(self, pcs9685_address=0x40):
        self.PCA9685_ADDRESS    = pcs9685_address
        self.MODE1              = 0x00
        self.MODE2              = 0x01
        self.SUBADR1            = 0x02
        self.SUBADR2            = 0x03
        self.SUBADR3            = 0x04
        self.PRESCALE           = 0xFE
        self.LED0_ON_L          = 0x06
        self.LED0_ON_H          = 0x07
        self.LED0_OFF_L         = 0x08
        self.LED0_OFF_H         = 0x09
        self.ALL_LED_ON_L       = 0xFA
        self.ALL_LED_ON_H       = 0xFB
        self.ALL_LED_OFF_L      = 0xFC
        self.ALL_LED_OFF_H      = 0xFD
        #instructions
        self.RESTART            = 0x80
        self.SLEEP              = 0x10
        self.ALLCALL            = 0x01
        self.INVRT              = 0x10
        self.OUTDRV             = 0x04
        
        print "init I2C communication with Adafruit FT232H breakout board"
        # Temporarily disable FTDI serial drivers.
        FT232H.use_FT232H()
        # Find the first FT232H device.
        ft232h = FT232H.FT232H()
        # Create an I2C device at address 0x40.
        self.pca9685_device = FT232H.I2CDevice(ft232h, self.PCA9685_ADDRESS)
        
        print "init PCA 9685 BOARD"
        self.set_all_pwm(0, 0)
        self.pca9685_device.write8(self.MODE2, self.OUTDRV)
        self.pca9685_device.write8(self.MODE1, self.ALLCALL)
        time.sleep(0.005)  # wait for oscillator
        mode1 = self.pca9685_device.readU8(self.MODE1)
        mode1 = mode1 & ~self.SLEEP  # wake up (reset sleep)
        self.pca9685_device.write8(self.MODE1, mode1)
        time.sleep(0.005)  # wait for oscillator

    def set_pwm_freq_precisely(self, prescaler):
        """
            Here directly set the (int) prescaler you want, for my PCA9685 board I get
            those values :

            60 = 108.7Hz, 70 = 93.46Hz, 80 = 81.97Hz, 90 = 72.46Hz, 95 = 68.43Hz,
            102 = 64.1Hz, 110 = 60.24Hz, 111 = 59.52Hz, 120 = 54.64Hz, 130 = 50.76Hz,
            140 = 46.73Hz, 150 = 43.48Hz, 160 = 41.15Hz, 170 = 38.46Hz

            THOSE VALUES ARE DIFFERENT FOR EACH BOARD, YOU HAVE TO MEASURE THEM YOURSELF
            
            see : https://electronics.stackexchange.com/questions/335825/setting-the-pca9685-pwm-module-prescaler
            TL:DR : PCA9685 was not meant for precision because it was made to drive LEDs not servos
        """
        print "setting new prescaler value : {}".format(prescaler)
        oldmode = self.pca9685_device.readU8(self.MODE1);
        newmode = (oldmode & 0x7F) | 0x10    # sleep
        self.pca9685_device.write8(self.MODE1, newmode)  # go to sleep
        self.pca9685_device.write8(self.PRESCALE, prescaler)
        self.pca9685_device.write8(self.MODE1, oldmode)
        time.sleep(0.005)
        self.pca9685_device.write8(self.MODE1, oldmode | 0x80)

    def set_pwm_freq(self, freq_hz):
        """Set the PWM frequency to the provided value in hertz. using the
           formulage page 25 of the pca9685 datasheet, note that this is not precise at all.
           When I use it with a 60Hz value the board then generate a 64.5Hz value
        """
        print "changing pwm frequency"

        pca9685_frequency = 25000000.0 #pca9685 clock : 25Mhz
        pca9685_resolution = 4096.0 #12 bits resolution
        float_prescaler = pca9685_frequency/(pca9685_resolution*freq_hz)
        print "prescaler value for {} = {}".format(freq_hz, prescaleval)
        round_prescaler = int(math.floor(float_prescaler + 0.5))
        print "however only round values can be set so we wil use {} as a prescaler value".format(round_prescaler)
        print "which makes a theoretical frequency of {}".format(pca9685_frequency/(round_prescaler*pca9685_resolution))

        oldmode = self.pca9685_device.readU8(self.MODE1);
        newmode = (oldmode & 0x7F) | 0x10    # sleep
        self.pca9685_device.write8(self.MODE1, newmode)  # go to sleep
        self.pca9685_device.write8(self.PRESCALE, round_prescaler)
        self.pca9685_device.write8(self.MODE1, oldmode)
        time.sleep(0.005)
        self.pca9685_device.write8(self.MODE1, oldmode | 0x80)

    def set_pwm(self, channel, on, off):
        """Sets a single PWM channel."""
        print "setting pwm on channel {} to : ({}, {})".format(channel, on, off)
        self.pca9685_device.write8(self.LED0_ON_L+4*channel, on & 0xFF)
        self.pca9685_device.write8(self.LED0_ON_H+4*channel, on >> 8)
        self.pca9685_device.write8(self.LED0_OFF_L+4*channel, off & 0xFF)
        self.pca9685_device.write8(self.LED0_OFF_H+4*channel, off >> 8)

    def set_all_pwm(self, on, off):
        """Sets all PWM channels."""
        print "setting pwm all channel to to : ({}, {})".format(on, off)
        self.pca9685_device.write8(self.ALL_LED_ON_L, on & 0xFF)
        self.pca9685_device.write8(self.ALL_LED_ON_H, on >> 8)
        self.pca9685_device.write8(self.ALL_LED_OFF_L, off & 0xFF)
        self.pca9685_device.write8(self.ALL_LED_OFF_H, off >> 8)

    def set_pulse_length(self, channel, pulse_length):
        """
            used to drive servos, ledn_on is always 0 and ledn_off is pulse length
            the pca9685 has a 4096 resolution so to get a 20% pwm you use a pulse_length
            if 20% of 4096, the time of that pulse will depend of the current frequency
        """
        self.set_pwm(channel, 0, pulse_length)

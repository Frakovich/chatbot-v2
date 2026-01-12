import time
import spidev
import RPi.GPIO as GPIO
from waveshare_config import CONFIGS

print("=== FIX COLORS TEST (RED - GREEN - BLUE) ===")

def test_screen(conf, color_bytes, name):
    print(f"Testing {conf['name']} with {name}...")
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(conf['rst'], GPIO.OUT)
    GPIO.setup(conf['dc'], GPIO.OUT)
    GPIO.setup(conf['bl'], GPIO.OUT)
    GPIO.output(conf['bl'], GPIO.HIGH)
    
    GPIO.output(conf['rst'], GPIO.HIGH); time.sleep(0.05)
    GPIO.output(conf['rst'], GPIO.LOW); time.sleep(0.05)
    GPIO.output(conf['rst'], GPIO.HIGH); time.sleep(0.05)
    
    spi = spidev.SpiDev()
    spi.open(conf['spi_bus'], conf['spi_device'])
    spi.max_speed_hz = 20000000
    spi.mode = 0b00
    
    def write_cmd(cmd):
        GPIO.output(conf['dc'], GPIO.LOW)
        spi.writebytes([cmd])
    def write_data(data):
        GPIO.output(conf['dc'], GPIO.HIGH)
        spi.writebytes([data])
        
    write_cmd(0x11); time.sleep(0.12)
    
    # Use the madctl value defined in waveshare_config.py
    # Center is 0x00 (RGB), Sides are 0x08 (BGR)
    madctl = conf['madctl']
        
    write_cmd(0x36); write_data(madctl)
    write_cmd(0x3A); write_data(0x05)
    write_cmd(0x21) # Inversion On (Waveshare use often inverted colors)
    write_cmd(0x29) # Display On
    
    write_cmd(0x2C)
    GPIO.output(conf['dc'], GPIO.HIGH)
    
    # Fill screen with color
    pixels = color_bytes * 240
    for _ in range(240):
        spi.writebytes(pixels)
    spi.close()

# Couleurs RGB565
RED   = [0xF8, 0x00]
GREEN = [0x07, 0xE0]
BLUE  = [0x00, 0x1F]

try:
    test_screen(CONFIGS[0], RED, "RED")     # Center
    test_screen(CONFIGS[1], GREEN, "GREEN") # Left
    test_screen(CONFIGS[2], BLUE, "BLUE")   # Right
    print("\nCheck: Center=RED, Side1=GREEN, Side2=BLUE")
    time.sleep(5)
finally:
    GPIO.cleanup()

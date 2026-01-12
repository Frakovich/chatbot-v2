import time
import spidev
import RPi.GPIO as GPIO
from waveshare_config import LCD_1_3

def test_primaries(conf):
    print(f"Testing PRIMARIES on {conf['name']}...")
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(conf['rst'], GPIO.OUT)
    GPIO.setup(conf['dc'], GPIO.OUT)
    GPIO.setup(conf['bl'], GPIO.OUT)
    GPIO.output(conf['bl'], GPIO.HIGH)
    
    # Reset
    GPIO.output(conf['rst'], GPIO.HIGH); time.sleep(0.05)
    GPIO.output(conf['rst'], GPIO.LOW); time.sleep(0.05)
    GPIO.output(conf['rst'], GPIO.HIGH); time.sleep(0.05)
    
    spi = spidev.SpiDev()
    spi.open(conf['spi_bus'], conf['spi_device'])
    spi.max_speed_hz = 40000000 # ST7789 supporte plus vite
    spi.mode = 0b00
    
    def write_cmd(cmd):
        GPIO.output(conf['dc'], GPIO.LOW)
        spi.writebytes([cmd])
    def write_data(data):
        GPIO.output(conf['dc'], GPIO.HIGH)
        spi.writebytes([data])
        
    write_cmd(0x11); time.sleep(0.12)
    
    write_cmd(0x36); write_data(conf['madctl']) 
    write_cmd(0x3A); write_data(0x05)
    write_cmd(0x21) # Inversion On
    write_cmd(0x29) # Display On
    
    # ST7789 RAM size is typically 240x320, but window is 240x240 usually.
    # Brute Force: 240x240
    max_w, max_h = 240, 240
    
    # Write Window
    write_cmd(0x2A); write_data(0x00); write_data(0x00); write_data(0x00); write_data(max_w - 1)
    write_cmd(0x2B); write_data(0x00); write_data(0x00); write_data(0x00); write_data(max_h - 1)
    write_cmd(0x2C)
    
    total_pixels = max_w * max_h
    chunk_size = 4096

    def fill(color_bytes, name):
        print(f" -> Displaying {name}...")
        data = color_bytes * total_pixels
        write_cmd(0x2C)
        GPIO.output(conf['dc'], GPIO.HIGH)
        for i in range(0, len(data), chunk_size):
            spi.writebytes(data[i:i + chunk_size])
        time.sleep(2)

    # ROUGE (0xF800)
    fill([0xF8, 0x00], "RED (0xF800)")
    
    # VERT (0x07E0)
    fill([0x07, 0xE0], "GREEN (0x07E0)")
    
    # BLEU (0x001F)
    fill([0x00, 0x1F], "BLUE (0x001F)")

    spi.close()

try:
    test_primaries(LCD_1_3)
finally:
    GPIO.cleanup()

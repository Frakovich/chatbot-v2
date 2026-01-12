import time
import spidev
import RPi.GPIO as GPIO
from waveshare_config import LCD_0_96_1

def turn_on_yellow(conf):
    print(f"Turning {conf['name']} YELLOW...")
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
    spi.max_speed_hz = 20000000
    spi.mode = 0b00
    
    def write_cmd(cmd):
        GPIO.output(conf['dc'], GPIO.LOW)
        spi.writebytes([cmd])
    def write_data(data):
        GPIO.output(conf['dc'], GPIO.HIGH)
        spi.writebytes([data])
        
    write_cmd(0x11); time.sleep(0.12) # Sleep out
    
    # Use madctl from config
    write_cmd(0x36); write_data(conf['madctl'])
    
    write_cmd(0x3A); write_data(0x05) # Interface pixel format (16-bit)
    write_cmd(0x21) # Display Inversion On (Standard for these Waveshare screens)
    write_cmd(0x29) # Display On
    
    # Column/Row address set for 160x80
    write_cmd(0x2A); write_data(0x00); write_data(conf['col_start']); write_data(0x00); write_data(conf['col_start'] + conf['width'] - 1)
    write_cmd(0x2B); write_data(0x00); write_data(conf['row_start']); write_data(0x00); write_data(conf['row_start'] + conf['height'] - 1)
    
    write_cmd(0x2C) # Memory write
    GPIO.output(conf['dc'], GPIO.HIGH)
    
    # Purple in RGB565 is 0xF81F (Red + Blue)
    purple_pixel = [0xF8, 0x1F]
    
    # BRUTE FORCE: Fill the entire possible RAM of ST7735S (132x162)
    # This ensures we cover the visible area regardless of offsets or rotation.
    
    max_w = 132
    max_h = 162
    
    # Set window to full RAM
    write_cmd(0x2A); write_data(0x00); write_data(0x00); write_data(0x00); write_data(max_w - 1)
    write_cmd(0x2B); write_data(0x00); write_data(0x00); write_data(0x00); write_data(max_h - 1)
    
    write_cmd(0x2C) # Memory write
    GPIO.output(conf['dc'], GPIO.HIGH)
    
    # Fill the entire RAM buffer
    total_pixels = max_w * max_h
    full_screen_data = purple_pixel * total_pixels
    
    # Send data in chunks
    chunk_size = 4096
    for i in range(0, len(full_screen_data), chunk_size):
        spi.writebytes(full_screen_data[i:i + chunk_size])
        
    print(f"Done. Screen {conf['name']} RAM (132x162) filled with PURPLE.")
    # We don't close SPI or cleanup GPIO to keep the display on
    # but in a script like this, it's better to stay alive or just exit without cleanup
    # spi.close()

if __name__ == "__main__":
    try:
        turn_on_yellow(LCD_0_96_1)
    except KeyboardInterrupt:
        GPIO.cleanup()

import time
import sys
import spidev
import RPi.GPIO as GPIO
from PIL import Image, ImageDraw, ImageFont

# Configuration Pi 5 pour l'écran 1.3" (SPI1)
RST = 27
DC = 22
BL = 19
SPI_BUS = 1
SPI_DEVICE = 0

def show_bonjour():
    print("Affichage 'Bonjour' via méthode directe SPI...")
    
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(RST, GPIO.OUT)
    GPIO.setup(DC, GPIO.OUT)
    GPIO.setup(BL, GPIO.OUT)

    GPIO.output(BL, GPIO.HIGH)
    GPIO.output(RST, GPIO.LOW); time.sleep(0.01)
    GPIO.output(RST, GPIO.HIGH); time.sleep(0.01)

    spi = spidev.SpiDev()
    spi.open(SPI_BUS, SPI_DEVICE)
    spi.max_speed_hz = 40000000
    spi.mode = 0b00

    def write_cmd(cmd):
        GPIO.output(DC, GPIO.LOW)
        spi.writebytes([cmd])

    def write_data(data):
        GPIO.output(DC, GPIO.HIGH)
        spi.writebytes([data])

    # Init ST7789
    write_cmd(0x11); time.sleep(0.12)
    write_cmd(0x36); write_data(0x00)
    write_cmd(0x3A); write_data(0x05)
    write_cmd(0x21)
    write_cmd(0x29)

    # Création Image avec PIL
    image = Image.new('RGB', (240, 240), (0, 0, 100))
    draw = ImageDraw.Draw(image)
    
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
    except:
        font = ImageFont.load_default()

    draw.text((30, 90), "BONJOUR", font=font, fill=(255, 255, 255))
    
    # Conversion image en bytes RGB565
    raw_data = []
    for y in range(240):
        for x in range(240):
            r, g, b = image.getpixel((x, y))
            # RGB888 to RGB565
            color = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
            raw_data.append((color >> 8) & 0xFF)
            raw_data.append(color & 0xFF)

    # Envoi RAMWR
    write_cmd(0x2A); write_data(0x00); write_data(0x00); write_data(0x00); write_data(0xEF)
    write_cmd(0x2B); write_data(0x00); write_data(0x00); write_data(0x00); write_data(0xEF)
    write_cmd(0x2C)
    
    GPIO.output(DC, GPIO.HIGH)
    # Envoi par morceaux (SPI buffer limit)
    chunk_size = 4096
    for i in range(0, len(raw_data), chunk_size):
        spi.writebytes(raw_data[i:i+chunk_size])

    print("Affiché !")
    time.sleep(5)
    spi.close()

if __name__ == "__main__":
    try:
        show_bonjour()
    finally:
        GPIO.cleanup()
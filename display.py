# Description:
# This file provides an object-oriented driver for the ST7789 and ST7735S display
# controllers used in the Waveshare Triple LCD Hat. It is based on the procedural
# logic found in the original test scripts (test_bonjour_3_ecrans.py) which are
# confirmed to work on the Raspberry Pi 5.

import spidev
import RPi.GPIO as GPIO
import time
from PIL import Image

class ST7789:
    """
    Object-oriented driver for the Waveshare LCDs.
    """
    def __init__(self, config):
        """
        Initializes the display.
        Args:
            config (dict): A dictionary from waveshare_config.py (e.g., LCD_1_3).
        """
        self.config = config
        self.spi = spidev.SpiDev()
        
        # Use BCM GPIO numbering, as used in the working test scripts
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        # Open SPI bus
        self.spi.open(self.config['spi_bus'], self.config['spi_device'])
        self.spi.max_speed_hz = 60000000  # Set a high speed
        self.spi.mode = 0b00

        # Setup control pins
        GPIO.setup(self.config['rst'], GPIO.OUT)
        GPIO.setup(self.config['dc'], GPIO.OUT)
        GPIO.setup(self.config['bl'], GPIO.OUT)

        self._init_lcd()

    def _send_cmd(self, cmd):
        """Sends a command to the display."""
        GPIO.output(self.config['dc'], GPIO.LOW)
        self.spi.writebytes([cmd])

    def _send_data(self, data):
        """Sends data to the display."""
        GPIO.output(self.config['dc'], GPIO.HIGH)
        self.spi.writebytes(data)

    def _init_lcd(self):
        """Initializes the LCD controller based on the working test script."""
        GPIO.output(self.config['bl'], GPIO.HIGH)  # Backlight on
        
        # Hardware reset
        GPIO.output(self.config['rst'], GPIO.HIGH); time.sleep(0.01)
        GPIO.output(self.config['rst'], GPIO.LOW); time.sleep(0.01)
        GPIO.output(self.config['rst'], GPIO.HIGH); time.sleep(0.1)

        # Common initialization commands from test_bonjour_3_ecrans.py
        self._send_cmd(0x11)  # Sleep out
        time.sleep(0.12)
        
        self._send_cmd(0x3A)  # COLMOD (Pixel Format)
        self._send_data([0x05])  # 16-bit RGB565
        
        self._send_cmd(0x36)  # MADCTL (Memory Access Control)
        self._send_data([self.config['madctl']])
        
        self._send_cmd(0x21)  # Display Inversion ON
        self._send_cmd(0x29)  # Display ON

    def display(self, image):
        """
        Takes a PIL Image and displays it on the screen.
        """
        # Apply software rotation if needed (defined in config)
        if self.config.get('rotation', 0) != 0:
            image = image.rotate(self.config['rotation'])

        width, height = image.size
        
        # Get offsets from config, default to 0
        col_start = self.config.get('col_start', 0)
        row_start = self.config.get('row_start', 0)
        
        # Set the drawing window
        self._send_cmd(0x2A)  # CASET (Column Address Set)
        x_end = col_start + width - 1
        self._send_data([col_start >> 8, col_start & 0xFF, x_end >> 8, x_end & 0xFF])
        
        self._send_cmd(0x2B)  # RASET (Row Address Set)
        y_end = row_start + height - 1
        self._send_data([row_start >> 8, row_start & 0xFF, y_end >> 8, y_end & 0xFF])
        
        # Start memory write
        self._send_cmd(0x2C)  # RAMWR
        
        GPIO.output(self.config['dc'], GPIO.HIGH)
        
        # Convert PIL image to RGB565 byte array
        pixels = list(image.getdata())
        data = []
        for r, g, b in pixels:
            val = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
            data.append(val >> 8)
            data.append(val & 0xFF)
            
        # Write data in chunks for performance
        chunk_size = 4096
        for i in range(0, len(data), chunk_size):
            self.spi.writebytes(data[i:i+chunk_size])

    @property
    def width(self):
        return self.config['width']

    @property
    def height(self):
        return self.config['height']

    def close(self):
        """Closes the SPI connection."""
        self.spi.close()
        # The main app should handle GPIO.cleanup() at the very end.

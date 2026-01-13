import RPi.GPIO as GPIO
import spidev
import time
from waveshare_config import LCD_1_3, KEYS

class WhisplayBoard:
    # LCD parameters (Adapted for Waveshare 1.3 inch)
    LCD_WIDTH = 240
    LCD_HEIGHT = 240 # Original was 280, but this screen is 240x240
    CornerHeight = 0 # No rounded corners on this square display likely needed
    
    # Mapping configuration
    CONF = LCD_1_3
    
    # Backlight
    LED_PIN = CONF['bl']
    
    # Button (Mapping KEY1 to the main interaction button)
    BUTTON_PIN = KEYS['KEY1'] 

    def __init__(self):
        GPIO.setmode(GPIO.BCM) # Using BCM as per waveshare_config
        GPIO.setwarnings(False)

        # Initialize LCD pins
        GPIO.setup(self.CONF['rst'], GPIO.OUT)
        GPIO.setup(self.CONF['dc'], GPIO.OUT)
        GPIO.setup(self.CONF['bl'], GPIO.OUT)
        
        # Turn on backlight
        self.backlight_pwm = GPIO.PWM(self.LED_PIN, 1000)
        self.backlight_pwm.start(100)

        # Initialize buttons
        GPIO.setup(self.BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        self.button_press_callback = None
        self.button_release_callback = None
        
        # Event detection for button
        GPIO.add_event_detect(
            self.BUTTON_PIN, GPIO.BOTH, callback=self._button_event, bouncetime=50
        )

        # Initialize SPI
        self.spi = spidev.SpiDev()
        self.spi.open(self.CONF['spi_bus'], self.CONF['spi_device'])
        self.spi.max_speed_hz = 40000000 # 40MHz
        self.spi.mode = 0b00

        self._reset_lcd()
        self._init_display()
        self.fill_screen(0)

    # ========== LCD Display Functions ==========

    # ========== Backlight Control ==========
    def set_backlight(self, brightness):
        if 0 <= brightness <= 100:
            self.backlight_pwm.ChangeDutyCycle(brightness)

    def _reset_lcd(self):
        GPIO.output(self.CONF['rst'], GPIO.HIGH)
        time.sleep(0.05)
        GPIO.output(self.CONF['rst'], GPIO.LOW)
        time.sleep(0.05)
        GPIO.output(self.CONF['rst'], GPIO.HIGH)
        time.sleep(0.05)

    def _init_display(self):
        self._send_command(0x11) # Sleep Out
        time.sleep(0.12)
        
        # Memory Data Access Control
        self._send_command(0x36, self.CONF['madctl']) 
        
        # Interface Pixel Format
        self._send_command(0x3A, 0x05) 
        
        self._send_command(0x21) # Display Inversion On
        self._send_command(0x29) # Display On

    def _send_command(self, cmd, *args):
        GPIO.output(self.CONF['dc'], GPIO.LOW)
        self.spi.xfer2([cmd])
        if args:
            GPIO.output(self.CONF['dc'], GPIO.HIGH)
            # Flatten args if necessary, but *args is already a tuple
            self._send_data(list(args))

    def _send_data(self, data):
        GPIO.output(self.CONF['dc'], GPIO.HIGH)
        # optimize for large data chunks
        max_chunk = 4096
        for i in range(0, len(data), max_chunk):
            self.spi.writebytes(data[i : i + max_chunk])


    def set_window(self, x0, y0, x1, y1):
        # ST7789 standard window setting
        # Handle potential offset if screen is not 240x320? 
        # For this 1.3" 240x240, it's usually centered or top-aligned.
        # waveshare_config says row_start=0, col_start=0 for 1.3"
        
        # Note: command 0x2A is Column Address Set
        # command 0x2B is Row Address Set
        
        self._send_command(0x2A, x0 >> 8, x0 & 0xFF, x1 >> 8, x1 & 0xFF)
        self._send_command(0x2B, y0 >> 8, y0 & 0xFF, y1 >> 8, y1 & 0xFF)
        self._send_command(0x2C) # RAM Write

    def draw_pixel(self, x, y, color):
        if x >= self.LCD_WIDTH or y >= self.LCD_HEIGHT:
            return
        self.set_window(x, y, x, y)
        self._send_data([(color >> 8) & 0xFF, color & 0xFF])

    def fill_screen(self, color):
        self.set_window(0, 0, self.LCD_WIDTH - 1, self.LCD_HEIGHT - 1)
        # Create a buffer line
        high = (color >> 8) & 0xFF
        low = color & 0xFF
        # Create a chunk of data (e.g., one line or more)
        chunk = [high, low] * self.LCD_WIDTH
        
        # Send repeated chunks
        # Total bytes = width * height * 2
        
        GPIO.output(self.CONF['dc'], GPIO.HIGH)
        # Much faster to reuse the same list object if possible or just loop writes
        # But constructing a huge list is memory intensive.
        # Let's write line by line
        for _ in range(self.LCD_HEIGHT):
            self.spi.writebytes(chunk)

    def draw_image(self, x, y, width, height, pixel_data):
        if (x + width > self.LCD_WIDTH) or (y + height > self.LCD_HEIGHT):
            # Crop logic or ignore? Let's just clip logic if possible, or error.
            # print("Warning: Image size exceeds screen bounds, might glitch.")
            pass
            
        self.set_window(x, y, x + width - 1, y + height - 1)
        self._send_data(pixel_data)

    # ========== RGB (Stubbed) ==========
    def set_rgb(self, r, g, b):
        # No RGB LED on this board
        pass

    def set_rgb_fade(self, r_target, g_target, b_target, duration_ms=100):
        # No RGB LED on this board
        pass

    # ========== Buttons ==========
    def button_pressed(self):
        return GPIO.input(self.BUTTON_PIN) == 0

    def on_button_press(self, callback):
        self.button_press_callback = callback

    def on_button_release(self, callback):
        self.button_release_callback = callback

    def _button_release_event(self, channel):
        if self.button_release_callback:
            self.button_release_callback()

    def _button_press_event(self, channel):
        if self.button_press_callback:
            self.button_press_callback()

    def _button_event(self, channel):
        if GPIO.input(channel) == 0:
            # Falling edge (button pressed, assuming pull-up)
            self._button_press_event(channel)
        else:
            # Rising edge (button released)
            self._button_release_event(channel)

    # ========== Cleanup ==========
    def cleanup(self):
        self.spi.close()
        self.backlight_pwm.stop()
        GPIO.cleanup()

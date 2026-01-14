import time
import sys
import spidev
import RPi.GPIO as GPIO
from PIL import Image, ImageDraw, ImageFont
from waveshare_config import CONFIGS

# Configuration GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

def send_cmd(spi, dc_pin, cmd):
    GPIO.output(dc_pin, GPIO.LOW)
    spi.writebytes([cmd])

def send_data(spi, dc_pin, data):
    GPIO.output(dc_pin, GPIO.HIGH)
    spi.writebytes(data)

def init_lcd(spi, conf):
    # Setup GPIOs non-SPI
    GPIO.setup(conf['rst'], GPIO.OUT)
    GPIO.setup(conf['dc'], GPIO.OUT)
    GPIO.setup(conf['bl'], GPIO.OUT)
    
    # Backlight ON
    GPIO.output(conf['bl'], GPIO.HIGH)
    
    # Reset
    GPIO.output(conf['rst'], GPIO.HIGH)
    time.sleep(0.01)
    GPIO.output(conf['rst'], GPIO.LOW)
    time.sleep(0.01)
    GPIO.output(conf['rst'], GPIO.HIGH)
    time.sleep(0.1)

    # Commandes communes d'initialisation
    send_cmd(spi, conf['dc'], 0x11) # Sleep out
    time.sleep(0.12)
    
    send_cmd(spi, conf['dc'], 0x3A) # COLMOD (Pixel Format)
    send_data(spi, conf['dc'], [0x05]) # 16-bit RGB565
    
    send_cmd(spi, conf['dc'], 0x36) # MADCTL
    
    # Configuration specifique selon l'ecran
    if "1.3" in conf['name']:
        # Retour a 0x60 qui etait "Parfait mais a l'envers" (Tete en bas).
        # On va corriger l'orientation par rotation logicielle de l'image.
        send_data(spi, conf['dc'], [0x60])
    else:
        # Les petits ecrans sont OK avec 0x70
        send_data(spi, conf['dc'], [0x70])
    
    send_cmd(spi, conf['dc'], 0x21) # Display Inversion ON
    send_cmd(spi, conf['dc'], 0x29) # Display ON

def display_image(spi, conf, image):
    width, height = image.size
    
    # Gestion specifique ST7735S (0.96") vs ST7789 (1.3")
    col_start = 0
    row_start = 0
    
    if "0.96" in conf['name']:
        # En mode Swap XY (0x70), la resolution logique est 160x80.
        # Le driver ST7735S (132x162) a souvent un offset sur l'axe court en mode paysage.
        # Ici l'axe court est Y (80px). 132 - 80 = 52 ? Ou offset standard 24 ?
        # Essayons row_start = 24 (offset standard souvent observe).
        col_start = 0
        row_start = 24
    
    # Définir la fenêtre d'écriture
    # CASET (Column Address Set)
    send_cmd(spi, conf['dc'], 0x2A)
    x_end = col_start + width - 1
    send_data(spi, conf['dc'], [col_start >> 8, col_start & 0xFF, x_end >> 8, x_end & 0xFF])
    
    # RASET (Row Address Set)
    send_cmd(spi, conf['dc'], 0x2B)
    y_end = row_start + height - 1
    send_data(spi, conf['dc'], [row_start >> 8, row_start & 0xFF, y_end >> 8, y_end & 0xFF])
    
    # RAMWR (Memory Write)
    send_cmd(spi, conf['dc'], 0x2C)
    
    GPIO.output(conf['dc'], GPIO.HIGH)
    
    # Conversion image -> RGB565 bytes
    pixels = list(image.getdata())
    data = []
    for r, g, b in pixels:
        val = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
        data.append(val >> 8)
        data.append(val & 0xFF)
        
    # Envoi par chunks
    chunk_size = 4096
    for i in range(0, len(data), chunk_size):
        spi.writebytes(data[i:i+chunk_size])


def create_bonjour_image(width, height):
    image = Image.new('RGB', (width, height), (0, 0, 0)) # Fond noir
    draw = ImageDraw.Draw(image)
    
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
    except:
        font = ImageFont.load_default()

    text = "BONJOUR"
    
    # Calcul pour centrer le texte
    # bbox retourne (left, top, right, bottom)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    
    x = (width - text_w) // 2
    y = (height - text_h) // 2
    
    # Couleur Cyan
    draw.text((x, y), text, font=font, fill=(0, 255, 255))
    
    # Petit cadre rouge pour délimiter
    draw.rectangle((0, 0, width-1, height-1), outline=(255, 0, 0))
    
    return image

print("=== TEST BONJOUR SUR 3 ÉCRANS (PORTRAIT) ===")

for conf in CONFIGS:
    print(f"Initialisation de : {conf['name']}...")
    
    spi = spidev.SpiDev()
    spi.open(conf['spi_bus'], conf['spi_device'])
    spi.max_speed_hz = 20000000 # 20MHz
    spi.mode = 0b00
    
    try:
        init_lcd(spi, conf)
        
        # Détermination de la taille en fonction de l'écran
        # 1.3" ST7789 : 240x240
        # 0.96" ST7735 : 80x160
        
        if "1.3" in conf['name']:
            w, h = 240, 240
        else:
            # Mode 0x70 (Paysage/Swap XY) -> 160x80
            w, h = 160, 80
            
        print(f"Creation image {w}x{h}...")
        img = create_bonjour_image(w, h)
        
        if "1.3" in conf['name']:
            print("Correction orientation 1.3' : Rotation 180 degres...")
            img = img.rotate(180)

        print("Envoi de l'image...")
        display_image(spi, conf, img)
        
    finally:
        spi.close()

print("\nTerminé. Le message BONJOUR devrait être affiché sur les 3 écrans.")
print("Attente de 15 secondes...")
time.sleep(15)
GPIO.cleanup()

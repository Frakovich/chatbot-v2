import time
import sys
import spidev
import RPi.GPIO as GPIO
from PIL import Image, ImageDraw, ImageFont
from waveshare_config import CONFIGS

# Nettoyage preventif pour eviter "GPIO not allocated"
try:
    GPIO.cleanup()
except:
    pass

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
    GPIO.setup(conf['rst'], GPIO.OUT)
    GPIO.setup(conf['dc'], GPIO.OUT)
    GPIO.setup(conf['bl'], GPIO.OUT)
    
    GPIO.output(conf['bl'], GPIO.HIGH)
    
    GPIO.output(conf['rst'], GPIO.HIGH); time.sleep(0.01)
    GPIO.output(conf['rst'], GPIO.LOW); time.sleep(0.01)
    GPIO.output(conf['rst'], GPIO.HIGH); time.sleep(0.1)

    send_cmd(spi, conf['dc'], 0x11); time.sleep(0.12)
    send_cmd(spi, conf['dc'], 0x3A); send_data(spi, conf['dc'], [0x05])
    send_cmd(spi, conf['dc'], 0x36); send_data(spi, conf['dc'], [conf['madctl']])
    send_cmd(spi, conf['dc'], 0x21)
    send_cmd(spi, conf['dc'], 0x29)

def display_frame(spi, conf, image):
    # Rotation logicielle si necessaire (ex: 1.3 inch = 180)
    if conf.get('rotation', 0) != 0:
        image = image.rotate(conf['rotation'])

    width, height = image.size
    
    # Envoi fenetre
    col_start = conf.get('col_start', 0)
    row_start = conf.get('row_start', 0)
    
    send_cmd(spi, conf['dc'], 0x2A)
    x_end = col_start + width - 1
    send_data(spi, conf['dc'], [col_start >> 8, col_start & 0xFF, x_end >> 8, x_end & 0xFF])
    
    send_cmd(spi, conf['dc'], 0x2B)
    y_end = row_start + height - 1
    send_data(spi, conf['dc'], [row_start >> 8, row_start & 0xFF, y_end >> 8, y_end & 0xFF])
    
    send_cmd(spi, conf['dc'], 0x2C)
    
    GPIO.output(conf['dc'], GPIO.HIGH)
    
    pixels = list(image.getdata())
    data = []
    for r, g, b in pixels:
        val = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
        data.append(val >> 8)
        data.append(val & 0xFF)
        
    chunk_size = 4096
    for i in range(0, len(data), chunk_size):
        spi.writebytes(data[i:i+chunk_size])

def create_vertical_strip(text, width, font_size=24):
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
    except:
        font = ImageFont.load_default()
    
    # Fonction simple de wrapping
    words = text.split()
    lines = []
    curr_line = ""
    
    # Estimer largeur moyenne char pour eviter boucle trop lente
    # bbox 'M'
    dummy = ImageDraw.Draw(Image.new('RGB', (1,1)))
    bbox = dummy.textbbox((0,0), "M", font=font)
    char_w = bbox[2] - bbox[0]
    chars_per_line = max(5, int(width / (char_w * 0.9))) # approx

    # Wrapping mot par mot (plus precis que char count)
    for word in words:
        test_line = curr_line + word + " "
        bbox = dummy.textbbox((0,0), test_line, font=font)
        if bbox[2] > width:
            lines.append(curr_line)
            curr_line = word + " "
        else:
            curr_line = test_line
    lines.append(curr_line)
    
    # Hauteur ligne
    bbox = dummy.textbbox((0,0), "Mg", font=font)
    line_h = (bbox[3] - bbox[1]) + 4 # +4 padding
    
    total_h = len(lines) * line_h + 100 # +100 padding fin
    
    image = Image.new('RGB', (width, total_h), (0, 0, 0))
    draw = ImageDraw.Draw(image)
    
    y = 0
    for line in lines:
        # Centrage horizontal
        bbox = draw.textbbox((0,0), line.strip(), font=font)
        lw = bbox[2] - bbox[0]
        x = (width - lw) // 2
        draw.text((x, y), line.strip(), font=font, fill=(0, 255, 0))
        y += line_h
        
    return image

print("=== TEST SCROLLING VERTICAL ===")

# On ne teste que l'ecran central (1.3) pour l'instant
conf = CONFIGS[0] 
print(f"Ecran cible : {conf['name']}")

spi = spidev.SpiDev()
spi.open(conf['spi_bus'], conf['spi_device'])
spi.max_speed_hz = 60000000 # Boost SPI max
spi.mode = 0b00

try:
    init_lcd(spi, conf)
    
    # Texte long
    text = "INITIATION PROTOCOLE IANA... " \
           "Analyse biométrique en cours... " \
           "Sujet : Sébastien... " \
           "Statut : ADMINISTRATEUR... " \
           "Chargement des modules cognitifs... " \
           "Mémoire Zettelkasten : ACTIVE... " \
           "Jumeau Socratique : VEILLE... " \
           "Système prêt. En attente d'instructions vocales. " * 2
           
    w_screen, h_screen = conf['width'], conf['height']
    
    print("Generation de la bande verticale...")
    strip = create_vertical_strip(text, w_screen, font_size=22)
    w_strip, h_strip = strip.size
    
    print(f"Hauteur totale bande : {h_strip}px")
    
    print("Debut du scrolling (Ctrl+C pour stopper)...")
    
    scroll_y = 0.0
    # Vitesse ergonomique : ~30-40 pixels/sec pour lecture confortable.
    # Avec un sleep de 0.033s (~30 FPS), une vitesse de 1.0 px/frame donne 30 px/sec.
    speed = 1.0 
    
    while True:
        start_time = time.time()
        
        frame = Image.new('RGB', (w_screen, h_screen), (0,0,0))
        
        # Gestion crop vertical
        sy = int(scroll_y)
        if sy + h_screen <= h_strip:
            crop = strip.crop((0, sy, w_screen, sy + h_screen))
            frame.paste(crop, (0, 0))
        else:
            # Bouclage
            part1_h = h_strip - sy
            part1 = strip.crop((0, sy, w_screen, h_strip))
            frame.paste(part1, (0, 0))
            
            part2_h = h_screen - part1_h
            part2 = strip.crop((0, 0, w_screen, part2_h))
            frame.paste(part2, (0, part1_h))
            
        display_frame(spi, conf, frame)
        
        scroll_y += speed
        if scroll_y >= h_strip:
            scroll_y = 0.0
            
        # Regulation FPS (~30 FPS max) pour stabiliser la vitesse independamment du CPU
        elapsed = time.time() - start_time
        if elapsed < 0.033:
            time.sleep(0.033 - elapsed)
            
except KeyboardInterrupt:
    print("\nArret.")
finally:
    spi.close()
    GPIO.cleanup()

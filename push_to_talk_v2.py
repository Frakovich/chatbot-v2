import time
import os
import threading
import RPi.GPIO as GPIO
import speech_recognition as sr
import pyaudio
import wave
import ollama
from PIL import Image, ImageDraw, ImageFont
import textwrap

# Import local drivers
from waveshare_config import LCD_1_3, LCD_0_96_1, LCD_0_96_2, KEYS
from display import ST7789

# --- CONFIGURATION ---
RECORD_PIN = KEYS['KEY2']
VALIDATE_PIN = KEYS['KEY1']
OLLAMA_MODEL = "llama3.2:latest"
TEMP_AUDIO_FILE = "/tmp/recording.wav"

# --- INIT HARDWARE ---
print("Initialisation des ecrans...")
LCD_1_3['rotation'] = 180
disp = ST7789(LCD_1_3)
disp_side1 = ST7789(LCD_0_96_1)
disp_side2 = ST7789(LCD_0_96_2)

GPIO.setmode(GPIO.BCM)
GPIO.setup(RECORD_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(VALIDATE_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# --- GLOBAL STATE ---
state = "IDLE"
user_text = ""
bot_text = "Pret. Maintenez K2 pour parler."
scroll_y = 0.0
bot_strip = None
running = True
lock = threading.Lock()

# --- FONTS ---
def get_font(size):
    try:
        # Chemin standard sur Raspberry Pi
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)
    except:
        return ImageFont.load_default()

font_ui = get_font(16)
font_text = get_font(14)
font_sm = get_font(12)
font_large = get_font(24)

# --- UI LOGIC ---
def create_bot_strip(text, width):
    # Wrapping plus large pour l'ecran central
    lines = textwrap.wrap(text, width=28)
    line_h = 18
    padding_top = 5
    padding_bottom = 60 # Espace pour respirer en fin de scroll
    
    total_h = len(lines) * line_h + padding_top + padding_bottom
    # On laisse un peu de marge sur les bords
    img = Image.new('RGB', (width - 10, max(total_h, 100)), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    y = padding_top
    for line in lines:
        draw.text((0, y), line, font=font_text, fill=(255, 255, 255))
        y += line_h
    return img

def update_bot_text(text):
    global bot_text, bot_strip, scroll_y
    with lock:
        bot_text = text
        bot_strip = create_bot_strip(text, disp.width)
        scroll_y = 0.0

def update_side_screens(current_state):
    texts = {
        "IDLE": "PRET",
        "RECORDING": "ECOUTE",
        "PROCESSING": "ANALYSE",
        "VALIDATE": "VALIDER",
        "THINKING": "PENSE..."
    }
    txt = texts.get(current_state, "IANA")
    
    img = Image.new('RGB', (disp_side1.width, disp_side1.height), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    bbox = draw.textbbox((0, 0), txt, font=font_large)
    w_text = bbox[2] - bbox[0]
    h_text = bbox[3] - bbox[1]
    x = (disp_side1.width - w_text) / 2
    y = (disp_side1.height - h_text) / 2
    draw.text((x, y), txt, font=font_large, fill=(255, 255, 255))
    
    disp_side1.display(img)
    disp_side2.display(img)

def display_thread_func():
    global scroll_y, running
    last_state = None
    
    update_bot_text(bot_text)
    
    while running:
        start_time = time.time()
        
        # Copie locale des etats pour eviter les locks longs
        with lock:
            curr_state = state
            curr_user = user_text
            curr_strip = bot_strip
            curr_scroll = scroll_y
        
        # Preparation de la frame
        img = Image.new('RGB', (disp.width, disp.height), (0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Barre de statut
        status_colors = {
            "IDLE": (0, 255, 0),
            "RECORDING": (255, 0, 0),
            "PROCESSING": (0, 0, 255),
            "VALIDATE": (255, 255, 0),
            "THINKING": (255, 165, 0)
        }
        color = status_colors.get(curr_state, (200, 200, 200))
        draw.rectangle([(0,0), (disp.width, 5)], fill=color)
        draw.text((5, 10), f"MODE: {curr_state}", font=font_ui, fill=(200, 200, 200))
        
        # Zone Texte Utilisateur
        draw.line([(0, 40), (disp.width, 40)], fill=(50, 50, 50))
        lines_user = textwrap.wrap(curr_user, width=28)
        uy = 45
        for line in lines_user[:3]:
            draw.text((5, uy), line, font=font_text, fill=(100, 255, 255))
            uy += 18

        # Aide Validation
        if curr_state == "VALIDATE":
            draw.rectangle([(0, 100), (disp.width, 120)], fill=(40, 40, 0))
            draw.text((10, 102), "K1: OUI | K2: NON", font=font_sm, fill=(255, 255, 0))
            
        # Zone Texte Bot (Scrolling)
        bot_area_y = 125
        draw.line([(0, bot_area_y), (disp.width, bot_area_y)], fill=(50, 50, 50))
        
        area_h = disp.height - bot_area_y - 5
        if curr_strip:
            sy = int(curr_scroll)
            # Si on depasse la fin, on boucle
            if sy >= curr_strip.height - area_h/2 and curr_strip.height > area_h:
                with lock: scroll_y = 0.0
                sy = 0
            
            # Crop de la bande
            crop_h = min(area_h, curr_strip.height - sy)
            if crop_h > 0:
                crop = curr_strip.crop((0, sy, disp.width - 10, sy + crop_h))
                img.paste(crop, (5, bot_area_y + 5))
            
            # Increment scroll si le texte est plus long que la zone
            if curr_strip.height > area_h + 10:
                with lock: scroll_y += 1.0 # Vitesse de scroll (pixels par frame)
        
        disp.display(img)
        
        # Mise a jour ecrans lateraux sur changement d'etat
        if curr_state != last_state:
            update_side_screens(curr_state)
            last_state = curr_state
            
        # Regulation FPS (~20 FPS)
        elapsed = time.time() - start_time
        if elapsed < 0.05:
            time.sleep(0.05 - elapsed)

# --- AUDIO LOGIC ---
def record_audio_hold():
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    
    p = pyaudio.PyAudio()
    try:
        stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    except:
        return False

    frames = []
    while GPIO.input(RECORD_PIN) == GPIO.LOW:
        data = stream.read(CHUNK, exception_on_overflow=False)
        frames.append(data)
    
    stream.stop_stream()
    stream.close()
    p.terminate()

    wf = wave.open(TEMP_AUDIO_FILE, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()
    return True

def transcribe_audio():
    recognizer = sr.Recognizer()
    with sr.AudioFile(TEMP_AUDIO_FILE) as source:
        audio_data = recognizer.record(source)
        try:
            return recognizer.recognize_google(audio_data, language="fr-FR")
        except:
            return None

# --- MAIN LOOP ---
def main():
    global state, user_text, running
    
    # Lancement du thread d'affichage
    t = threading.Thread(target=display_thread_func)
    t.daemon = True
    t.start()
    
    try:
        while True:
            # Attente K2 (Enregistrement)
            if GPIO.input(RECORD_PIN) == GPIO.LOW:
                with lock:
                    state = "RECORDING"
                    user_text = "..."
                
                if record_audio_hold():
                    with lock: state = "PROCESSING"
                    txt = transcribe_audio()
                    
                    if txt:
                        with lock:
                            user_text = txt
                            state = "VALIDATE"
                        
                        # Attente Validation (K1) ou Annulation (K2)
                        validated = False
                        while True:
                            if GPIO.input(VALIDATE_PIN) == GPIO.LOW:
                                validated = True
                                break
                            if GPIO.input(RECORD_PIN) == GPIO.LOW:
                                # Anti-rebond
                                while GPIO.input(RECORD_PIN) == GPIO.LOW: time.sleep(0.01)
                                break
                            time.sleep(0.05)
                        
                        if validated:
                            with lock: state = "THINKING"
                            try:
                                messages = [
                                    {'role': 'system', 'content': 'Tu es Iana, un assistant concis et efficace. Réponds en français.'},
                                    {'role': 'user', 'content': user_text}
                                ]
                                response = ollama.chat(model=OLLAMA_MODEL, messages=messages)
                                update_bot_text(response['message']['content'])
                            except Exception as e:
                                update_bot_text(f"Erreur Ollama: {e}")
                        else:
                            with lock: user_text = "(Annule)"
                    else:
                        with lock: user_text = "(Pas compris)"
                    
                    with lock: state = "IDLE"
                
                # Anti-rebond final
                while GPIO.input(RECORD_PIN) == GPIO.LOW: time.sleep(0.1)
            
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("Arret...")
        running = False
        t.join(1.0)
        GPIO.cleanup()
        disp.close()
        disp_side1.close()
        disp_side2.close()

if __name__ == "__main__":
    main()

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
STATIC_HOLD_SECONDS = 3.0
SCROLL_SPEED = 0.8

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
bot_text = "Bonjour. Je suis Iana."
scroll_y = 0.0
bot_strip = None
running = True
lock = threading.Lock()
last_bot_update_time = 0.0

# --- FONTS ---
def get_font(size):
    try:
        # Chemin standard sur Raspberry Pi
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)
    except:
        return ImageFont.load_default()

def wrap_text_pixel(text, font, width):
    """
    Wraps text based on pixel width, not character count.
    Returns a list of lines.
    """
    words = text.split()
    if not words:
        return []

    lines = []
    current_line = words[0]
    
    # We need a dummy drawable to measure text without creating a new image every time
    dummy_img = Image.new('RGB', (1, 1))
    dummy_draw = ImageDraw.Draw(dummy_img)

    for word in words[1:]:
        # Check width of the line with the new word
        test_line = f"{current_line} {word}"
        bbox = dummy_draw.textbbox((0, 0), test_line, font=font)
        w = bbox[2] - bbox[0]
        
        if w > width:
            # The new word makes the line too long, so save the current line
            lines.append(current_line)
            current_line = word
        else:
            # The new word fits, so add it to the current line
            current_line = test_line
    
    # Add the last remaining line
    lines.append(current_line)
    return lines

font_ui = get_font(16)
font_text = get_font(16)
font_sm = get_font(12)
font_large = get_font(24)

# --- UI LOGIC ---
def create_bot_strip(text, width, height, font):
    """
    Creates an image strip for the main display.
    Returns a static image if text fits, or a long scrolling strip if it doesn't.
    """
    # Use a 10px margin for the text
    lines = wrap_text_pixel(text, font, width - 10)
    
    # Get realistic line height
    line_h = font.getbbox("Mg")[3] - font.getbbox("Mg")[1] + 4
    total_h = len(lines) * line_h

    # --- CONDITIONAL LOGIC ---
    if total_h <= height:
        # Text fits, create a static, centered image
        img = Image.new('RGB', (width, height), (0, 0, 0))
        draw = ImageDraw.Draw(img)
        y = (height - total_h) / 2 # Center the whole block
        for line in lines:
            draw.text((5, y), line, font=font, fill=(255, 255, 255))
            y += line_h
        return img
    else:
        # Text overflows, create a long scrolling strip
        # Add padding at the bottom so the last line can scroll to the top
        strip_h = total_h + height - line_h
        img = Image.new('RGB', (width, strip_h), (0, 0, 0))
        draw = ImageDraw.Draw(img)
        y = 5 # Small top padding
        for line in lines:
            draw.text((5, y), line, font=font, fill=(255, 255, 255))
            y += line_h
        return img

def update_bot_text(text):
    global bot_text, bot_strip, scroll_y, last_bot_update_time
    with lock:
        bot_text = text
        # Pass dimensions and font to the strip creator
        bot_strip = create_bot_strip(text, disp.width, disp.height, font_text)
        scroll_y = 0.0
        last_bot_update_time = time.time()

def update_side_screens(text_left, text_right):
    # Font for side screens - smaller
    font = get_font(18)
    
    # --- Process left screen ---
    img1 = Image.new('RGB', (disp_side1.width, disp_side1.height), (0, 0, 0))
    draw1 = ImageDraw.Draw(img1)
    
    # Use the new reliable wrapper with a small margin
    lines1 = wrap_text_pixel(text_left, font, disp_side1.width - 10)
    
    # Calculate total height to center the text block
    line_h = (font.getbbox("Mg")[3] - font.getbbox("Mg")[1]) + 2 # Get real line height
    total_h = len(lines1) * line_h
    y1 = (disp_side1.height - total_h) / 2
    
    for line in lines1:
        bbox = draw1.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        x = (disp_side1.width - w) / 2 # Center each line horizontally
        draw1.text((x, y1), line, font=font, fill=(255, 255, 255))
        y1 += line_h
    disp_side1.display(img1)

    # --- Process right screen (same logic) ---
    img2 = Image.new('RGB', (disp_side2.width, disp_side2.height), (0, 0, 0))
    draw2 = ImageDraw.Draw(img2)
    lines2 = wrap_text_pixel(text_right, font, disp_side2.width - 10)
    
    total_h_2 = len(lines2) * line_h
    y2 = (disp_side2.height - total_h_2) / 2
    
    for line in lines2:
        bbox = draw2.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        x = (disp_side2.width - w) / 2
        draw2.text((x, y2), line, font=font, fill=(255, 255, 255))
        y2 += line_h
    disp_side2.display(img2)

def display_thread_func():
    global scroll_y, running, last_bot_update_time
    
    # On fait le premier rendu du message d'accueil
    update_bot_text(bot_text)
    
    while running:
        start_time = time.time()
        
        with lock:
            curr_state = state
            curr_user = user_text
            curr_strip = bot_strip
            curr_scroll = scroll_y
            last_update = last_bot_update_time
        
        img = Image.new('RGB', (disp.width, disp.height), (0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        if curr_state == "VALIDATE":
            # --- LAYOUT VALIDATION ---
            # Utilise le nouveau wrapper pour le texte utilisateur
            lines_user = wrap_text_pixel(curr_user, font_text, disp.width - 20)
            
            line_h = font_text.getbbox("Mg")[3] - font_text.getbbox("Mg")[1] + 4
            total_h = len(lines_user) * line_h
            
            # Centre le bloc de texte verticalement, un peu vers le haut
            uy = (disp.height - total_h) / 2 - 20
            
            for line in lines_user:
                bbox = draw.textbbox((0, 0), line, font=font_text)
                w = bbox[2] - bbox[0]
                # Centre chaque ligne horizontalement
                draw.text(((disp.width - w) / 2, uy), line, font=font_text, fill=(100, 255, 255))
                uy += line_h

            # Aide pour la validation en bas
            help_text = "K1: Valider | K2: Annuler"
            bbox = draw.textbbox((0, 0), help_text, font=font_ui)
            w = bbox[2] - bbox[0]
            draw.text(((disp.width - w) / 2, disp.height - 30), help_text, font=font_ui, fill=(255, 255, 0))

        elif curr_strip:
            # --- DYNAMIC DISPLAY LOGIC (STATIC OR SCROLL) ---
            is_scrolling = curr_strip.height > disp.height

            if not is_scrolling:
                # It's a static image, just paste it
                img.paste(curr_strip, (0, 0))
            else:
                # It's a scrolling strip
                area_h = disp.height
                sy = int(curr_scroll)

                # If we've scrolled to the end, pause and then loop back
                if sy >= curr_strip.height - area_h:
                    time.sleep(1.5)  # Pause at the end before looping
                    with lock:
                        scroll_y = 0.0
                        # Reset the timer to enforce the static hold again on loop
                        last_bot_update_time = time.time()
                    sy = 0  # Use 0 for this frame's render

                crop = curr_strip.crop((0, sy, disp.width, sy + area_h))
                img.paste(crop, (0, 0))

                # Increment scroll position only after the hold time has passed
                if time.time() - last_update > STATIC_HOLD_SECONDS:
                    with lock:
                        scroll_y += SCROLL_SPEED

        disp.display(img)
            
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

    # Etat initial des ecrans lateraux
    update_side_screens("Maintenez K2 pour parler", "IDLE")
    
    try:
        while True:
            # Attente K2 (Enregistrement)
            if GPIO.input(RECORD_PIN) == GPIO.LOW:
                # On nettoie l'ecran central et on change l'etat
                update_bot_text("") 
                with lock: state = "RECORDING"
                update_side_screens("Enregistrement...", "RECORDING")
                
                if record_audio_hold():
                    with lock: state = "PROCESSING"
                    update_side_screens("Transcription...", "PROCESSING")
                    txt = transcribe_audio()
                    
                    if txt:
                        with lock:
                            user_text = txt
                            state = "VALIDATE"
                        update_side_screens("Validez votre texte", "VALIDATE")
                        
                        validated = False
                        # Boucle de validation
                        while state == "VALIDATE":
                            if GPIO.input(VALIDATE_PIN) == GPIO.LOW:
                                validated = True
                                break
                            if GPIO.input(RECORD_PIN) == GPIO.LOW:
                                while GPIO.input(RECORD_PIN) == GPIO.LOW: time.sleep(0.01)
                                break
                            time.sleep(0.05)
                        
                        if validated:
                            prompt_for_api = ""
                            with lock:
                                state = "THINKING"
                                prompt_for_api = user_text
                                user_text = "" # Efface pour l'ecran central
                            update_side_screens("Iana réfléchit...", "THINKING")
                            
                            try:
                                messages = [
                                    {'role': 'system', 'content': 'Tu es Iana, un assistant concis et efficace. Réponds en français.'},
                                    {'role': 'user', 'content': prompt_for_api}
                                ]
                                response = ollama.chat(model=OLLAMA_MODEL, messages=messages)
                                update_bot_text(response['message']['content'])
                            except Exception as e:
                                update_bot_text(f"Erreur Ollama: {e}")
                        else: # Annulation
                             with lock: user_text = "" # Clear le texte de validation
                    else: # Pas de transcription
                        update_bot_text("(Je n'ai pas compris)") # Affiche l'erreur au centre
                    
                    # Retour a l'etat initial
                    with lock: state = "IDLE"
                    update_side_screens("Maintenez K2 pour parler", "IDLE")

                # Anti-rebond
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

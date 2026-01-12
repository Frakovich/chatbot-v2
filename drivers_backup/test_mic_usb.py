import sounddevice as sd
import numpy as np
import time
from scipy.io.wavfile import write

# Configuration
DEVICE_INDEX = 2  # USB Microphone
SAMPLE_RATE = 16000 # ou 44100 ou 48000 selon le micro
CHANNELS = 1
DURATION = 5  # secondes
OUTPUT_FILE = "test_mic.wav"

def test_microphone():
    print("=== TEST MICROPHONE USB ===")
    
    # 1. Lister et trouver le périphérique USB
    print("\nRecherche du microphone USB...")
    devices = sd.query_devices()
    usb_device_index = None
    
    for i, dev in enumerate(devices):
        print(f"Index {i}: {dev['name']} (In: {dev['max_input_channels']}, Out: {dev['max_output_channels']})")
        # On cherche un device avec 'USB' dans le nom et au moins 1 canal d'entrée
        if 'USB' in dev['name'] and dev['max_input_channels'] > 0:
            usb_device_index = i
    
    if usb_device_index is not None:
        print(f"\n[✅] Microphone USB trouvé à l'index : {usb_device_index}")
        device_to_use = usb_device_index
    else:
        print("\n[⚠️] Microphone USB non trouvé spécifiquement. Essai avec le périphérique par défaut.")
        device_to_use = None # Laissera sounddevice choisir le defaut
        
    rates_to_try = [48000, 44100, 16000]
    
    for rate in rates_to_try:
        try:
            print(f"\n[🎤] Essai enregistrement à {rate} Hz (Device Index: {device_to_use})...")
            audio = sd.rec(int(DURATION * rate), samplerate=rate, channels=CHANNELS, device=device_to_use, dtype='int16')
            sd.wait()
            print("[⏹] Enregistrement terminé.")
            
            # Vérification
            max_val = np.max(np.abs(audio))
            print(f"Niveau Max (Amplitude): {max_val} / 32767")
            
            if max_val == 0:
                print("[⚠️] ATTENTION : Le signal est vide (silence total). Vérifiez le volume (alsamixer).")
            else:
                print("[✅] Signal détecté.")
                
            write(OUTPUT_FILE, rate, audio)
            print(f"Fichier sauvegardé : {OUTPUT_FILE}")
            return # Succès, on quitte
            
        except Exception as e:
            print(f"[❌] Echec à {rate} Hz : {e}")
            
    print("\n[!!!] Impossible d'enregistrer avec les fréquences standards.")

    print("\n--- Note ---")
    print("Pour visualiser le volume en temps réel (VU-mètre) dans le terminal, utilisez :")
    print("arecord -D hw:2,0 -c 1 -f S16_LE -V mono /dev/null")

if __name__ == "__main__":
    test_microphone()

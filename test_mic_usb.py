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
        # On cherche spécifiquement le matériel détecté par le système (PCM2902 ou USB PnP)
        dev_name = dev['name'].lower()
        if ('usb pnp' in dev_name or 'pcm2902' in dev_name) and dev['max_input_channels'] > 0:
            usb_device_index = i
            break # On a trouvé le bon !
        # Repli sur une recherche 'usb' générique si le nom précis n'est pas trouvé
        elif 'usb' in dev_name and dev['max_input_channels'] > 0 and usb_device_index is None:
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
            
            # --- Ajout du VU-mètre visuel ---
            recorded_frames = []

            def callback(indata, frames, time, status):
                if status:
                    print(status)
                recorded_frames.append(indata.copy())
                
                # Calcul du niveau pour le VU-mètre (RMS plus robuste)
                # On convertit en float pour éviter les overflows sur les entiers courts
                data_float = indata.astype(np.float32)
                rms = np.sqrt(np.mean(data_float**2))
                
                if np.isnan(rms):
                    rms = 0
                
                # Normalisation sur une échelle de 0 à 100 (basé sur 16-bit ~32768)
                # On divise par ~300 au lieu de multiplier pour avoir une échelle cohérente
                level = (rms / 32768.0) * 100
                
                bar_length = int(level * 2) # Facteur visuel
                if bar_length > 50: bar_length = 50
                bar = "#" * bar_length
                print(f"\rVolume: [{bar:<50}] {int(rms)}", end="", flush=True)

            with sd.InputStream(samplerate=rate, channels=CHANNELS, device=device_to_use, dtype='int16', callback=callback):
                time.sleep(DURATION)
            
            print("\n[⏹] Enregistrement terminé.")
            
            # Reconstitution du signal complet
            audio = np.concatenate(recorded_frames, axis=0)
            # ---------------------------------

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

import time
import spidev
import RPi.GPIO as GPIO
from waveshare_config import CONFIGS

def turn_off_all():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    for conf in CONFIGS:
        try:
            print(f"Eteindre {conf['name']}...")
            
            # Init minimum pour contrôler le rétroéclairage
            GPIO.setup(conf['bl'], GPIO.OUT)
            GPIO.output(conf['bl'], GPIO.LOW) # Eteindre le backlight
            
            # Optionnel : Envoyer du noir si le backlight ne suffit pas ou fuit
            # Mais sans init LCD complet, ça ne marchera pas. 
            # Le backlight LOW est le plus efficace et rapide.
            
        except Exception as e:
            print(f"Erreur sur {conf['name']}: {e}")

    GPIO.cleanup()
    print("Tous les ecrans devraient etre eteints.")

if __name__ == "__main__":
    turn_off_all()

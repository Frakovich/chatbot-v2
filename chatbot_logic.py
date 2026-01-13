import socket
import json
import time
import threading
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import requests
import speech_recognition as sr
import pyttsx3
import os

# Configuration
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2"
UI_HOST = '127.0.0.1'
UI_PORT = 12345

# Audio Config
SAMPLE_RATE = 16000 # 16kHz is good for Whisper/SpeechRecognition
CHANNELS = 1
AUDIO_FILE = "input_command.wav"

class ChatbotLogic:
    def __init__(self):
        self.sock = None
        self.connect_ui()
        self.is_recording = False
        
        # Init TTS
        self.tts_engine = pyttsx3.init()
        # You might need to adjust voice/rate here
        self.tts_engine.setProperty('rate', 150)
        
        # Init STT
        self.recognizer = sr.Recognizer()

    def connect_ui(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((UI_HOST, UI_PORT))
            print("Connected to UI Server")
            self.send_ui({"text": "System Ready", "emoji": "✅", "status": "Idle"})
        except Exception as e:
            print(f"Could not connect to UI: {e}")
            time.sleep(2)
            self.connect_ui()

    def send_ui(self, data):
        if self.sock:
            try:
                msg = json.dumps(data) + "\n"
                self.sock.sendall(msg.encode('utf-8'))
            except BrokenPipeError:
                print("UI Disconnected")
                self.connect_ui()

    def record_audio(self, duration=5):
        print("Recording...")
        # Use sounddevice to record
        audio_data = sd.rec(int(duration * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=CHANNELS, dtype='int16')
        sd.wait()
        print("Recording finished")
        wav.write(AUDIO_FILE, SAMPLE_RATE, audio_data)

    def transcribe_audio(self):
        with sr.AudioFile(AUDIO_FILE) as source:
            audio = self.recognizer.record(source)
        try:
            # Using Google Web Speech API for simplicity (Online)
            # For offline, you'd use self.recognizer.recognize_whisper(audio) but it requires setup
            text = self.recognizer.recognize_google(audio, language="fr-FR") 
            return text
        except sr.UnknownValueError:
            return None
        except sr.RequestError as e:
            print(f"STT Error: {e}")
            return None

    def query_ollama(self, prompt):
        try:
            payload = {
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False
            }
            response = requests.post(OLLAMA_URL, json=payload)
            response.raise_for_status()
            return response.json()['response']
        except Exception as e:
            print(f"Ollama Error: {e}")
            return "Désolé, je ne peux pas réfléchir maintenant."

    def speak(self, text):
        self.tts_engine.say(text)
        self.tts_engine.runAndWait()

    def process_interaction(self):
        # 1. Update UI
        self.send_ui({"status": "Listening...", "emoji": "👂", "text": "..."})
        
        # 2. Record
        self.record_audio(duration=5) # Fixed duration for now
        
        # 3. Transcribe
        self.send_ui({"status": "Thinking...", "emoji": "🤔"})
        user_text = self.transcribe_audio()
        
        if not user_text:
            self.send_ui({"status": "Error", "emoji": "😕", "text": "Je n'ai rien entendu."})
            self.speak("Je n'ai pas compris.")
            return

        self.send_ui({"text": f"Moi: {user_text}"})
        
        # 4. AI Generation
        ai_response = self.query_ollama(user_text)
        
        # 5. Output
        self.send_ui({"status": "Speaking", "emoji": "🗣️", "text": ai_response})
        self.speak(ai_response)
        
        # 6. Reset
        self.send_ui({"status": "Idle", "emoji": "🙂"})

    def listen_loop(self):
        buffer = ""
        while True:
            try:
                data = self.sock.recv(4096).decode('utf-8')
                if not data:
                    break
                buffer += data
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if not line.strip(): continue
                    
                    try:
                        event_data = json.loads(line)
                        if event_data.get("event") == "button_pressed":
                            print("Button Pressed Event Received")
                            # Run interaction in a separate thread to not block socket listener
                            threading.Thread(target=self.process_interaction).start()
                            
                    except json.JSONDecodeError:
                        pass
            except Exception as e:
                print(f"Socket Error: {e}")
                self.connect_ui()

if __name__ == "__main__":
    bot = ChatbotLogic()
    bot.listen_loop()

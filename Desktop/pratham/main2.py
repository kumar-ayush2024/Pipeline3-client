import speech_recognition as sr
from pvrecorder import PvRecorder
from playsound3 import playsound
import wave
import struct
import requests
import cv2
import os
import uuid  # <--- NEW: Required for generating Session ID

# --- CONFIGURATION ---
FLASK_API_URL = "http://127.0.0.1:5003/checkSST"
FLASK_API_URLWI = "http://127.0.0.1:5003/checkWImage"

# --- MEMORY SETUP ---
# Generate a unique ID for this run of the app
SESSION_ID = str(uuid.uuid4())
print(f"Session ID: {SESSION_ID}")

# Global variable to store the current language session
# 'en' = English, 'hi' = Hindi, 'pa' = Punjabi
CURRENT_LANG = 'en' 
language_code = 'en-IN'

def recordSound():
    """ Records audio and sends to server with the CURRENT_LANG """
    print(f"🎤 Recording 6 seconds in ({CURRENT_LANG})...")
    
    recorder = PvRecorder(device_index=-1, frame_length=512)
    recorder.start()

    frames = []
    for _ in range(int(16000 / 512 * 6)):  # 6 seconds at 16kHz
        pcm = recorder.read()
        frames.extend(pcm)

    recorder.stop()
    recorder.delete()

    with wave.open("recording.wav", "wb") as f:
        f.setnchannels(1)            # mono
        f.setsampwidth(2)            # 16-bit PCM
        f.setframerate(16000)        # 16kHz sample rate
        f.writeframes(struct.pack("<" + "h" * len(frames), *frames))

    playsound("wait.wav")

    # SEND TO SERVER with 'lang' parameter
    try:
        with open("recording.wav", "rb") as audio_file:
            files = {"file": ("recording.wav", audio_file, "audio/wav")}
            
            # --- MEMORY CHANGE: Send Session ID ---
            data = {
                "lang": language_code,
                "session_id": SESSION_ID  # <--- Identifying the user session
            }
            
            response = requests.post(FLASK_API_URL, files=files, data=data, timeout=1000)

        if response.status_code == 200:
            wav_path = "response.mp3"
            with open(wav_path, 'wb') as f:
                f.write(response.content)
            playsound(wav_path)
            try:
                os.remove(wav_path)
                os.remove("recording.wav")
            except:
                pass
            print("DONE")
        else:
            print(f"Server Error: {response.status_code}")
    except Exception as e:
        print(f"Connection Error: {e}")

def captureImage():
    """ Captures image + audio and sends to server with CURRENT_LANG """
    print("📸 Capturing Image...")
    cam = cv2.VideoCapture(0)
    if not cam.isOpened():
        print("Could not open webcam")
        return

    ret, frame = cam.read()
    if not ret:
        print("Failed to capture image")
        return

    filename = "inputimg.jpg"
    cv2.imwrite(filename, frame)
    cam.release()
    print(f"Image saved.")
    
    # Record Audio Context
    print(f"🎤 Recording Context ({CURRENT_LANG})...")
    recorder = PvRecorder(device_index=-1, frame_length=512)
    recorder.start()

    frames = []
    for _ in range(int(16000 / 512 * 6)):
        pcm = recorder.read()
        frames.extend(pcm)

    recorder.stop()
    recorder.delete()

    with wave.open("recording.wav", "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(16000)
        f.writeframes(struct.pack("<" + "h" * len(frames), *frames))

    playsound("wait.wav")

    try:
        with open("recording.wav", "rb") as audio_file, open("inputimg.jpg", "rb") as image_file:
            files = {
                "audio": ("recording.wav", audio_file, "audio/wav"),
                "image": ("inputimg.jpg", image_file, "image/jpeg")
            }
            
            # --- MEMORY CHANGE: Send Session ID ---
            data = {
                "lang": language_code, 
                "session_id": SESSION_ID # <--- Identifying the user session
            }
            
            response = requests.post(FLASK_API_URLWI, files=files, data=data, timeout=1000)

        if response.status_code == 200:
            wav_path = "response.mp3"
            with open(wav_path, 'wb') as f:
                f.write(response.content)
            playsound(wav_path)
            try:
                os.remove(wav_path)
                os.remove("recording.wav")
                os.remove("inputimg.jpg")
            except:
                pass
            print("DONE")
        else:
            print("No response from server")
    except Exception as e:
        print(f"Error: {e}")

def takeUserInput():
    """ Listening for commands in the SELECTED language """
    print(f"--- Listening for commands in {CURRENT_LANG} ---")
    
    while True:
        r = sr.Recognizer()
        with sr.Microphone() as source:
            r.adjust_for_ambient_noise(source, duration=0.5)
            print("Listening for command...")
            
            try:
                audio = r.listen(source, timeout=4, phrase_time_limit=4)
            except sr.WaitTimeoutError:
                continue

        try:
            print("Processing...")
            query = r.recognize_google(audio, language=language_code).lower()
            print(f"You Said ({CURRENT_LANG}): {query}")

            # --- MULTILINGUAL COMMAND MATCHING ---
            
            ask_triggers = [
                "ask something", "i want to ask",       
                "kuch pucho", "kuch poocho","कुछ पूछो",
                "kujh pucho", "kujh puchna","kuchh poochho","kuchh poochhoo","kuch poochhoo","kuch poochoo"
            ]
            
            image_triggers = [
                "capture image", "take photo",          
                "photo kheecho", "photo khicho",        
                "photo khich", "tasveer khich"          
            ]

            stop_triggers = ["stop", "exit", "ruk jao", "band karo"]

            if any(x in query for x in ask_triggers):
                print("Cmd: Ask Something")
                playsound('startRecording.wav')
                recordSound()

            elif any(x in query for x in image_triggers):
                print("Cmd: Capture Image")
                playsound('startRecording.wav')
                captureImage()

            elif any(x in query for x in stop_triggers):
                print("Returning to Wake Word Mode...")
                return 

        except Exception as e:
            # print(e) 
            pass

def startLens():
    """ 
    Wake Word Listener. 
    It listens in 'Mixed' mode to detect if user wants English, Hindi, or Punjabi.
    """
    # --- NECESSARY CHANGE: GLOBAL SCOPE ---
    # We must make language_code global so takeUserInput sees the update
    global CURRENT_LANG, language_code 
    
    print("\n--- WAITING FOR WAKE WORD ---")
    
    r = sr.Recognizer()
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source, duration=1)
        print("Say: 'Hello Lens', 'Namaste Lens', or 'Sat Sri Akal Lens'")
        try:
            audio = r.listen(source, timeout=None, phrase_time_limit=5)
        except:
            return "None"

    try:
        query = r.recognize_google(audio, language='en-in').lower()
        print(f"Wake Check: {query}")

        # --- ENGLISH WAKE WORD ---
        if "hello lens" in query or "lens" in query:
            print("Wake: English Detected")
            CURRENT_LANG = 'en'
            language_code = 'en-IN'
            playsound('wake.wav')
            takeUserInput()

        # --- HINDI WAKE WORD ---
        elif "namaste" in query or "namaskar" in query:
            print("Wake: Hindi Detected")
            CURRENT_LANG = 'en-in'
            language_code = 'hi-IN'

            playsound('wake.wav')
            takeUserInput()

        # --- PUNJABI WAKE WORD ---
        elif "sat shri akaal" in query or "sasriakal" in query:
            print("Wake: Punjabi Detected")
            CURRENT_LANG = 'en-in'
            language_code = 'pa-IN'
            playsound('wake.wav')
            takeUserInput()
            
    except Exception as e:
        pass
    return "None"

if __name__ == "__main__":
    print("System Starting...")
    playsound('startup.mp3')
    
    while True:
        startLens()
import pyttsx3
import speech_recognition
from pvrecorder import PvRecorder
from playsound3 import playsound
import wave
import struct
import requests
import cv2

FLASK_API_URL="http://127.0.0.1:5000/checkSST"

def recordSound():
    recorder = PvRecorder(device_index=-1, frame_length=512)
    recorder.start()
    print("🎤 Recording 6 seconds...")

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

    with open("recording.wav", "rb") as audio_file, open("inputimg.jpg", "rb") as image_file:
        files = {
            "audio": ("recording.wav", audio_file, "audio/wav"),
            "image": ("inputimg.jpg", image_file, "image/jpeg")
        }
        response = requests.post(FLASK_API_URL, files=files, timeout=1000)


    if response.status_code == 200:
        wav_path = "response.mp3"
        with open(wav_path, 'wb') as f:
            f.write(response.content)
        playsound(wav_path)
        try:
            os.remove(wav_path)
            os.remove("recording.wav")
        except Exception as e:
            print("Failed to delete audio files")
        print("DONE")






def captureImage():
    #Capture Image
    cam = cv2.VideoCapture(0)
    if not cam.isOpened():
        raise Exception("Could not open webcam")
    # Capture one frame
    ret, frame = cam.read()
    if not ret:
        raise Exception("Failed to capture image")
    # Save with timestamp
    filename = "inputimg.jpg"
    cv2.imwrite(filename, frame)
    print(f"Image saved as {filename}")
    # Release the camera
    cam.release()
    
    #Record Audio
    recorder = PvRecorder(device_index=-1, frame_length=512)
    recorder.start()
    print("🎤 Recording 6 seconds...")

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

    with open("recording.wav", "rb") as f:
        files = {"file": ("recording.wav", f, "audio/wav")}
        response = requests.post(FLASK_API_URL, files=files, timeout=1000)

    if response.status_code == 200:
        wav_path = "response.mp3"
        with open(wav_path, 'wb') as f:
            f.write(response.content)
        playsound(wav_path)
        try:
            os.remove(wav_path)
            os.remove("recording.wav")
        except Exception as e:
            print("Failed to delete audio files")
        print("DONE")
















def takeUserInput():
    print("In user input")
    while True:
        r = speech_recognition.Recognizer()
        with speech_recognition.Microphone() as source:
            print("Listening.....")
            r.pause_threshold = 1
            r.energy_threshold = 300
            audio = r.listen(source,0,4)
        try:
            
            print("Understanding..")
            query  = r.recognize_google(audio,language='en-in')
            print(f"You Said: {query}\n")
            if query=="ask something" or query=="I want to ask something" or query=="I want to ask":
                print("Please Ask...")
                playsound('startRecording.wav')
                playsound('three.wav')
                playsound('two.wav')
                playsound('one.wav')
                playsound('go.wav')
                recordSound()
            if query=="capture image":
                captureImage()
        except Exception as e:
            print("Say that again")

def startLens():
    print("Lens Startup")
    r = speech_recognition.Recognizer()
    with speech_recognition.Microphone() as source:
        print("Listening.....")
        r.pause_threshold = 1
        r.energy_threshold = 300
        audio = r.listen(source,0,4)
    try:
        print("Understanding..")
        query  = r.recognize_google(audio,language='en-in')
        print(f"You Said: {query}\n")
        if query=="Lens"or query=="hello lens":
            print("System Turning On...")
            playsound('wake.wav')
            takeUserInput()
    except Exception as e:
        print("Say that again")
        return "None"
    return query

if __name__ == "__main__":
    # recordSound()
    while True:
        query = startLens()
        if query=="stop":
            break
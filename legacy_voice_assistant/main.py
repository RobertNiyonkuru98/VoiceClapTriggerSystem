import pyaudio
import numpy as np
import time
import speech_recognition as sr
import pyttsx3
from actions import launch_study, launch_coding, launch_gaming, launch_social, handle_advanced_command
from config import THRESHOLD, WAKE_WORD

engine = pyttsx3.init()

def speak(text):
    engine.say(text)
    engine.runAndWait()

def count_claps(seconds=5):
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)

    print(f"DEBUG: Listening for claps now...")
    claps = 0
    last_clap_time = 0
    start_time = time.time()

    while time.time() - start_time < seconds:
        data = np.frombuffer(stream.read(1024), dtype=np.int16)
        peak = np.average(np.abs(data))

        if peak > 500:
            print(f"Volume detected: {int(peak)}")

        if peak > THRESHOLD:
            if time.time() - last_clap_time > 0.25:
                claps += 1
                print(f">>> CLAP {claps} REGISTERED! <<<")
                last_clap_time = time.time()

    stream.stop_stream()
    stream.close()
    p.terminate()
    return claps

def main():
    r = sr.Recognizer()
    r.energy_threshold = 300

    with sr.Microphone() as source:
        print(f"System Active. Waiting for '{WAKE_WORD}'...")
        while True:
            try:
                audio = r.listen(source, timeout=None, phrase_time_limit=4)
                voice_input = r.recognize_google(audio).lower()

                if WAKE_WORD in voice_input:
                    speak("Yes Boss!")

                    claps = count_claps(4)

                    if claps > 0:
                        print("Waiting for modifier (3 secods)...")
                        try:
                            cmd_audio = r.listen(source, timeout=2, phrase_time_limit=2)
                            modifier = r.recognize_google(cmd_audio).lower()
                        except:
                            modifier= ""
                        # print(f"Command received: {modifier}")

                        handle_advanced_command(claps, modifier)

            except Exception:
                continue

if __name__ == "__main__":
    main()
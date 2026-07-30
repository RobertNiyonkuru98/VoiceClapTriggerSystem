import subprocess
import pygetwindow as gw
import time
import os
import webbrowser
from config import BRAVE_PATH, STUDY_URLS, SOCIAL_URLS

def launch_study():
    print("Mode: Study")
    for url in STUDY_URLS:
        subprocess.Popen([BRAVE_PATH, url])

def launch_coding():
    print("Mode: Coding")
    subprocess.Popen(["code"], shell=True) # Opens VS Code
    subprocess.Popen(["notepad.exe"])      # Opens Notepad

def launch_gaming():
    print("Mode: Gaming - Clearing RAM")
    os.system("taskkill /f /im brave.exe")
    os.system("taskkill /f /im Code.exe")
    # Add Steam path here if needed: os.startfile("steam://open/main")

def launch_social(app_name):
    print(f"Opening {app_name}")
    url = SOCIAL_URLS.get(app_name)
    if url:
        subprocess.Popen([BRAVE_PATH, f"--app={url}"])

def open_pwa(url):
    subprocess.Popen([BRAVE_PATH, f"--app={url}"])

def snap_windows_coding():
    subprocess.Popen(["code"], shell=True)
    subprocess.Popen(["notepad.exe"])

    time.sleep(2)

    try:
        vscode = gw.getWindowsWithTitle("Visual Studio Code")[0]
        notes = gw.getWindowsWithTitle("Notepad")[0]

        vscode.restore()
        vscode.moveTo(0,0)
        vscode.resizeTo(960, 1080)

        notes.restore()
        notes.moveTo(960,0)
        notes.resizeTo(960, 1080)
    except:
        print("Could not find windows to snap.")


def handle_advanced_command(claps, word=""):
    print(f"Executing: {claps} claps with word: '{word}'")

    if claps == 1:
        if "social" in word:
            open_pwa("https://www.instagram.com")
        elif "music" in word:
            os.system("start spotify")
        elif "movie" in word:
            open_pwa("https://www.moviebox.ph")
        else:
            launch_study()

    elif claps == 2:
        if "peace" in word:
            os.system("start chatgpt://")
            # os.system("start claude://")
        elif "study" in word:
            launch_study()
        else:
            snap_windows_coding()

    elif claps == 3:
        print("System Shutdown Mode...")
        os.system("taskkill /IM brave.exe /T")
        os.system("taskkill /f /im Code.exe")
        os.startfile("start steam://open/main")
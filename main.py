import os
import subprocess
import pygame
import speech_recognition as sr
import datetime
import webbrowser
import wikipedia
import ctypes
import pyautogui   # <-- NEW: Screen capturing
import sys         # <-- NEW: Output capturing for local code
from io import StringIO
from PIL import Image
from dotenv import load_dotenv
from google import genai
from google.genai import types

# --- 1. SETUP NEPTUNE'S NEURAL VOICE (MOUTH) ---
pygame.mixer.init()

def speak(text):
    print(f"Neptune: {text}\n")
    try:
        subprocess.run(
            ["edge-tts", "--voice", "hi-IN-SwaraNeural", "--rate", "+15%", "--text", text, "--write-media", "response.mp3"], 
            check=True, capture_output=True
        )
        pygame.mixer.music.load("response.mp3")
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        pygame.mixer.music.unload()
        if os.path.exists("response.mp3"):
            os.remove("response.mp3")
    except Exception as e:
        print(f"(Audio failed to play: {e})")

# --- 2. SETUP NEPTUNE'S EARS (MICROPHONE) ---
def listen():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening for wake word 'Neptune'...")
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            return recognizer.recognize_google(audio)
        except:
            return ""

# --- 3. SETUP NEPTUNE'S BRAIN & TOOLS (AGENT) ---
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

MEMORY_FILE = "neptune_memory.txt"

def load_memory() -> str:
    if not os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            f.write("- The user's name is Vaibhav.\n")
            f.write("- The user operates an ASUS laptop.\n")
            f.write("- The user studies Python and data science.\n")
            f.write("- The user builds dashboards using Power BI and Tableau.\n")
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        return f.read()

def memorize_fact(fact: str) -> str:
    print(f"\n[SYSTEM LOG: Neptune committed to memory: {fact}]")
    with open(MEMORY_FILE, "a", encoding="utf-8") as f:
        f.write(f"- {fact}\n")
    return f"Successfully remembered: {fact}"

def get_current_time() -> str:
    print("\n[SYSTEM LOG: Neptune accessed the system clock]")
    return datetime.datetime.now().strftime("%A, %B %d, %Y %I:%M %p")

def open_application(target: str) -> str:
    """Opens applications, websites, or specific files. DO NOT use this tool to lock the screen."""
    print(f"\n[SYSTEM LOG: Neptune attempting to open {target}]")
    target = target.lower().strip()
    app_registry = {
        "youtube": "https://www.youtube.com",
        "google": "https://www.google.com",
        "notepad": "notepad",
        "calculator": "calc",
        "power bi": "PBIDesktop",
        "excel": "excel",
        "word": "winword",
        "tableau": "tableau",
    }
    try:
        if target in app_registry:
            command = app_registry[target]
            if command.startswith("http"):
                webbrowser.open(command)
            else:
                os.system(f'start "" "{command}"')
            return f"Successfully opened {target}."
        else:
            os.system(f'start "" "{target}"')
            return f"Asked Windows to open {target}."
    except Exception as e:
        return f"Failed to open {target}. Error: {e}"

def search_wikipedia(query: str) -> str:
    print(f"\n[SYSTEM LOG: Neptune querying the web for '{query}']")
    try:
        return f"Web Search Result: {wikipedia.summary(query, sentences=2)}"
    except Exception as e:
        return f"Could not find exact information. Error: {e}"

def control_system(action: str) -> str:
    print(f"\n[SYSTEM LOG: Neptune executing system command: {action}]")
    if "lock" in action.lower():
        ctypes.windll.user32.LockWorkStation()
        return "Screen locked successfully."
    return f"Action '{action}' is not supported."

# NEW: The Vision Upgrade
def analyze_screen(query: str) -> str:
    """Takes a live screenshot of the computer and analyzes it based on the user's query."""
    print("\n[SYSTEM LOG: Neptune is looking at the screen]")
    try:
        screenshot = pyautogui.screenshot()
        screenshot.save("vision_cache.png")
        
        # Internal Gemini call to analyze the image
        vision_response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=[f"Look at this screenshot and answer: {query}", Image.open("vision_cache.png")]
        )
        return f"Screen Analysis: {vision_response.text}"
    except Exception as e:
        return f"Failed to analyze screen. Error: {e}"

# NEW: The Data Analyst Upgrade
def execute_python(code: str) -> str:
    """Executes Python code locally. Use this to do math, analyze CSVs with pandas, or manipulate data. You must use print() to output the results."""
    print("\n[SYSTEM LOG: Neptune is executing local Python code]")
    
    # Reroute standard output to capture her print statements
    old_stdout = sys.stdout
    redirected_output = sys.stdout = StringIO()
    
    try:
        exec(code)
        sys.stdout = old_stdout
        output = redirected_output.getvalue()
        return f"Execution Output:\n{output}"
    except Exception as e:
        sys.stdout = old_stdout
        return f"Execution Error: {e}"

base_instruction = (
    "You are Neptune, an advanced, highly capable AI assistant inspired by J.A.R.V.I.S. "
    "You are fluent in English, Hindi, and Marathi. You must reply in the exact language the user speaks to you. "
    "Keep spoken answers concise and clear. Refer to yourself as Neptune. "
    "Do NOT use markdown formatting like asterisks (**bold**) because your responses are being read aloud.\n\n"
    "Here is your permanent memory file regarding the user. Use this context naturally:\n"
)
system_instruction = base_instruction + load_memory()

chat = client.chats.create(
    model="gemini-3.6-flash",
    config=types.GenerateContentConfig(
        system_instruction=system_instruction,
        temperature=0.7,
        # ALL 7 TOOLS EQUIPPED
        tools=[get_current_time, open_application, memorize_fact, search_wikipedia, control_system, analyze_screen, execute_python], 
    )
)

speak("Systems online. Vision and Data Analytics protocols loaded. I am listening.")

# --- 4. CONTINUOUS VOICE LOOP ---
while True:
    user_voice_input = listen()
    if not user_voice_input:
        continue
        
    user_text = user_voice_input.lower()
    
    if "neptune" in user_text:
        print(f"\nYou: {user_voice_input}")
        
        if any(word in user_text for word in ["exit", "quit", "shutdown", "stop listening"]):
            speak("Shutting down systems. Goodbye.")
            break
            
        print("Neptune: Thinking...\r", end="")
        
        try:
            response = chat.send_message(user_voice_input)
            speak(response.text)
        except Exception as e:
            error_msg = str(e)
            if "503" in error_msg:
                speak("Sir, the AI servers are currently congested. Please try asking again in a moment.")
            else:
                speak("Apologies, my systems encountered an unexpected error.")
                print(f"(Error details: {error_msg})")
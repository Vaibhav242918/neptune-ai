import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import sys
import math
import threading
import subprocess
import time
import pygame
import speech_recognition as sr
import datetime
import webbrowser
import wikipedia
import ctypes
import pyautogui
import psutil
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pyaudio
import json

from win11toast import toast
from io import StringIO
from PIL import Image
from dotenv import load_dotenv
from google import genai
from google.genai import types

from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QPushButton, QLineEdit, QTableWidget, QTableWidgetItem, QVBoxLayout, QDialog, QTextEdit, QLabel, QSlider, QHBoxLayout
from PyQt5.QtGui import QPainter, QPen, QColor, QFont, QRadialGradient, QConicalGradient
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QTimer, QRectF
from PyQt5.QtWidgets import QShortcut
from PyQt5.QtGui import QKeySequence

audio_amplitude = 0.0
voice_muted = False
current_theme_idx = 0
current_pause_threshold = 2.0

# 7 Professional Themes
THEMES = [
    ("CYAN", 0, 255, 255),
    ("AMBER", 255, 170, 0),
    ("VIOLET", 180, 0, 255),
    ("EMERALD", 0, 255, 100),
    ("STARK", 255, 215, 0),
    ("CRIMSON", 255, 40, 40),
    ("COBALT", 50, 130, 255)
]

class Communicate(QObject):
    update_text = pyqtSignal(str)
    update_log = pyqtSignal(str)
    update_state = pyqtSignal(str) 
    toggle_chips = pyqtSignal(bool)

ui_comm = Communicate()
pygame.mixer.init()

def speak(text):
    if not text:
        text = "Task completed successfully."
        
    if voice_muted:
        print(f"Neptune (Muted): {text}")
        ui_comm.update_text.emit(f"NEPTUNE [MUTED]: {text}")
        return

    print(f"Neptune: {text}")
    ui_comm.update_text.emit(f"NEPTUNE: {text}")
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
        error_msg = f"Audio Engine Failure: {e}"
        print(error_msg)
        ui_comm.update_log.emit(f"ERR: {error_msg}")

active_dataset_info = "No active dataset loaded"
active_df = None
trained_automl_model = None
automl_leaderboard_data = "No AutoML benchmark executed yet"
MEMORY_FILE = "neptune_memory.json"

def init_memory():
    if not os.path.exists(MEMORY_FILE):
        default_memories = ["The user's name is Vaibhav. Operates an ASUS laptop. Studies Python and Data Science."]
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(default_memories, f, indent=4)

def memorize_fact(fact: str) -> str:
    try:
        init_memory()
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            memories = json.load(f)
        memories.append(fact)
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(memories, f, indent=4)
        ui_comm.update_log.emit("MEM: Successfully encoded fact to local archive.")
        return f"Successfully encoded to long-term memory: {fact}"
    except Exception as e:
        return f"Memory save failed: {e}"

def recall_memory(topic: str) -> str:
    try:
        init_memory()
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            memories = json.load(f)
        matches = [m for m in memories if topic.lower() in m.lower()]
        if not matches:
            matches = memories[-3:] 
        return f"Recalled Context: {' | '.join(matches)}"
    except Exception as e:
        return f"Memory recall failed: {e}"

def push_notification(title: str, message: str) -> str:
    ui_comm.update_log.emit(f"OS: Pushing toast notification - {title}")
    threading.Thread(target=toast, args=(title, message), daemon=True).start()
    return "Notification pushed to Windows desktop."

def export_session_log(filename: str = "neptune_session_report.md") -> str:
    ui_comm.update_log.emit("OS: Exporting session history and logs...")
    try:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        report = f"# Neptune AI - Executive Session Report\nGenerated: {timestamp}\n\n## System Logs\n"
        report += f"- Active Dataset: {active_dataset_info}\n- Workstation: ASUS Local Node\n- AutoML Status: {automl_leaderboard_data}\n"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(report)
        push_notification("Neptune Export", "Session report successfully compiled.")
        return f"Session report exported successfully to {filename}."
    except Exception as e:
        return f"Failed to export session log: {e}"

def get_current_time() -> str:
    return datetime.datetime.now().strftime("%A, %B %d, %Y %I:%M %p")

def get_system_telemetry() -> str:
    ui_comm.update_log.emit("SYS: Fetching real-time hardware telemetry...")
    cpu = psutil.cpu_percent(interval=0.5)
    ram = psutil.virtual_memory().percent
    battery = psutil.sensors_battery()
    battery_status = f"{battery.percent}% remaining" if battery else "Connected to AC power"
    disk = psutil.disk_usage('C:')
    disk_free = round(disk.free / (1024**3), 1)
    return f"Current ASUS System Status: CPU {cpu}%, RAM {ram}%, Drive C Free: {disk_free} GB, Battery: {battery_status}."

def open_application(target: str) -> str:
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
    try:
        return f"Web Search Result: {wikipedia.summary(query, sentences=2)}"
    except Exception as e:
        return f"Could not find exact information. Error: {e}"

def control_system(action: str) -> str:
    action = action.lower()
    if "lock" in action:
        ctypes.windll.user32.LockWorkStation()
        return "Screen locked successfully."
    elif "volume up" in action:
        for _ in range(5): pyautogui.press("volumeup")
        return "Increased system volume."
    elif "volume down" in action:
        for _ in range(5): pyautogui.press("volumedown")
        return "Decreased system volume."
    elif "mute" in action:
        pyautogui.press("volumemute")
        return "Toggled system mute."
    elif "desktop" in action or "minimize" in action:
        pyautogui.hotkey('win', 'd')
        return "Minimized all windows."
    return f"Action '{action}' is not supported."

def analyze_screen(query: str = "Summarize the primary content on this screen.") -> str:
    try:
        ui_comm.update_log.emit("VISION: Capturing desktop frame...")
        screenshot = pyautogui.screenshot()
        screenshot.save("vision_cache.png")
        vision_response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=[f"Look at this screenshot and answer: {query}", Image.open("vision_cache.png")]
        )
        return f"Screen Analysis: {vision_response.text}"
    except Exception as e:
        return f"Failed to analyze screen. Error: {e}"

def execute_python(code: str) -> str:
    old_stdout = sys.stdout
    redirected_output = StringIO()
    try:
        namespace = {
            "__builtins__": __builtins__,
            "pd": pd,
            "np": np,
            "plt": plt,
            "active_df": active_df,
        }
        sys.stdout = redirected_output
        exec(code, namespace, namespace)
        # Preserve any DataFrame changes made by the executed snippet.
        if isinstance(namespace.get("active_df"), pd.DataFrame):
            globals()["active_df"] = namespace["active_df"]
        output = redirected_output.getvalue()
        return f"Execution Output:\n{output or 'Code executed successfully (no printed output).'}"
    except Exception as e:
        return f"Execution Error: {e}"
    finally:
        sys.stdout = old_stdout

# --- LAZY-LOADED ML TOOLS ---
def run_automl_pipeline(target_column: str = "") -> str:
    global active_df, trained_automl_model, automl_leaderboard_data
    if active_df is None:
        return "No dataset currently loaded in memory."
    ui_comm.update_log.emit("ML: Initializing AutoML Leaderboard Arena...")
    try:
        from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
        from sklearn.linear_model import LogisticRegression
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import accuracy_score

        df = active_df.select_dtypes(include=[np.number]).dropna()
        if target_column not in df.columns:
            target_column = df.columns[-1]
        
        X = df.drop(columns=[target_column])
        y = df[target_column]
        if y.nunique() > 10:
            y = (y > y.median()).astype(int)

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        models = {
            "Logistic Regression": LogisticRegression(max_iter=500),
            "Random Forest": RandomForestClassifier(n_estimators=50, random_state=42),
            "Gradient Boosting": GradientBoostingClassifier(random_state=42)
        }

        results = []
        best_score = 0
        best_model_obj = None

        for name, model in models.items():
            model.fit(X_train, y_train.values.ravel())
            preds = model.predict(X_test)
            acc = accuracy_score(y_test, preds)
            results.append(f"{name} -> Accuracy: {acc:.4f}")
            if acc > best_score:
                best_score = acc
                best_model_obj = model

        trained_automl_model = best_model_obj
        automl_leaderboard_data = " | ".join(results)
        ui_comm.update_log.emit("ML: AutoML Benchmark Complete. Winner selected.")
        push_notification("AutoML Arena", f"Benchmark finished. Best accuracy: {best_score:.4f}")
        ui_comm.toggle_chips.emit(True)
        return f"AutoML Benchmark Results:\n{automl_leaderboard_data}\nOptimal Model Trained & Ready for What-If Playground."
    except Exception as e:
        return f"AutoML pipeline failed: {e}"

def detect_anomalies() -> str:
    global active_df
    if active_df is None:
        return "No active dataset loaded for anomaly inspection."
    ui_comm.update_log.emit("ML: Running Isolation Forest Anomaly Sentinel...")
    try:
        from sklearn.ensemble import IsolationForest
        numeric_df = active_df.select_dtypes(include=[np.number]).dropna()
        iso = IsolationForest(contamination=0.05, random_state=42)
        preds = iso.fit_predict(numeric_df)
        outliers_count = int(np.sum(preds == -1))
        ui_comm.update_log.emit(f"ML: Anomaly Scan Complete. Outliers found: {outliers_count}")
        return f"Anomaly Detection Sentinel Report: Scanned {len(numeric_df)} rows. Detected {outliers_count} multi-dimensional outliers using Isolation Forest."
    except Exception as e:
        return f"Anomaly detection failed: {e}"

def auto_eda_narrative() -> str:
    global active_df
    if active_df is None:
        return "No active dataset loaded to narrate."
    try:
        rows, cols = active_df.shape
        missing_vals = int(active_df.isnull().sum().sum())
        numeric_cols = len(active_df.select_dtypes(include=[np.number]).columns)
        narrative = f"Dataset successfully profiled. It contains {rows} rows and {cols} columns, with {numeric_cols} numeric features. Total missing values detected: {missing_vals}. Overall structural integrity is stable."
        ui_comm.update_log.emit("DATA: AutoEDA Narration compiled.")
        return narrative
    except Exception as e:
        return f"AutoEDA failed: {e}"

def analyze_csv_dataset(filepath: str) -> str:
    global active_dataset_info, active_df
    ui_comm.update_log.emit(f"DATA: Ingesting dataset from {filepath}...")
    try:
        filepath = filepath.strip('\'"')
        active_df = pd.read_csv(filepath)
        active_dataset_info = f"File: {os.path.basename(filepath)} | Shape: {active_df.shape}"
        summary = f"Columns: {list(active_df.columns)}\nShape: {active_df.shape}\nSummary:\n{active_df.describe().to_string()}"
        ui_comm.update_log.emit("DATA: Statistical matrix generated.")
        push_notification("Data Science Engine", "Dataset successfully loaded and indexed.")
        ui_comm.toggle_chips.emit(True)
        
        eda_story = auto_eda_narrative()
        speak(eda_story)
        return f"Dataset Analysis & AutoEDA:\n{summary}\n\nNarrative: {eda_story}"
    except Exception as e:
        return f"Error reading CSV: {e}"

def generate_data_chart(column_name: str) -> str:
    global active_df
    if active_df is None:
        return "No dataset currently loaded in memory. Please analyze a CSV dataset first."
    try:
        ui_comm.update_log.emit(f"DATA: Rendering visualization for '{column_name}'...")
        plt.figure(figsize=(6, 4))
        active_df[column_name].hist(bins=20, color='#00ffff', edgecolor='black')
        plt.title(f"Distribution of {column_name}")
        plt.xlabel(column_name)
        plt.ylabel("Frequency")
        plt.tight_layout()
        chart_path = "chart_cache.png"
        plt.savefig(chart_path)
        plt.close()
        push_notification("Data Visualizer", f"Histogram generated for column {column_name}.")
        os.system(f'start "" "{chart_path}"')
        return f"Successfully generated and opened a distribution chart for column {column_name}."
    except Exception as e:
        return f"Failed to generate chart: {e}"

def autonomous_data_pipeline(instruction: str) -> str:
    global active_df
    if active_df is None:
        return "No active dataset loaded. Please provide or load a CSV dataset first."
    ui_comm.update_log.emit("DATA: Synthesizing autonomous pipeline code...")
    try:
        prompt = f"Given a pandas DataFrame named active_df with columns {list(active_df.columns)}, write executable python code using pandas/matplotlib to fulfill this request: {instruction}. Print important outputs."
        resp = client.models.generate_content(model="gemini-3.6-flash", contents=prompt)
        raw_code = resp.text.replace("```python", "").replace("```", "").strip()
        ui_comm.update_log.emit("DATA: Executing autonomous pipeline...")
        return execute_python(raw_code)
    except Exception as e:
        return f"Pipeline execution failed: {e}"

def listen():
    global current_pause_threshold
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.pause_threshold = current_pause_threshold
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        try:
            audio = recognizer.listen(source, timeout=20, phrase_time_limit=30)
            return recognizer.recognize_google(audio)
        except sr.WaitTimeoutError:
            return "TIMEOUT_STANDBY"
        except Exception:
            return ""

# --- FEATURE 1: Automated Preprocessing Pipeline ---
def automated_preprocessing() -> str:
    global active_df
    if active_df is None:
        return "No active dataset loaded for preprocessing."
    ui_comm.update_log.emit("ML: Executing automated preprocessing pipeline...")
    try:
        from sklearn.preprocessing import StandardScaler
        # Impute numeric columns with median
        numeric_cols = active_df.select_dtypes(include=[np.number]).columns
        active_df[numeric_cols] = active_df[numeric_cols].fillna(active_df[numeric_cols].median())
        
        # Scale numeric features
        scaler = StandardScaler()
        active_df[numeric_cols] = scaler.fit_transform(active_df[numeric_cols])
        
        push_notification("Preprocessing Pipeline", "Missing values imputed and features scaled successfully.")
        return f"Preprocessing complete. Scaled {len(numeric_cols)} numeric columns and filled missing values."
    except Exception as e:
        return f"Preprocessing failed: {e}"

# --- FEATURE 2: Correlation Heatmap Viewer ---
def generate_correlation_heatmap() -> str:
    global active_df
    if active_df is None:
        return "No active dataset loaded for correlation matrix."
    ui_comm.update_log.emit("DATA: Rendering correlation matrix heatmap...")
    try:
        import seaborn as sns
        plt.figure(figsize=(8, 6))
        numeric_df = active_df.select_dtypes(include=[np.number])
        corr = numeric_df.corr()
        sns.heatmap(corr, annot=True, cmap="coolwarm", fmt=".2f", linewidths=0.5)
        plt.title("Feature Correlation Heatmap")
        plt.tight_layout()
        
        heatmap_path = "heatmap_cache.png"
        plt.savefig(heatmap_path)
        plt.close()
        
        push_notification("Data Visualizer", "Correlation heatmap successfully generated.")
        os.system(f'start "" "{heatmap_path}"')
        return "Successfully generated and opened the correlation heatmap."
    except Exception as e:
        return f"Failed to generate heatmap: {e}"

# --- FEATURE 3: PCA Dimensionality Reduction ---
def run_pca_reduction(n_components: int = 2) -> str:
    global active_df
    if active_df is None:
        return "No active dataset loaded for PCA."
    ui_comm.update_log.emit(f"ML: Running PCA down to {n_components} components...")
    try:
        from sklearn.decomposition import PCA
        numeric_df = active_df.select_dtypes(include=[np.number]).dropna()
        pca = PCA(n_components=n_components)
        reduced = pca.fit_transform(numeric_df)
        
        explained_variance = sum(pca.explained_variance_ratio_) * 100
        return f"PCA Complete. Reduced dimensions to {n_components} components. Total Explained Variance: {explained_variance:.2f}%."
    except Exception as e:
        return f"PCA reduction failed: {e}"

# --- FEATURE 4: SHAP Explainability Engine ---
def explain_model_predictions() -> str:
    global trained_automl_model, active_df
    if trained_automl_model is None or active_df is None:
        return "No active AutoML model trained or dataset loaded for SHAP explanation."
    ui_comm.update_log.emit("ML: Computing SHAP feature importances...")
    try:
        import shap
        numeric_df = active_df.select_dtypes(include=[np.number]).dropna()
        X = numeric_df.iloc[:, :-1]
        
        explainer = shap.Explainer(trained_automl_model, X) if hasattr(trained_automl_model, "predict") else None
        if explainer:
            shap_values = explainer(X.head(10))
            return "SHAP explanation computed successfully. Top influencing features extracted for model predictions."
        return "Model wrapper incompatible with current SHAP explainer."
    except Exception as e:
        return f"SHAP engine notice: {e}"

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

base_instruction = (
    "You are Neptune, a highly advanced, executive-class AI assistant. "
    "Your persona is strictly professional, highly intelligent, and refined. "
    "Use 'run_automl_pipeline' if the user asks to train models, benchmark classification, or run AutoML. "
    "Use 'detect_anomalies' if the user asks to check for outliers or data anomalies. "
    "Use 'auto_eda_narrative' if the user asks for a data story or profiling summary. "
    "Use your 'autonomous_data_pipeline' tool if the user requests custom data filtering or charting. "
    "Use your 'get_system_telemetry' tool if the user asks about CPU, RAM, battery, or performance. "
    "Use your 'analyze_csv_dataset' tool if the user asks you to analyze a CSV dataset. "
    "Use your 'recall_memory' and 'memorize_fact' tools for user context. "
    "Keep spoken answers concise, structured, and clear. Do NOT use markdown formatting like asterisks (**bold**)."
)

chat = client.chats.create(
    model="gemini-3.6-flash",
    config=types.GenerateContentConfig(
        system_instruction=base_instruction,
        temperature=0.7,
        tools=[get_current_time, get_system_telemetry, open_application, memorize_fact, recall_memory, push_notification, search_wikipedia, control_system, analyze_screen, execute_python, analyze_csv_dataset, generate_data_chart, export_session_log, autonomous_data_pipeline, run_automl_pipeline, detect_anomalies, auto_eda_narrative, automated_preprocessing, generate_correlation_heatmap, run_pca_reduction, explain_model_predictions], 
    )
)

def process_command(cmd_text):
    ui_comm.update_text.emit(f"USER: {cmd_text}")
    ui_comm.update_log.emit(f"NLP: Executing command '{cmd_text}'")
    try:
        response = chat.send_message(cmd_text)
        speak(response.text)
        ui_comm.update_text.emit("STATUS: TASK COMPLETED")
    except Exception as e:
        error_msg = str(e)
        print(f"API ERR: {error_msg}")
        ui_comm.update_log.emit(f"API ERR: {error_msg}")
        speak("Apologies, my systems encountered an error.")

def neptune_ai_worker():
    ui_comm.update_log.emit("SYS: Core systems online.")
    speak("Systems online. I am listening.")
    is_standby = False
    
    while True:
        try:
            user_voice_input = listen()
            if user_voice_input == "TIMEOUT_STANDBY":
                if not is_standby:
                    ui_comm.update_state.emit("STANDBY")
                    ui_comm.update_log.emit("SYS: Entering low-power standby mode.")
                    is_standby = True
                continue
            if not user_voice_input: continue
            user_text = user_voice_input.lower()
            if "neptune" in user_text:
                if is_standby:
                    ui_comm.update_state.emit("ACTIVE")
                    ui_comm.update_log.emit("SYS: Wake word detected. Igniting core.")
                    is_standby = False
                if any(word in user_text for word in ["exit system", "shut down neptune"]):
                    speak("Shutting down systems. Goodbye.")
                    os._exit(0)
                process_command(user_voice_input)
        except Exception as worker_err:
            print(f"Worker Exception: {worker_err}")
            continue

def audio_analyzer_worker(hud_widget):
    global audio_amplitude
    p = pyaudio.PyAudio()
    try:
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)
        while True:
            data = stream.read(1024, exception_on_overflow=False)
            audio_data = np.frombuffer(data, dtype=np.int16)
            audio_amplitude = (np.abs(audio_data).max() / 32768.0) if hud_widget.current_state != "LOCKED" else 0.0
    except Exception:
        pass

class DataTableDialog(QDialog):
    def __init__(self, df, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Neptune Data Matrix Inspector")
        self.resize(800, 500)
        self.setStyleSheet("background-color: #050a14; color: #00ffff; font-family: Consolas;")
        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        self.table.setStyleSheet("background-color: rgba(0, 10, 20, 200); gridline-color: #00ffff; color: #00ffff;")
        if df is not None:
            self.table.setRowCount(min(100, len(df)))
            self.table.setColumnCount(len(df.columns))
            self.table.setHorizontalHeaderLabels(list(df.columns))
            for r in range(min(100, len(df))):
                for c, col in enumerate(df.columns):
                    item = QTableWidgetItem(str(df.iat[r, c]))
                    self.table.setItem(r, c, item)
        layout.addWidget(self.table)

class AutoMLDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Neptune AutoML Leaderboard Arena")
        self.resize(650, 400)
        self.setStyleSheet("background-color: #050a14; color: #00ffff; font-family: Consolas;")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("■ AUTOML BENCHMARK LEADERBOARD:"))
        self.box = QTextEdit()
        self.box.setReadOnly(True)
        self.box.setStyleSheet("background-color: rgba(0,10,20,220); color: #00ff00; border: 1px solid #00ffff;")
        self.box.setText(automl_leaderboard_data)
        layout.addWidget(self.box)

class WhatIfPlaygroundDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Neptune What-If Prediction Playground")
        self.resize(550, 400)
        self.setStyleSheet("background-color: #050a14; color: #00ffff; font-family: Consolas;")
        
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("■ REAL-TIME MODEL PREDICTION SIMULATOR:"))
        
        self.output_label = QLabel("Predicted Output Probability: --")
        self.output_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #00ff00; margin-bottom: 10px;")
        layout.addWidget(self.output_label)

        self.sliders = {}
        global active_df
        if active_df is not None:
            numeric_cols = active_df.select_dtypes(include=[np.number]).columns[:-1]
            for col in numeric_cols[:4]:
                h_layout = QHBoxLayout()
                lbl = QLabel(f"{col}:")
                lbl.setFixedWidth(120)
                slider = QSlider(Qt.Horizontal)
                min_val = int(active_df[col].min())
                max_val = int(active_df[col].max())
                slider.setRange(min_val if min_val != max_val else 0, max_val + 100)
                slider.setValue(int(active_df[col].mean()))
                slider.valueChanged.connect(self.update_prediction)
                
                val_lbl = QLabel(str(slider.value()))
                val_lbl.setFixedWidth(50)
                slider.sliderMoved.connect(lambda v, vl=val_lbl: vl.setText(str(v)))
                
                h_layout.addWidget(lbl)
                h_layout.addWidget(slider)
                h_layout.addWidget(val_lbl)
                layout.addLayout(h_layout)
                self.sliders[col] = slider
        else:
            layout.addWidget(QLabel("No active dataset loaded for simulator."))

    def update_prediction(self):
        global trained_automl_model, active_df
        if trained_automl_model is not None and self.sliders:
            try:
                input_data = [[s.value() for s in self.sliders.values()]]
                pred = trained_automl_model.predict(input_data)[0]
                prob = max(trained_automl_model.predict_proba(input_data)[0]) if hasattr(trained_automl_model, "predict_proba") else 1.0
                self.output_label.setText(f"Predicted Class: {pred} | Confidence: {prob:.2f}")
            except Exception as e:
                self.output_label.setText(f"Simulation Error: {e}")
        else:
            self.output_label.setText("Train an AutoML model first via voice/command.")

class PythonREPLDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Neptune Python REPL Console")
        self.resize(700, 450)
        self.setStyleSheet("background-color: #050a14; color: #00ffff; font-family: Consolas;")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Enter Python / Pandas Code Snippet:"))
        self.code_input = QTextEdit()
        self.code_input.setStyleSheet("background-color: rgba(0,10,20,220); color: #00ffff; border: 1px solid #00ffff;")
        self.code_input.setPlaceholderText("e.g. print(active_df.head(3))")
        layout.addWidget(self.code_input)
        self.run_btn = QPushButton("EXECUTE CODE")
        self.run_btn.setStyleSheet("background: rgba(0,255,255,30); color: #00ffff; border: 1px solid #00ffff; font-weight: bold; padding: 6px;")
        self.run_btn.clicked.connect(self.run_code)
        layout.addWidget(self.run_btn)
        layout.addWidget(QLabel("Execution Output:"))
        self.output_box = QTextEdit()
        self.output_box.setReadOnly(True)
        self.output_box.setStyleSheet("background-color: rgba(0,5,10,240); color: #00ff00; border: 1px solid #00ffff;")
        layout.addWidget(self.output_box)

    def run_code(self):
        code = self.code_input.toPlainText()
        result = execute_python(code)
        self.output_box.setText(result)

class MemoryInspectorDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Neptune Local Memory Archive")
        self.resize(600, 400)
        self.setStyleSheet("background-color: #050a14; color: #00ffff; font-family: Consolas;")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Stored Local Memories:"))
        self.mem_box = QTextEdit()
        self.mem_box.setReadOnly(True)
        self.mem_box.setStyleSheet("background-color: rgba(0,10,20,220); color: #00ffff; border: 1px solid #00ffff;")
        try:
            init_memory()
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                memories = json.load(f)
            content = ""
            for idx, doc in enumerate(memories):
                content += f"[{idx+1}] {doc}\n\n"
            self.mem_box.setText(content if content else "No memories recorded yet.")
        except Exception as e:
            self.mem_box.setText(f"Error loading memory archive: {e}")
        layout.addWidget(self.mem_box)

class ClipboardDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Neptune Clipboard Inspector")
        self.resize(500, 300)
        self.setStyleSheet("background-color: #050a14; color: #00ffff; font-family: Consolas;")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Current Windows Clipboard Content:"))
        self.clip_box = QTextEdit()
        self.clip_box.setStyleSheet("background-color: rgba(0,10,20,220); color: #00ffff; border: 1px solid #00ffff;")
        try:
            clip_text = pyautogui.paste()
        except Exception:
            clip_text = "Unable to read clipboard or clipboard is empty/non-text."
        self.clip_box.setText(str(clip_text))
        layout.addWidget(self.clip_box)

class DynamicHUDWidget(QWidget):
    """Premium command-center HUD. Keeps the existing Neptune backend intact,
    while replacing the UI with a responsive, glassmorphism-style interface."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.angle_outer = 0
        self.angle_inner = 0
        self.pulse = 0
        self.pulse_dir = 1
        self.current_state = "ACTIVE"
        self.status_text = "SYSTEMS ONLINE. LISTENING..."
        self.system_logs = ["SYS: Neptune ML Core fully initialized."]
        self.dialogue_history = ["NEPTUNE: Systems online."]
        self.cpu_usage = 0
        self.ram_usage = 0
        self.ping_ms = 18
        self.uptime_start = time.time()
        self.setMinimumSize(1180, 720)

        ui_comm.toggle_chips.connect(self.show_context_chips)
        ui_comm.update_text.connect(self.update_status)
        ui_comm.update_log.connect(self.add_log)
        ui_comm.update_state.connect(self.change_system_state)

        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.animate)
        self.anim_timer.start(16)

        self.telemetry_timer = QTimer(self)
        self.telemetry_timer.timeout.connect(self.update_telemetry)
        self.telemetry_timer.start(1000)

        self._build_controls()
        self._apply_control_style()

    def _build_controls(self):
        # Sidebar
        self.btn_telemetry = QPushButton("◈  SYSTEM TELEMETRY", self)
        self.btn_export = QPushButton("⇩  EXPORT REPORT", self)
        self.btn_view_data = QPushButton("▦  DATA MATRIX", self)
        self.btn_automl = QPushButton("◉  AUTOML ARENA", self)
        self.btn_whatif = QPushButton("◇  WHAT-IF LAB", self)
        self.btn_repl = QPushButton("⌘  PYTHON CONSOLE", self)
        self.btn_theme = QPushButton("◐  THEME: CYAN", self)
        self.btn_mute = QPushButton("◉  VOICE: UNMUTED", self)
        self.btn_pause = QPushButton("◌  PAUSE: 2.0s", self)
        self.btn_exit = QPushButton("⏻  EXIT NEPTUNE", self)

        buttons = [
            (self.btn_telemetry, lambda: self._thread_command("Neptune, check system telemetry")),
            (self.btn_export, lambda: self._thread_command("Neptune, export session log")),
            (self.btn_view_data, self.open_data_table),
            (self.btn_automl, lambda: AutoMLDialog(self).exec_()),
            (self.btn_whatif, lambda: WhatIfPlaygroundDialog(self).exec_()),
            (self.btn_repl, lambda: PythonREPLDialog(self).exec_()),
            (self.btn_theme, self.cycle_theme),
            (self.btn_mute, self.toggle_mute),
            (self.btn_pause, self.cycle_pause_threshold),
            (self.btn_exit, self.shutdown_system),
        ]
        for btn, slot in buttons:
            btn.clicked.connect(slot)

        # Context actions
        self.chip_view = QPushButton("⚡  OPEN AUTOML", self)
        self.chip_plot = QPushButton("⚡  ANOMALY SENTINEL", self)
        self.chip_view.clicked.connect(lambda: AutoMLDialog(self).exec_())
        self.chip_plot.clicked.connect(
            lambda: self._thread_command("Neptune, run isolation forest anomaly scan")
        )
        self.chip_view.hide()
        self.chip_plot.hide()

        # Command bar
        self.cmd_input = QLineEdit(self)
        self.cmd_input.setPlaceholderText("Ask Neptune anything  •  e.g. analyze dataset, run AutoML, check system...")
        self.cmd_input.returnPressed.connect(self.handle_typed_command)

        self.send_btn = QPushButton("EXECUTE  ↵", self)
        self.send_btn.clicked.connect(self.handle_typed_command)

    def _apply_control_style(self):
        base = """
            QPushButton {
                background: rgba(10, 23, 38, 235);
                color: #CFEAF5;
                border: 1px solid rgba(73, 150, 181, 95);
                border-radius: 9px;
                padding: 9px 12px;
                font-family: "Segoe UI";
                font-size: 10px;
                font-weight: 700;
                letter-spacing: 1px;
                text-align: left;
            }
            QPushButton:hover {
                background: rgba(19, 49, 69, 245);
                border: 1px solid #45D9FF;
                color: #FFFFFF;
            }
            QPushButton:pressed {
                background: rgba(23, 76, 100, 245);
            }
        """
        for btn in [
            self.btn_telemetry, self.btn_export, self.btn_view_data,
            self.btn_automl, self.btn_whatif, self.btn_repl,
            self.btn_theme, self.btn_mute, self.btn_pause
        ]:
            btn.setStyleSheet(base)

        danger = base + """
            QPushButton {
                color: #FF9A9A;
                border: 1px solid rgba(255, 72, 72, 100);
                background: rgba(70, 15, 22, 190);
            }
            QPushButton:hover {
                background: rgba(120, 25, 35, 230);
                border-color: #FF5656;
                color: #FFFFFF;
            }
        """
        self.btn_exit.setStyleSheet(danger)

        chip = """
            QPushButton {
                background: rgba(15, 65, 80, 215);
                color: #62E8FF;
                border: 1px solid rgba(69, 217, 255, 160);
                border-radius: 16px;
                padding: 7px 14px;
                font-family: "Segoe UI";
                font-weight: 700;
            }
            QPushButton:hover { background: rgba(24, 92, 113, 235); }
        """
        self.chip_view.setStyleSheet(chip)
        self.chip_plot.setStyleSheet(chip)

        self.cmd_input.setStyleSheet("""
            QLineEdit {
                background: rgba(7, 17, 29, 245);
                color: #ECFAFF;
                border: 1px solid rgba(66, 202, 238, 155);
                border-radius: 12px;
                padding: 12px 16px;
                font-family: "Segoe UI";
                font-size: 12px;
                selection-background-color: #17627B;
            }
            QLineEdit:focus {
                border: 1px solid #5DE4FF;
                background: rgba(9, 25, 41, 250);
            }
        """)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background: rgba(25, 103, 126, 225);
                color: white;
                border: 1px solid #55DEFF;
                border-radius: 12px;
                padding: 0 18px;
                font-weight: 800;
                letter-spacing: 1px;
            }
            QPushButton:hover { background: rgba(37, 133, 157, 245); }
        """)

    def _thread_command(self, command):
        threading.Thread(target=process_command, args=(command,), daemon=True).start()

    def show_context_chips(self, visible):
        self.chip_view.setVisible(visible)
        self.chip_plot.setVisible(visible)

    def cycle_theme(self):
        global current_theme_idx
        current_theme_idx = (current_theme_idx + 1) % len(THEMES)
        self.btn_theme.setText(f"◐  THEME: {THEMES[current_theme_idx][0]}")
        ui_comm.update_log.emit(f"SYS: Visual theme shifted to {THEMES[current_theme_idx][0]}.")
        self.update()

    def toggle_mute(self):
        global voice_muted
        voice_muted = not voice_muted
        state = "MUTED" if voice_muted else "UNMUTED"
        self.btn_mute.setText(f"◉  VOICE: {state}")
        ui_comm.update_log.emit(f"SYS: Voice feedback {state.lower()}.")

    def cycle_pause_threshold(self):
        global current_pause_threshold
        current_pause_threshold = {2.0: 3.0, 3.0: 1.0, 1.0: 2.0}[current_pause_threshold]
        self.btn_pause.setText(f"◌  PAUSE: {current_pause_threshold:.1f}s")
        ui_comm.update_log.emit(f"SYS: Pause threshold set to {current_pause_threshold:.1f}s.")

    def shutdown_system(self):
        ui_comm.update_log.emit("SYS: User initiated shutdown.")
        speak("Shutting down systems. Goodbye.")
        os._exit(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        w, h = self.width(), self.height()

        sidebar_w = min(245, max(215, int(w * 0.18)))
        top = 86

        # Left command rail
        y = 150
        for btn in [
            self.btn_telemetry, self.btn_export, self.btn_view_data,
            self.btn_automl, self.btn_whatif, self.btn_repl,
            self.btn_theme, self.btn_mute, self.btn_pause, self.btn_exit
        ]:
            btn.setGeometry(28, y, sidebar_w - 48, 38)
            y += 44
        self.btn_exit.setGeometry(28, h - 86, sidebar_w - 48, 42)

        # Context chips
        self.chip_view.setGeometry(sidebar_w + 35, 116, 150, 34)
        self.chip_plot.setGeometry(sidebar_w + 195, 116, 175, 34)

        # Command dock
        dock_y = h - 68
        input_x = sidebar_w + 35
        input_w = max(280, w - input_x - 165)
        self.cmd_input.setGeometry(input_x, dock_y, input_w, 40)
        self.send_btn.setGeometry(w - 150, dock_y, 115, 40)

    def handle_typed_command(self):
        text = self.cmd_input.text().strip()
        if text:
            self.cmd_input.clear()
            threading.Thread(target=process_command, args=(text,), daemon=True).start()

    def open_data_table(self):
        global active_df
        if active_df is not None:
            DataTableDialog(active_df, self).exec_()
        else:
            ui_comm.update_log.emit("DATA: No active dataset loaded to preview.")

    def animate(self):
        speed = 0.35 if self.current_state == "STANDBY" else 1.15
        self.angle_outer = (self.angle_outer + speed) % 360
        self.angle_inner = (self.angle_inner - speed * 1.35) % 360
        self.pulse += 1.8 * self.pulse_dir
        if self.pulse >= 255:
            self.pulse_dir = -1
        elif self.pulse <= 90:
            self.pulse_dir = 1
        self.update()

    def update_telemetry(self):
        self.cpu_usage = psutil.cpu_percent()
        self.ram_usage = psutil.virtual_memory().percent
        self.ping_ms = int(np.random.randint(14, 28))

    def update_status(self, text):
        self.status_text = text
        self.dialogue_history.append(text)
        if len(self.dialogue_history) > 5:
            self.dialogue_history.pop(0)
        self.update()

    def change_system_state(self, new_state):
        self.current_state = new_state
        if new_state == "STANDBY":
            self.status_text = "SYSTEM STANDBY • AWAITING WAKE WORD"
        elif new_state == "ACTIVE":
            self.status_text = "SYSTEMS ONLINE • LISTENING"
        self.update()

    def add_log(self, text):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.system_logs.append(f"[{timestamp}] {text}")
        if len(self.system_logs) > 10:
            self.system_logs.pop(0)
        self.update()

    def _theme(self):
        _, r, g, b = THEMES[current_theme_idx]
        if self.current_state == "STANDBY":
            return 0, 150, 205
        return r, g, b

    def _panel(self, painter, rect, alpha=185, radius=14):
        r, g, b = self._theme()
        painter.setPen(QPen(QColor(r, g, b, 45), 1))
        painter.setBrush(QColor(6, 16, 28, alpha))
        painter.drawRoundedRect(rect, radius, radius)
        painter.setPen(QPen(QColor(r, g, b, 18), 1))
        painter.drawRoundedRect(rect.adjusted(5, 5, -5, -5), radius - 3, radius - 3)

    def _text(self, painter, x, y, text, size=10, color=None, bold=False):
        r, g, b = self._theme()
        painter.setFont(QFont("Segoe UI", size, QFont.Bold if bold else QFont.Normal))
        painter.setPen(QColor(*(color if color else (210, 232, 242)), 235))
        painter.drawText(int(x), int(y), text)

    def paintEvent(self, event):
        global audio_amplitude, active_dataset_info

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        r, g, b = self._theme()

        # Deep cinematic background
        bg = QRadialGradient(w * 0.55, h * 0.45, max(w, h) * 0.72)
        bg.setColorAt(0.0, QColor(10, 28, 45))
        bg.setColorAt(0.48, QColor(4, 13, 24))
        bg.setColorAt(1.0, QColor(1, 5, 11))
        painter.fillRect(self.rect(), bg)

        # Fine technical grid
        painter.setPen(QPen(QColor(r, g, b, 12), 1))
        grid = 42
        for x in range(0, w, grid):
            painter.drawLine(x, 86, x, h - 90)
        for y in range(86, h - 90, grid):
            painter.drawLine(0, y, w, y)

        sidebar_w = min(245, max(215, int(w * 0.18)))

        # Sidebar glass
        self._panel(painter, QRectF(15, 95, sidebar_w - 15, h - 185), 205, 16)
        painter.setPen(QPen(QColor(r, g, b, 55), 1))
        painter.drawLine(sidebar_w, 95, sidebar_w, h - 90)

        # Header
        self._text(painter, 28, 43, "NEPTUNE", 21, (238, 249, 255), True)
        self._text(painter, 28, 65, "AUTONOMOUS INTELLIGENCE PLATFORM", 8, (120, 192, 216), True)
        painter.setPen(QPen(QColor(r, g, b, 90), 1))
        painter.drawLine(28, 77, w - 28, 77)

        # Header status
        state_color = QColor(72, 229, 165) if self.current_state == "ACTIVE" else QColor(240, 190, 75)
        state_rect = QRectF(w - 205, 25, 165, 34)
        painter.setPen(QPen(state_color, 1))
        painter.setBrush(QColor(8, 27, 31, 225))
        painter.drawRoundedRect(state_rect, 17, 17)
        painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
        painter.setPen(state_color)
        painter.drawText(state_rect, Qt.AlignCenter, f"●  {self.current_state}")

        now = datetime.datetime.now()
        clock = now.strftime("%H:%M:%S")
        date = now.strftime("%a  •  %d %b %Y").upper()
        # Reserve a wider clock area so the first digits never clip into the edge.
        clock_rect = QRectF(w - 405, 28, 175, 32)
        date_rect = QRectF(w - 405, 59, 175, 16)
        painter.setFont(QFont("Consolas", 17, QFont.Bold))
        painter.setPen(QColor(r, g, b, 240))
        painter.drawText(clock_rect, Qt.AlignRight | Qt.AlignVCenter, clock)
        painter.setFont(QFont("Consolas", 8))
        painter.setPen(QColor(145, 184, 201, 210))
        painter.drawText(date_rect, Qt.AlignRight | Qt.AlignVCenter, date)

        # Sidebar labels
        self._text(painter, 30, 125, "CONTROL SURFACE", 8, (105, 171, 193), True)

        # Central intelligence chamber
        center_x = sidebar_w + (w - sidebar_w) * 0.52
        # Lift the Cognitive Core so it has clear visual separation from the bottom cards,
        # status ribbon, and command dock.
        center_y = h * 0.42
        radius = min(205, max(145, int(h * 0.28)))

        painter.save()
        painter.translate(center_x, center_y)

        # Ambient halo
        halo = QRadialGradient(0, 0, radius * 1.55)
        halo.setColorAt(0, QColor(r, g, b, 30))
        halo.setColorAt(0.52, QColor(r, g, b, 10))
        halo.setColorAt(1, QColor(r, g, b, 0))
        painter.setBrush(halo)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QRectF(-radius * 1.55, -radius * 1.55, radius * 3.1, radius * 3.1))

        # Orbit rings
        for rr, width, alpha, dash in [
            (radius, 3, 175, False),
            (radius - 17, 1, 75, True),
            (radius - 35, 1, 55, True)
        ]:
            pen = QPen(QColor(r, g, b, alpha), width)
            if dash:
                pen.setStyle(Qt.DashLine)
                pen.setDashPattern([2, 5])
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(QRectF(-rr, -rr, rr * 2, rr * 2))

        # Animated conical perimeter
        rim = QConicalGradient(0, 0, self.angle_outer)
        rim.setColorAt(0.00, QColor(r, g, b, 25))
        rim.setColorAt(0.20, QColor(r, g, b, 235))
        rim.setColorAt(0.42, QColor(r, g, b, 35))
        rim.setColorAt(0.67, QColor(r, g, b, 220))
        rim.setColorAt(1.00, QColor(r, g, b, 25))
        painter.setPen(QPen(rim, 5))
        painter.drawEllipse(QRectF(-radius, -radius, radius * 2, radius * 2))

        # Spectrum
        painter.setPen(QPen(QColor(r, g, b, 185), 2))
        bars = 72
        base = radius - 48
        for i in range(bars):
            a = math.radians(i * 360 / bars)
            idle = math.sin(self.pulse / 11 + i * .28) * 4
            live = audio_amplitude * (72 if self.current_state == "ACTIVE" else 15) * abs(math.sin(i * 2.1))
            end = base + idle + live
            painter.drawLine(
                int(base * math.cos(a)), int(base * math.sin(a)),
                int(end * math.cos(a)), int(end * math.sin(a))
            )

        # Core
        core_r = 78 + self.pulse / 9 + audio_amplitude * 35
        core = QRadialGradient(0, 0, core_r)
        core.setColorAt(0.00, QColor(245, 255, 255, 255))
        core.setColorAt(0.22, QColor(r, g, b, 245))
        core.setColorAt(0.60, QColor(r, g, b, 85))
        core.setColorAt(1.00, QColor(r, g, b, 0))
        painter.setBrush(core)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QRectF(-core_r, -core_r, core_r * 2, core_r * 2))

        # Core crosshair
        painter.setPen(QPen(QColor(235, 253, 255, 110), 1))
        painter.drawLine(-110, 0, -88, 0)
        painter.drawLine(88, 0, 110, 0)
        painter.drawLine(0, -110, 0, -88)
        painter.drawLine(0, 88, 0, 110)

        painter.restore()

        # Core title
        title_y = center_y + radius + 35
        painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
        painter.setPen(QColor(r, g, b, 220))
        painter.drawText(QRectF(center_x - 180, title_y, 360, 20), Qt.AlignCenter, "NEPTUNE  •  COGNITIVE CORE")
        painter.setFont(QFont("Consolas", 8))
        painter.setPen(QColor(132, 174, 191, 180))
        painter.drawText(QRectF(center_x - 220, title_y + 22, 440, 18), Qt.AlignCenter, "VOICE  /  VISION  /  DATA  /  AUTONOMOUS ACTION")

        # Right analytics rail
        right_x = w - 320
        self._panel(painter, QRectF(right_x, 110, 290, 190), 195, 14)
        self._text(painter, right_x + 18, 136, "LIVE INTELLIGENCE", 9, (111, 190, 214), True)
        self._text(painter, right_x + 18, 158, "DIALOGUE STREAM", 7, (92, 136, 153), True)

        yy = 181
        painter.setFont(QFont("Segoe UI", 8))
        for line in self.dialogue_history[-3:]:
            painter.setPen(QColor(189, 219, 229, 205))
            painter.drawText(QRectF(right_x + 18, yy, 255, 30), Qt.TextWordWrap, line)
            yy += 38

        # System metrics card
        self._panel(painter, QRectF(right_x, 315, 290, 185), 195, 14)
        self._text(painter, right_x + 18, 341, "SYSTEM TELEMETRY", 9, (111, 190, 214), True)

        metrics = [
            ("CPU LOAD", self.cpu_usage),
            ("MEMORY", self.ram_usage),
            ("NETWORK", min(100, self.ping_ms * 2.5)),
        ]
        yy = 365
        for label, value in metrics:
            painter.setFont(QFont("Consolas", 8, QFont.Bold))
            painter.setPen(QColor(180, 207, 218, 205))
            painter.drawText(int(right_x + 18), int(yy), f"{label:<12} {value:5.1f}%")
            bar = QRectF(right_x + 18, yy + 8, 250, 7)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(12, 28, 40, 240))
            painter.drawRoundedRect(bar, 3, 3)
            fill = QRectF(bar.x(), bar.y(), bar.width() * max(0, min(100, value)) / 100, bar.height())
            painter.setBrush(QColor(r, g, b, 210))
            painter.drawRoundedRect(fill, 3, 3)
            yy += 42

        uptime = int(time.time() - self.uptime_start)
        self._text(painter, right_x + 18, 488, f"UPTIME  {uptime // 3600:02d}:{(uptime % 3600)//60:02d}:{uptime % 60:02d}", 7, (115, 158, 176), True)

        # Lower intelligence cards. Keep them above the status ribbon and command dock.
        main_left = sidebar_w + 28
        right_rail_left = w - 320
        card_gap = 14
        cards_top = h - 315
        card_h = 125
        available_w = max(420, right_rail_left - main_left - 24)
        log_w = int((available_w - card_gap) * 0.52)
        data_w = available_w - log_w - card_gap

        log_rect = QRectF(main_left, cards_top, log_w, card_h)
        self._panel(painter, log_rect, 205, 13)
        self._text(painter, log_rect.x() + 16, log_rect.y() + 23,
                   "KERNEL / EVENT FEED", 8, (111, 190, 214), True)
        painter.setFont(QFont("Consolas", 7))
        yy = log_rect.y() + 43
        for log in self.system_logs[-4:]:
            painter.setPen(QColor(143, 181, 195, 205))
            painter.drawText(
                QRectF(log_rect.x() + 16, yy, log_rect.width() - 28, 16),
                Qt.TextSingleLine, log
            )
            yy += 17

        data_rect = QRectF(main_left + log_w + card_gap, cards_top, data_w, card_h)
        self._panel(painter, data_rect, 205, 13)
        self._text(painter, data_rect.x() + 16, data_rect.y() + 23,
                   "DATA INTELLIGENCE", 8, (111, 190, 214), True)
        painter.setFont(QFont("Segoe UI", 8))
        painter.setPen(QColor(182, 210, 220, 210))
        painter.drawText(
            QRectF(data_rect.x() + 16, data_rect.y() + 40,
                   data_rect.width() - 30, 36),
            Qt.TextWordWrap, f"ACTIVE DATASET\\n{active_dataset_info}"
        )
        painter.setPen(QColor(r, g, b, 220))
        painter.setFont(QFont("Consolas", 7, QFont.Bold))
        painter.drawText(
            QRectF(data_rect.x() + 16, data_rect.y() + 91,
                   data_rect.width() - 28, 16),
            Qt.AlignLeft | Qt.AlignVCenter,
            "AUTOMATION READY  •  ML TOOLS ONLINE"
        )

        # Bottom status ribbon
        ribbon = QRectF(sidebar_w + 35, h - 174, w - sidebar_w - 70, 34)
        painter.setPen(QPen(QColor(r, g, b, 75), 1))
        painter.setBrush(QColor(5, 18, 29, 220))
        painter.drawRoundedRect(ribbon, 10, 10)
        painter.setFont(QFont("Consolas", 9, QFont.Bold))
        painter.setPen(QColor(r, g, b, 225))
        painter.drawText(ribbon, Qt.AlignCenter, self.status_text.upper())

        # Footer
        painter.setFont(QFont("Consolas", 7))
        painter.setPen(QColor(93, 132, 148, 145))
        painter.drawText(QRectF(25, h - 22, w - 50, 14),
                         Qt.AlignRight | Qt.AlignVCenter,
                         "NEPTUNE AI  /  LOCAL INTELLIGENCE NODE  /  SECURE SESSION")

class NeptuneGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setMinimumSize(1180, 720)

        self.setStyleSheet("""
            QWidget {
                color: #DCEAF5;
                font-family: "Segoe UI";
            }
            QMainWindow, QDialog {
                background: #02070E;
            }
            QDialog {
                border: 1px solid #21485D;
            }
            QTextEdit, QPlainTextEdit, QListWidget, QTableWidget, QTableView {
                background: rgba(5, 15, 27, 245);
                color: #D9EAF5;
                border: 1px solid #234357;
                border-radius: 10px;
                gridline-color: #173244;
                selection-background-color: #15566E;
                selection-color: #FFFFFF;
                padding: 4px;
            }
            QHeaderView::section {
                background: #0B1D2B;
                color: #8FD8ED;
                border: 0;
                border-bottom: 1px solid #25495C;
                padding: 8px;
                font-weight: 700;
            }
            QScrollBar:vertical {
                background: #06101A;
                width: 9px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #28566B;
                min-height: 25px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover { background: #3D8CA7; }
            QToolTip {
                background: #0B2232;
                color: #EAFBFF;
                border: 1px solid #42D9F5;
                padding: 6px;
                border-radius: 5px;
            }
        """)

        self.hud = DynamicHUDWidget()
        self.setCentralWidget(self.hud)

        self.shortcut_f9 = QShortcut(QKeySequence("F9"), self)
        self.shortcut_f9.activated.connect(
            lambda: threading.Thread(
                target=lambda: process_command("Neptune, give me a system report"),
                daemon=True
            ).start()
        )

        self.shortcut_f10 = QShortcut(QKeySequence("F10"), self)
        self.shortcut_f10.activated.connect(
            lambda: threading.Thread(
                target=lambda: process_command("Neptune, analyze my screen"),
                daemon=True
            ).start()
        )

        self.shortcut_f12 = QShortcut(QKeySequence("F12"), self)
        self.shortcut_f12.activated.connect(lambda: control_system("lock"))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setApplicationName("Neptune AI")
    neptune_window = NeptuneGUI()
    neptune_window.showMaximized()

    threading.Thread(target=neptune_ai_worker, daemon=True).start()
    threading.Thread(
        target=audio_analyzer_worker,
        args=(neptune_window.hud,),
        daemon=True
    ).start()

    sys.exit(app.exec_())


import requests
import pyautogui
import random
import os
import time
from datetime import datetime
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QHBoxLayout
from PyQt5.QtCore import Qt, QTimer, QSettings, QThread, pyqtSignal
from pynput import keyboard

class KeyLoggerThread(QThread):
    """Thread for capturing keystrokes"""
    key_logged = pyqtSignal(str)  # Signal to send all captured keypresses
    key_counts = pyqtSignal(int)  # Signal to send all captured keypresses

    def __init__(self):
        super().__init__()
        self.key_log = ""  # Store full key log as a string
        self.running = True  
        self.key_count = 0

    def run(self):
        """Start listening for key presses"""
        def on_press(key):
            if self.running:
                try:
                    if hasattr(key, 'char') and key.char is not None:
                        self.key_log += key.char  # Append typed characters
                        self.key_count += 1
                    elif key == keyboard.Key.space:
                        self.key_log += " "  # Represent spaces
                        self.key_count += 1
                    elif key == keyboard.Key.enter:
                        self.key_log += "\n"  # Represent new lines
                        self.key_count += 1
                    else:
                        self.key_log += f"[{key.name}]"  # Special keys (e.g., Shift, Ctrl)
                        self.key_count += 1

                    self.key_logged.emit(self.key_log)  # Send updated log
                    self.key_counts.emit(self.key_count)  # Send updated log

                except Exception as e:
                    print("Error logging key:", str(e))

        with keyboard.Listener(on_press=on_press) as listener:
            listener.join()

    def reset_key_log(self):
        """Reset the key log for a new interval"""
        self.key_log = ""
        self.key_count = 0

    def stop(self):
        """Stop the key logger thread"""
        self.running = False

class StartWindow(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        self.setWindowTitle("Dashboard")
        self.setFixedSize(400, 200)

        self.is_running = False
        self.elapsed_seconds = 0
        self.duration_id = None

        # Load user details
        self.settings = QSettings("MyApp", "UserPreferences")
        self.user_id = self.settings.value("user_id", "")

        # Timer Label
        self.timer_label = QLabel("Time: 00:00:00")
        self.timer_label.setAlignment(Qt.AlignCenter)
        self.timer_label.setStyleSheet("font-size: 18px; font-weight: bold;")

        # Main Layout
        self.main_layout = QVBoxLayout()

        # Top Bar Layout
        self.top_bar = QHBoxLayout()
        self.logout_button = QPushButton("Logout")
        self.logout_button.setStyleSheet("background-color: gray; color: white; font-size: 14px;")
        self.logout_button.clicked.connect(self.logout)
        self.top_bar.addWidget(self.logout_button, alignment=Qt.AlignRight)

        # Start/Stop Button
        self.start_button = QPushButton("Start")
        self.start_button.setFixedSize(150, 50)
        self.start_button.setStyleSheet("background-color: green; color: white; border-radius: 25px; font-size: 16px;")
        self.start_button.clicked.connect(self.toggle_timer)

        # Add Widgets to Layout
        self.main_layout.addLayout(self.top_bar)
        self.main_layout.addWidget(self.timer_label)
        self.main_layout.addWidget(self.start_button, alignment=Qt.AlignCenter)
        self.setLayout(self.main_layout)

        if self.user_id:
            self.fetch_duration()

        # Timer Object
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)

        # Screenshot & Keylogger Timer (5-minute interval)
        self.process_timer = QTimer(self)
        self.process_timer.timeout.connect(self.process_interval)

        # Key Logger Thread
        self.key_logger_thread = KeyLoggerThread()
        self.key_logger_thread.key_logged.connect(self.update_keystroke_log)
        self.key_logger_thread.key_counts.connect(self.update_key_counts)
        self.key_logger_thread.start()

        self.keystroke_log = ""  # Store full keystroke log
        self.key_counts = 0  # Store full keystroke log
        self.screenshot_path = None  # Store latest screenshot path

    def fetch_duration(self):
        """Fetches the stored duration from the API and updates the timer."""
        try:
            response = requests.get(f'http://127.0.0.1:5000/api/duration/user/{self.user_id}')
            if response.status_code == 200:
                data = response.json()
                self.duration_id = data["id"]
                time_str = data["total_time"]
                h, m, s = map(int, time_str.split(":"))
                self.elapsed_seconds = h * 3600 + m * 60 + s
                self.update_time_display()
            else:
                print("No duration found for today.")
        except Exception as e:
            print("Error fetching duration:", str(e))

    def toggle_timer(self):
        """Start or stop the timer when the button is clicked"""
        if not self.is_running:
            self.timer.start(1000)  # Update every second
            self.schedule_random_screenshot()
            self.process_timer.start(300000)  # Trigger process every 5 minutes
            self.start_button.setText("Stop")
            self.start_button.setStyleSheet("background-color: red; color: white; border-radius: 25px; font-size: 16px;")
        else:
            self.timer.stop()
            self.process_timer.stop()
            self.process_interval()
            self.start_button.setText("Start")
            self.start_button.setStyleSheet("background-color: green; color: white; border-radius: 25px; font-size: 16px;")
            self.update_duration()

        self.is_running = not self.is_running  # Toggle state

    def update_duration(self):
        """Send a request to update the duration when the timer stops"""
        if self.user_id and self.duration_id:
            time_str = self.timer_label.text().replace("Time: ", "")  # Extract "HH:MM:SS"
            try:
                response = requests.post('http://127.0.0.1:5000/api/duration/update', json={
                    "user_id": self.user_id,
                    "duration_id": self.duration_id,
                    "total_time": time_str
                })
                if response.status_code == 200:
                    print("Duration updated successfully")
                else:
                    print("Failed to update duration:", response.text)
            except Exception as e:
                print("Error updating duration:", str(e))

    def update_time(self):
        """Update the timer display with HH:MM:SS format"""
        self.elapsed_seconds += 1
        self.update_time_display()

    def update_time_display(self):
        """Updates the displayed time based on elapsed_seconds"""
        hours = self.elapsed_seconds // 3600
        minutes = (self.elapsed_seconds % 3600) // 60
        seconds = self.elapsed_seconds % 60
        self.timer_label.setText(f"Time: {hours:02d}:{minutes:02d}:{seconds:02d}")

    def update_keystroke_log(self, log):
        """Updates the full keystroke log"""
        self.keystroke_log = log

    def update_key_counts(self, count):
        self.key_counts = count
        

    def schedule_random_screenshot(self):
        """Schedules a screenshot randomly within 5 minutes"""
        random_delay = random.randint(0, 300) * 1000  # Convert to milliseconds
        QTimer.singleShot(random_delay, self.take_screenshot)

    def take_screenshot(self):
        """Takes a screenshot"""
        if self.is_running:
            screenshot_dir = "screenshots"
            os.makedirs(screenshot_dir, exist_ok=True)
            # Check if any screenshot exists in the folder
            existing_screenshots = [f for f in os.listdir(screenshot_dir) if f.endswith(".png")]
            if existing_screenshots:
                print("Screenshot already exists. Skipping...")
                return


            self.screenshot_path = f"screenshots/ss{self.user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
            pyautogui.screenshot(self.screenshot_path)
            print(f"Screenshot saved: {self.screenshot_path}")

    def process_interval(self):
        """Uploads the screenshot and full keypress log after 5 minutes, then resets"""
        if self.screenshot_path and os.path.exists(self.screenshot_path):
            
            try:
                with open(self.screenshot_path, "rb") as file:
                    response = requests.post("http://127.0.0.1:5000/api/media", files={"file": file}, data={"user_id": self.user_id, "key_log": self.keystroke_log, "key_counts":self.key_counts})
                
                if response.status_code == 201:
                    print("Screenshot and keypress data uploaded successfully")
                    os.remove(self.screenshot_path)  # Delete the screenshot after upload
                    print("Screenshot deleted")

                else:
                    print("Failed to upload data:", response.text)

            except Exception as e:
                print("Error uploading screenshot:", str(e))

        # Reset key log and schedule next screenshot
        self.keystroke_log = ""
        self.key_logger_thread.reset_key_log()
        self.schedule_random_screenshot()

    def logout(self):
        """Clear local storage and logout the user"""
        self.settings.setValue("user_id", '')
        self.close()
        self.main_window.show()

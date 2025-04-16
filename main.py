#!/opt/homebrew/Caskroom/miniconda/base/bin/python
# -*- coding: utf-8 -*-

import sys
import platform
import subprocess
import tkinter as tk
from tkinter import ttk
import time

from Settings import Settings

def send_notification(title, message):
    """
    Send a system notification.
    This function encapsulates the notification sending method.
    Modify it as needed for Windows, macOS, or Ubuntu.
    """
    current_platform = platform.system().lower()
    try:
        if "windows" in current_platform:
            # For Windows, use Toast notifications (win10toast required).
            from win10toast import ToastNotifier
            toaster = ToastNotifier()
            toaster.show_toast(title, message, duration=5)
        elif "darwin" in current_platform:
            # For macOS, using AppleScript.
            subprocess.call(['osascript', '-e',
                             f'display notification "{message}" with title "{title}"'])
            subprocess.call(['osascript', '-e', f'display dialog "{message}" with title "{title}" buttons {{"OK"}} default button "OK"'])
        elif "linux" in current_platform:
            # For Ubuntu and other Linux distributions.
            subprocess.call(['notify-send', title, message])
        else:
            # For unknown platforms, just print the notification.
            print(f"[{title}] {message}")
    except Exception as e:
        print("Notification error:", e)
        print(f"[{title}] {message}")

class CountdownApp:
    def __init__(self, master: tk.Tk):
        self.master = master
        master.title("Corian Timer")
        
        # Set window geometry: 1/3 of screen size and centered.
        screen_width = master.winfo_screenwidth()
        screen_height = master.winfo_screenheight()
        width = int(screen_width / 4)
        height = int(screen_height / 4)
        x_pos = int((screen_width - width) / 2)
        y_pos = int((screen_height - height) / 2)
        master.geometry(f"{width}x{height}+{x_pos}+{y_pos}")
        self.font_size = screen_height // 80  # Font size based on screen height

        # Main frame to contain all elements with a grid.
        self.main_frame = ttk.Frame(master)
        self.main_frame.pack(fill="both", expand=True)

        # Configure grid rows and columns for dynamic resizing.
        for i in range(7):
            self.main_frame.rowconfigure(i, weight=1)
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=1)

        # Row0: Input fields for optional and mandatory break time (in minutes)
        self.optional_label_entry = ttk.Label(self.main_frame, text="Optional break (min):", anchor="center", font=("Arial", self.font_size))
        self.optional_label_entry.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.optional_entry = ttk.Entry(self.main_frame, font=("Arial", self.font_size))
        self.optional_entry.insert(0, str(Settings.default_min_work_time))  # default value
        self.optional_entry.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        self.mandatory_label_entry = ttk.Label(self.main_frame, text="Mandatory break (min):", anchor="center", font=("Arial", self.font_size))
        self.mandatory_label_entry.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.mandatory_entry = ttk.Entry(self.main_frame, font=("Arial", self.font_size))
        self.mandatory_entry.insert(0, str(Settings.default_max_work_time))  # default value
        self.mandatory_entry.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)

        # Row2: Mandatory break countdown label
        self.countdown_label = ttk.Label(self.main_frame, text="Time left until mandatory break:", anchor="center", font=("Arial", self.font_size))
        self.countdown_label.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=10, pady=5)

        # Row3: Mandatory break countdown timer value
        self.timer_value_label = ttk.Label(self.main_frame, text="", anchor="center", font=("Arial", self.font_size))
        self.timer_value_label.grid(row=3, column=0, columnspan=2, sticky="nsew", padx=10, pady=5)

        # Row4: Optional break countdown label
        self.optional_countdown_label = ttk.Label(self.main_frame, text="Time left until optional break:", anchor="center", font=("Arial", self.font_size))
        self.optional_countdown_label.grid(row=4, column=0, columnspan=2, sticky="nsew", padx=10, pady=5)

        # Row5: Optional break countdown timer value
        self.optional_timer_label = ttk.Label(self.main_frame, text="", anchor="center", font=("Arial", self.font_size))
        self.optional_timer_label.grid(row=5, column=0, columnspan=2, sticky="nsew", padx=10, pady=5)

        # Row6: Control buttons (Start, Pause/Resume, Stop)
        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.grid(row=6, column=0, columnspan=2, sticky="nsew", padx=10, pady=10)

        self.start_button = ttk.Button(self.button_frame, text="Start", command=self.start_timer)
        self.start_button.pack(side="left", expand=True, fill="both", padx=5)

        self.pause_button = ttk.Button(self.button_frame, text="Pause", command=self.pause_resume_timer, state="disabled")
        self.pause_button.pack(side="left", expand=True, fill="both", padx=5)

        self.stop_button = ttk.Button(self.button_frame, text="Stop", command=self.stop_timer, state="disabled")
        self.stop_button.pack(side="left", expand=True, fill="both", padx=5)

        # Timer control variables.
        self.start_time = None
        self.running = False
        self.paused = False
        self.pause_start = None  # time when paused
        
        # Notification flags.
        self.first_notification_sent = False
        self.second_notification_sent = False

        # Store break times (in seconds)
        self.x_seconds = None
        self.y_seconds = None
        
        # icon
        icon_base64 = Settings.icon_base64
        self.master.iconphoto(True, tk.PhotoImage(data=icon_base64))

    def start_timer(self):
        try:
            opt_minutes = int(self.optional_entry.get())
            mand_minutes = int(self.mandatory_entry.get())
        except ValueError:
            # If conversion error, fail gracefully.
            self.timer_value_label.config(text="Invalid input!")
            return

        self.x_seconds = opt_minutes * 60
        self.y_seconds = mand_minutes * 60

        # Disable the input fields and start button.
        self.optional_entry.config(state="disabled")
        self.mandatory_entry.config(state="disabled")
        self.start_button.config(state="disabled")
        self.pause_button.config(state="normal")
        self.stop_button.config(state="normal")

        self.start_time = time.time()
        self.running = True
        self.paused = False
        self.first_notification_sent = False
        self.second_notification_sent = False
        self.update_timer()

    def pause_resume_timer(self):
        if not self.running:
            return
        if not self.paused:
            # Pause the timer.
            self.paused = True
            self.pause_start = time.time()
            self.pause_button.config(text="Resume")
        else:
            # Resume the timer: adjust start_time to account for paused duration.
            paused_duration = time.time() - self.pause_start
            self.start_time += paused_duration
            self.paused = False
            self.pause_button.config(text="Pause")
            self.update_timer()

    def stop_timer(self):
        # Stop the timer and reset everything.
        self.running = False
        self.paused = False
        self.start_time = None
        self.pause_start = None
        self.first_notification_sent = False
        self.second_notification_sent = False
        self.timer_value_label.config(text="")
        self.optional_timer_label.config(text="")
        self.start_button.config(state="normal")
        self.pause_button.config(state="disabled", text="Pause")
        self.stop_button.config(state="disabled")
        # Re-enable the input fields.
        self.optional_entry.config(state="normal")
        self.mandatory_entry.config(state="normal")

    def update_timer(self):
        if not self.running:
            return
        if self.paused:
            # If paused, simply schedule the next check.
            self.master.after(500, self.update_timer)
            return

        elapsed = int(time.time() - self.start_time)
        
        remaining_y = self.y_seconds - elapsed
        if remaining_y < 0:
            remaining_y = 0

        remaining_x = self.x_seconds - elapsed
        if remaining_x < 0:
            remaining_x = 0

        self.timer_value_label.config(text=self.format_time(remaining_y))
        self.optional_timer_label.config(text=self.format_time(remaining_x))

        # Send notifications.
        if (not self.first_notification_sent) and elapsed >= self.x_seconds:
            send_notification("Optional Break", f"You have worked for {self.x_seconds // 60} minutes. If possible, take a break!")
            self.first_notification_sent = True

        if (not self.second_notification_sent) and elapsed >= self.y_seconds:
            send_notification("Mandatory Break", f"You have worked for {self.y_seconds // 60} minutes. Time to take a break immediately!")
            self.second_notification_sent = True

        if elapsed < self.y_seconds:
            self.master.after(1000, self.update_timer)
        else:
            self.running = False
            # Timer finished, re-enable start and disable pause.
            self.start_button.config(state="normal")
            self.pause_button.config(state="disabled")
            self.stop_button.config(state="disabled")
            # Also re-enable input fields.
            self.optional_entry.config(state="normal")
            self.mandatory_entry.config(state="normal")

    def format_time(self, seconds):
        m, s = divmod(seconds, 60)
        return f"{m:02d}:{s:02d}"

def main():
    root = tk.Tk()
    app = CountdownApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()

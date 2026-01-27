import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import time
import numpy as np
from PIL import Image
import pyautogui
import os
import random
import json
from datetime import datetime
from queue import Queue
import traceback
import sys
import subprocess
import platform
import glob
import shutil
import tempfile
import re

_BUFFERED_LOGS = []
_APP_INSTANCE = None
_APP_LOCK = threading.Lock()

def app_log(message, level="info"):
    global _BUFFERED_LOGS, _APP_INSTANCE
    try:
        with _APP_LOCK:
            if _APP_INSTANCE is not None:
                try:
                    _APP_INSTANCE.log(str(message), level)
                except Exception:
                    _BUFFERED_LOGS.append((str(message), level))
            else:
                _BUFFERED_LOGS.append((str(message), level))
    except Exception:
        try:
            _BUFFERED_LOGS.append((str(message), level))
        except Exception:
            pass

try:
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    app_log("Warning: pytesseract not installed. OCR antibot detection will not work.", "warning")

send_lock = threading.Lock()
COLORS = {
    'bg': "#0a0e27",
    'surface': '#1a1f3a',
    'surface_light': '#252d48',
    'primary': "#7aa2f7",
    'success': '#9ece6a',
    'warning': '#e0af68',
    'danger': '#f7768e',
    'text': '#c0caf5',
    'text_dim': '#565f89',
    'border': '#414868',
    'accent': '#bb9af7',
    'hover': "#c8d1fa",
    'section_title': '#7dcfff'
}

class ModernButton(tk.Canvas):
    def __init__(self, parent, text, command, bg_color, width=140, height=45):
        try:
            parent_bg = parent.cget('bg')
        except:
            parent_bg = COLORS['bg']
        super().__init__(parent, width=width, height=height, bg=parent_bg, highlightthickness=0)
        self.command = command
        self.bg_color = bg_color
        self.text = text
        self.hover = False
        self.enabled = True
        self.width = width
        self.height = height
        self.draw_button()
        self.bind('<Button-1>', self.on_click)
        self.bind('<Enter>', self.on_enter)
        self.bind('<Leave>', self.on_leave)

    def draw_button(self):
        try:
            self.delete('all')
            color = self.bg_color if self.enabled else COLORS['surface_light']
            if self.hover and self.enabled:
                color = self.lighten_color(color)
            shadow_color = self.darken_color(self.bg_color, 40) if self.enabled else COLORS['surface_light']
            self.create_rounded_rect(4, 4, self.width, self.height, radius=8, fill=shadow_color, outline='')
            if self.hover and self.enabled:
                top_color = self.lighten_color(color, 30)
                bottom_color = color
            else:
                top_color = color
                bottom_color = self.darken_color(color, 20)
            self.create_gradient_rect(2, 2, self.width - 2, self.height - 2, top_color, bottom_color, radius=8)
            text_x = self.width // 2
            text_y = self.height // 2
            text_color = COLORS['text'] if self.enabled else COLORS['text_dim']
            shadow_offset = 1 if self.hover else 2
            if self.enabled:
                self.create_text(text_x + 1, text_y + shadow_offset, text=self.text,
                               fill=COLORS['text_dim'], font=('Segoe UI', 11, 'bold'))
            self.create_text(text_x, text_y + shadow_offset, text=self.text,
                            fill=text_color, font=('Segoe UI', 11, 'bold'))
        except:
            pass

    def create_rounded_rect(self, x1, y1, x2, y2, radius=10, **kwargs):
        try:
            points = [x1+radius, y1, x1+radius, y1, x2-radius, y1, x2-radius, y1,
                     x2, y1, x2, y1+radius, x2, y1+radius, x2, y2-radius,
                     x2, y2-radius, x2, y2, x2-radius, y2, x2-radius, y2,
                     x1+radius, y2, x1+radius, y2, x1, y2, x1, y2-radius,
                     x1, y2-radius, x1, y1+radius, x1, y1+radius, x1, y1]
            return self.create_polygon(points, smooth=True, **kwargs)
        except:
            return None

    def create_gradient_rect(self, x1, y1, x2, y2, color1, color2, radius=10):
        try:
            gradient_steps = 20
            height = y2 - y1
            step_size = height / gradient_steps
            for i in range(gradient_steps):
                ratio = i / gradient_steps
                r = int(int(color1[1:3], 16) * (1-ratio) + int(color2[1:3], 16) * ratio)
                g = int(int(color1[3:5], 16) * (1-ratio) + int(color2[3:5], 16) * ratio)
                b = int(int(color1[5:7], 16) * (1-ratio) + int(color2[5:7], 16) * ratio)
                color = f'#{r:02x}{g:02x}{b:02x}'
                if i == 0:
                    self.create_rounded_rect(x1, y1, x2, y1 + step_size * 2,
                                          radius=radius, fill=color, outline='')
                elif i == gradient_steps - 1:
                    self.create_rounded_rect(x1, y2 - step_size * 2, x2, y2,
                                          radius=radius, fill=color2, outline='')
                else:
                    y_top = y1 + step_size * i
                    y_bottom = y1 + step_size * (i + 1)
                    self.create_rectangle(x1, y_top, x2, y_bottom,
                                       fill=color, outline='')
        except:
            pass

    def lighten_color(self, color, amount=20):
        try:
            color = color.lstrip('#')
            r, g, b = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
            r = min(255, r + amount)
            g = min(255, g + amount)
            b = min(255, b + amount)
            return f'#{r:02x}{g:02x}{b:02x}'
        except:
            return color

    def darken_color(self, color, amount=30):
        try:
            color = color.lstrip('#')
            r, g, b = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
            r = max(0, r - amount)
            g = max(0, g - amount)
            b = max(0, b - amount)
            return f'#{r:02x}{g:02x}{b:02x}'
        except:
            return color

    def on_click(self, event):
        if self.enabled and self.command:
            self.command()

    def on_enter(self, event):
        self.hover = True
        self.draw_button()

    def on_leave(self, event):
        self.hover = False
        self.draw_button()

    def set_enabled(self, enabled):
        self.enabled = enabled
        self.draw_button()

class CommandScheduler:
    def __init__(self):
        self.lock = threading.Lock()
        self.last_command_time = 0
        self.min_gap = 0.8
        self.gui = None

    def can_send(self):
        with self.lock:
            current_time = time.time()
            time_since_last = current_time - self.last_command_time
            can_send = time_since_last >= self.min_gap
            if can_send:
                self.last_command_time = current_time
            return can_send

    def wait_for_slot(self, timeout=30):
        start_time = time.time()
        while not self.can_send():
            if time.time() - start_time > timeout:
                return False
            time.sleep(0.1)
        return True

    def humanize_delay(self, base_delay):
        if not self.gui or not self.gui.random_enabled.get():
            return base_delay
        variance = self.gui.command_variance.get()
        min_delay = base_delay * (1 - variance)
        max_delay = base_delay * (1 + variance)
        return random.uniform(min_delay, max_delay)

    def humanize_typing(self, text):
        if not self.gui or not self.gui.random_enabled.get():
            try:
                if platform.system() == 'Linux':
                    subprocess.run(['xdotool', 'type', '--', text], check=True)
                else:
                    pyautogui.write(text)
                time.sleep(0.3)
            except Exception as e:
                app_log(f"Typing error: {e}", "warning")
                pyautogui.write(text)
                time.sleep(0.3)
            return
        try:
            if platform.system() == 'Linux':
                for char in text:
                    delay = random.uniform(
                        self.gui.typing_delay_min.get(),
                        self.gui.typing_delay_max.get()
                    )
                    subprocess.run(['xdotool', 'type', '--', char], check=True)
                    time.sleep(delay)
            else:
                for char in text:
                    delay = random.uniform(
                        self.gui.typing_delay_min.get(),
                        self.gui.typing_delay_max.get()
                    )
                    pyautogui.write(char, interval=delay)
        except Exception as e:
            app_log(f"Humanized typing error: {e}", "error")
            pyautogui.write(text)
        pause = random.uniform(
            self.gui.typing_pause_min.get(),
            self.gui.typing_pause_max.get()
        )
        time.sleep(pause)

class FloatingControlPanel:
    def __init__(self, parent_gui, root):
        self.parent_gui = parent_gui
        self.root = root
        self.settings_window = None
        self.setup_ui()

    def setup_ui(self):
        self.root.title("Project Promohomo")
        self.root.geometry("400x600")
        self.root.resizable(True, True)
        self.root.configure(bg=COLORS['bg'])
        self.root.attributes('-topmost', True)
        self.root.minsize(300, 400)

        main_frame = tk.Frame(self.root, bg=COLORS['surface'],
                             highlightbackground=COLORS['border'],
                             highlightthickness=1)
        main_frame.pack(fill='both', expand=True, padx=2, pady=2)

        title = tk.Label(main_frame, text="Project Promohomo",
                        font=('Segoe UI', 14, 'bold'),
                        bg=COLORS['surface'], fg=COLORS['primary'])
        title.pack(pady=(10, 5))

        status_frame = tk.Frame(main_frame, bg=COLORS['surface'])
        status_frame.pack(fill='x', padx=15, pady=(5, 10))

        tk.Label(status_frame, text="Status:",
                font=('Segoe UI', 9, 'bold'),
                bg=COLORS['surface'], fg=COLORS['text']).pack(anchor='w')

        self.status_indicator = tk.Label(status_frame, text="Stopped",
                                        font=('Segoe UI', 11, 'bold'),
                                        bg=COLORS['surface'],
                                        fg=COLORS['danger'])
        self.status_indicator.pack(anchor='w', pady=(2, 0))

        btn_frame = tk.Frame(main_frame, bg=COLORS['surface'])
        btn_frame.pack(pady=(5, 15))

        self.start_btn = ModernButton(btn_frame, "Start",
                                      self.parent_gui.start_macro, COLORS['success'],
                                      width=75, height=35)
        self.start_btn.pack(side='left', padx=5)

        self.pause_btn = ModernButton(btn_frame, "Pause",
                                      self.parent_gui.pause_macro, COLORS['warning'],
                                      width=75, height=35)
        self.pause_btn.set_enabled(False)
        self.pause_btn.pack(side='left', padx=5)

        self.stop_btn = ModernButton(btn_frame, "Stop",
                                     self.parent_gui.stop_macro, COLORS['danger'],
                                     width=75, height=35)
        self.stop_btn.set_enabled(False)
        self.stop_btn.pack(side='left', padx=5)

        settings_btn = ModernButton(main_frame, "Settings",
                                   self.open_settings, COLORS['accent'],
                                   width=360, height=32)
        settings_btn.pack(pady=(0, 10), padx=15)

        log_header = tk.Frame(main_frame, bg=COLORS['surface'])
        log_header.pack(fill='x', padx=15, pady=(10, 5))
        tk.Label(log_header, text="Activity Log",
                font=('Segoe UI', 10, 'bold'),
                bg=COLORS['surface'], fg=COLORS['section_title']).pack(anchor='w')

        log_container = tk.Frame(main_frame, bg=COLORS['surface'])
        log_container.pack(fill='both', expand=True, padx=15, pady=(0, 10))

        self.log_text = tk.Text(log_container,
                               font=('Consolas', 8),
                               bg=COLORS['surface_light'],
                               fg=COLORS['text'],
                               bd=0, relief='flat',
                               wrap='word',
                               height=10,
                               padx=5, pady=5,
                               insertbackground=COLORS['text'],
                               selectbackground=COLORS['primary'],
                               selectforeground=COLORS['text'])

        log_scrollbar = tk.Scrollbar(log_container,
                                command=self.log_text.yview,
                                bg=COLORS['surface_light'],
                                troughcolor=COLORS['surface'],
                                bd=0, width=10)

        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        self.log_text.config(state='disabled')
        self.log_text.pack(side='left', fill='both', expand=True)
        log_scrollbar.pack(side='right', fill='y')

    def open_settings(self):
        if self.settings_window and self.settings_window.root.winfo_exists():
            self.settings_window.root.lift()
            return
        self.settings_window = SettingsWindow(self.parent_gui, self.root)

    def update_status(self, status_text, status_color):
        try:
            self.status_indicator.config(text=status_text, fg=status_color)
        except:
            pass

    def add_log(self, message, level="info"):
        def _add_to_log():
            try:
                if not self.log_text.winfo_exists():
                    return

                timestamp = datetime.now().strftime("%H:%M:%S")
                colors = {
                    "info": COLORS['text'],
                    "success": COLORS['success'],
                    "warning": COLORS['warning'],
                    "error": COLORS['danger'],
                    "command": COLORS['primary']
                }

                self.log_text.tag_config('timestamp', foreground=COLORS['text_dim'])
                for tag, color in colors.items():
                    self.log_text.tag_config(tag, foreground=color)

                self.log_text.config(state='normal')
                self.log_text.insert('end', f"[{timestamp}] ", ('timestamp',))
                self.log_text.insert('end', f"{message}\n", (level,))
                self.log_text.see('end')
                self.log_text.config(state='disabled')
            except:
                pass

        try:
            self.root.after(0, _add_to_log)
        except:
            pass

class SettingsWindow:
    def __init__(self, parent_gui, parent_root):
        self.parent_gui = parent_gui
        self.root = tk.Toplevel(parent_root)
        self.root.title("OwO Bot Settings")
        self.root.geometry("650x750")
        self.root.resizable(True, True)
        self.root.configure(bg=COLORS['bg'])
        self.root.minsize(400, 500)
        self.setup_ui()

    def create_themed_frame(self, parent, style='normal'):
        try:
            if style == 'section':
                frame = tk.Frame(parent, bg=COLORS['surface'],
                                highlightbackground=COLORS['border'],
                                highlightthickness=1)
            elif style == 'surface':
                frame = tk.Frame(parent, bg=COLORS['surface'])
            elif style == 'input':
                frame = tk.Frame(parent, bg=COLORS['surface_light'])
            else:
                frame = tk.Frame(parent, bg=COLORS['bg'])
            return frame
        except:
            return tk.Frame(parent, bg=COLORS['bg'])

    def setup_ui(self):
        main_container = tk.Frame(self.root, bg=COLORS['bg'])
        main_container.pack(fill='both', expand=True, padx=15, pady=15)

        title = tk.Label(main_container, text="Settings",
                        font=('Segoe UI', 20, 'bold'),
                        bg=COLORS['bg'], fg=COLORS['primary'])
        title.pack(pady=(0, 20))

        canvas = tk.Canvas(main_container, bg=COLORS['bg'], highlightthickness=0)
        scrollbar = tk.Scrollbar(main_container, orient="vertical", command=canvas.yview,
                                bg=COLORS['surface_light'], troughcolor=COLORS['surface'],
                                bd=0, width=12)
        scrollable_frame = tk.Frame(canvas, bg=COLORS['bg'])
        scrollable_frame.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(window_id, width=e.width))
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        img_frame = self.create_themed_frame(scrollable_frame, 'section')
        img_frame.pack(fill='x', pady=(0, 15), padx=0)

        section_title = tk.Label(img_frame, text="Anti-Bot Image",
                          font=('Segoe UI', 11, 'bold'),
                          bg=COLORS['surface'], fg=COLORS['section_title'])
        section_title.pack(anchor='w', padx=15, pady=(10, 5))

        self.image_label = tk.Label(img_frame, text="No image selected",
                                  font=('Segoe UI', 9),
                                  bg=COLORS['surface_light'],
                                  fg=COLORS['text_dim'],
                                  anchor='w', padx=12, pady=8,
                                  wraplength=400)
        self.image_label.pack(fill='x', padx=15, pady=(0, 8))

        browse_btn = ModernButton(img_frame, "Browse",
                                lambda: self.parent_gui.select_image(self.update_image_label),
                                COLORS['primary'],
                                width=100, height=32)
        browse_btn.pack(anchor='e', padx=15, pady=(0, 10))

        win_frame = self.create_themed_frame(scrollable_frame, 'section')
        win_frame.pack(fill='x', padx=0, pady=(0, 15))

        tk.Label(win_frame, text="Window Name:",
                font=('Segoe UI', 10, 'bold'),
                bg=COLORS['surface'], fg=COLORS['text']).pack(anchor='w', padx=15, pady=(10, 5))

        window_entry = tk.Entry(win_frame, textvariable=self.parent_gui.window_name,
                               font=('Segoe UI', 10),
                               bg=COLORS['surface_light'],
                               fg=COLORS['text'],
                               bd=0, insertbackground=COLORS['text'],
                               relief='flat')
        window_entry.pack(fill='x', padx=15, pady=(0, 10))

        timing_frame = self.create_themed_frame(scrollable_frame, 'section')
        timing_frame.pack(fill='x', pady=(0, 15), padx=0)

        tk.Label(timing_frame, text="Command Cooldowns (seconds)",
                font=('Segoe UI', 10, 'bold'),
                bg=COLORS['surface'], fg=COLORS['text']).pack(anchor='w', padx=15, pady=(10, 5))

        self.create_cooldown_control(timing_frame, "owo buy Command:",
                                     self.parent_gui.owobuy_cooldown, 1.0, 30.0)
        self.create_cooldown_control(timing_frame, "owo Command:",
                                     self.parent_gui.owo_cooldown, 1.0, 60.0)
        self.create_cooldown_control(timing_frame, "owoh/owob Commands:",
                                     self.parent_gui.owoh_owob_cooldown, 1.0, 60.0)

        toggles_frame = self.create_themed_frame(scrollable_frame, 'section')
        toggles_frame.pack(fill='x', pady=(0, 15), padx=0)

        tk.Label(toggles_frame, text="Command Options",
                font=('Segoe UI', 10, 'bold'),
                bg=COLORS['surface'], fg=COLORS['text']).pack(anchor='w', padx=15, pady=(10, 5))

        owobuy_toggle = tk.Frame(toggles_frame, bg=COLORS['surface'])
        owobuy_toggle.pack(fill='x', padx=15, pady=(0, 10))
        tk.Label(owobuy_toggle, text="Enable owo buy Command:",
                font=('Segoe UI', 9),
                bg=COLORS['surface'], fg=COLORS['text']).pack(side='left')
        tk.Checkbutton(owobuy_toggle, variable=self.parent_gui.owobuy_enabled,
                      bg=COLORS['surface'], fg=COLORS['text'],
                      activebackground=COLORS['surface'],
                      selectcolor=COLORS['surface_light']).pack(side='left', padx=10)

        owo_toggle = tk.Frame(toggles_frame, bg=COLORS['surface'])
        owo_toggle.pack(fill='x', padx=15, pady=(0, 10))
        tk.Label(owo_toggle, text="Enable owo Command:",
                font=('Segoe UI', 9),
                bg=COLORS['surface'], fg=COLORS['text']).pack(side='left')
        tk.Checkbutton(owo_toggle, variable=self.parent_gui.owo_enabled,
                      bg=COLORS['surface'], fg=COLORS['text'],
                      activebackground=COLORS['surface'],
                      selectcolor=COLORS['surface_light']).pack(side='left', padx=10)

        hb_toggle = tk.Frame(toggles_frame, bg=COLORS['surface'])
        hb_toggle.pack(fill='x', padx=15, pady=(0, 10))
        tk.Label(hb_toggle, text="Use /hunt & /battle instead of owoh/owob:",
                font=('Segoe UI', 9),
                bg=COLORS['surface'], fg=COLORS['text']).pack(side='left')
        tk.Checkbutton(hb_toggle, variable=self.parent_gui.use_slash_hunt_battle,
                      bg=COLORS['surface'], fg=COLORS['text'],
                      activebackground=COLORS['surface'],
                      selectcolor=COLORS['surface_light']).pack(side='left', padx=10)

        random_frame = self.create_themed_frame(scrollable_frame, 'section')
        random_frame.pack(fill='x', pady=(0, 15), padx=0)

        tk.Label(random_frame, text="Randomization Settings",
                font=('Segoe UI', 10, 'bold'),
                bg=COLORS['surface'], fg=COLORS['text']).pack(anchor='w', padx=15, pady=(10, 5))

        random_toggle = tk.Frame(random_frame, bg=COLORS['surface'])
        random_toggle.pack(fill='x', padx=15, pady=(0, 10))
        tk.Label(random_toggle, text="Enable Randomization:",
                font=('Segoe UI', 9),
                bg=COLORS['surface'], fg=COLORS['text']).pack(side='left')
        tk.Checkbutton(random_toggle, variable=self.parent_gui.random_enabled,
                      bg=COLORS['surface'], fg=COLORS['text'],
                      activebackground=COLORS['surface'],
                      selectcolor=COLORS['surface_light']).pack(side='left', padx=10)

        self.create_cooldown_control(random_frame,
                                   "Command Timing Variance (%):",
                                   self.parent_gui.command_variance, 0.0, 0.5,
                                   value_format=lambda x: f"{int(x * 100)}%")
        self.create_cooldown_control(random_frame,
                                   "Min Typing Delay (ms):",
                                   self.parent_gui.typing_delay_min, 0.01, 0.1,
                                   resolution=0.01,
                                   value_format=lambda x: f"{int(x * 1000)}ms")
        self.create_cooldown_control(random_frame,
                                   "Max Typing Delay (ms):",
                                   self.parent_gui.typing_delay_max, 0.02, 0.2,
                                   resolution=0.01,
                                   value_format=lambda x: f"{int(x * 1000)}ms")
        self.create_cooldown_control(random_frame,
                                   "Min Post-Typing Pause (ms):",
                                   self.parent_gui.typing_pause_min, 0.1, 1.0,
                                   resolution=0.1,
                                   value_format=lambda x: f"{int(x * 1000)}ms")
        self.create_cooldown_control(random_frame,
                                   "Max Post-Typing Pause (ms):",
                                   self.parent_gui.typing_pause_max, 0.2, 1.5,
                                   resolution=0.1,
                                   value_format=lambda x: f"{int(x * 1000)}ms")

    def create_cooldown_control(self, parent, label_text, variable, min_val, max_val,
                               resolution=0.5, value_format=None):
        frame = self.create_themed_frame(parent, 'surface')
        frame.pack(fill='x', padx=15, pady=(0, 10))

        label_container = tk.Frame(frame, bg=COLORS['surface'])
        label_container.pack(fill='x')

        tk.Label(label_container, text=label_text,
                font=('Segoe UI', 9),
                bg=COLORS['surface'], fg=COLORS['text']).pack(side='left')

        if value_format is None:
            value_format = lambda x: f"{x:.1f}s"

        value_label = tk.Label(label_container, text=value_format(variable.get()),
                              font=('Segoe UI', 9, 'bold'),
                              bg=COLORS['surface'], fg=COLORS['primary'])
        value_label.pack(side='right')

        scale = tk.Scale(frame, from_=min_val, to=max_val,
                        resolution=resolution,
                        orient='horizontal',
                        variable=variable,
                        bg=COLORS['surface_light'],
                        fg=COLORS['text'],
                        troughcolor=COLORS['surface'],
                        activebackground=COLORS['primary'],
                        highlightthickness=0,
                        bd=0,
                        font=('Segoe UI', 8),
                        showvalue=False,
                        length=600,
                        digits=3)
        scale.pack(fill='x', pady=(5, 0))

        def update_label(*args):
            if not value_label.winfo_exists():
                return
            try:
                current_value = variable.get()
                if current_value < min_val:
                    variable.set(min_val)
                elif current_value > max_val:
                    variable.set(max_val)
                value_label.config(text=value_format(variable.get()))
            except:
                pass

        variable.trace_add('write', update_label)
        update_label()

    def update_image_label(self):
        if self.parent_gui.image_path:
            display_name = os.path.basename(self.parent_gui.image_path)
            self.image_label.config(text=f"✓ {display_name}", fg=COLORS['success'])
        else:
            self.image_label.config(text="No image selected", fg=COLORS['text_dim'])

class MacroGUI:
    def __init__(self, root):
        self.root = root

        self.screenshot_lock = threading.Lock()
        self.screenshot_dir = os.path.join(os.path.dirname(__file__), "screenshots")
        os.makedirs(self.screenshot_dir, exist_ok=True)

        self.owobuy_cooldown = tk.DoubleVar(root, value=5.0)
        self.owo_enabled = tk.BooleanVar(root, value=True)
        self.use_slash_hunt_battle = tk.BooleanVar(root, value=False)
        self.owo_cooldown = tk.DoubleVar(root, value=10.0)
        self.owoh_owob_cooldown = tk.DoubleVar(root, value=15.0)
        self.command_variance = tk.DoubleVar(root, value=0.15)
        self.typing_delay_min = tk.DoubleVar(root, value=0.01)
        self.typing_delay_max = tk.DoubleVar(root, value=0.05)
        self.typing_pause_min = tk.DoubleVar(root, value=0.2)
        self.typing_pause_max = tk.DoubleVar(root, value=0.5)
        self.random_enabled = tk.BooleanVar(root, value=True)
        self.owobuy_enabled = tk.BooleanVar(root, value=True)
        self.window_name = tk.StringVar(root, value="Discord")

        self.running = False
        self.paused = False
        self.pause_lock = threading.RLock()

        self.start_lock = threading.Lock()
        self.countdown_thread = None

        self.threads = []
        self.image_path = ""

        self.lifetime_stats = {
            'commands_sent': 0,
            'owobuy': 0,
            'owo': 0,
            'owoh': 0,
            'owob': 0,
            'antibot_detections': 0
        }
        self.stats = {
            'cycles': 0,
            'commands_sent': 0,
            'start_time': None,
            'owobuy': 0,
            'owo': 0,
            'owoh': 0,
            'owob': 0,
            'antibot_detections': 0
        }

        self.load_settings()
        self.control_panel = FloatingControlPanel(self, root)

        global _APP_INSTANCE
        with _APP_LOCK:
            _APP_INSTANCE = self
            try:
                for msg, lvl in _BUFFERED_LOGS:
                    try:
                        self.log(msg, lvl)
                    except Exception:
                        pass
                _BUFFERED_LOGS.clear()
            except Exception:
                pass

        self.scheduler = CommandScheduler()
        self.scheduler.gui = self
        self.stop_event = threading.Event()

        try:
            pyautogui.FAILSAFE = False
            pyautogui.PAUSE = 0.1
            _ = pyautogui.position()
            self.log("PyAutoGUI initialized successfully", "info")
        except Exception as e:
            self.log(f"PyAutoGUI initialization warning: {e}", "warning")

        if OCR_AVAILABLE:
            self.log("OCR antibot detection enabled", "success")
        else:
            self.log("OCR not available - using image matching fallback", "warning")
        
        self.log(f"Screenshots will be saved to: {self.screenshot_dir}", "info")

    def log(self, message, level="info"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

        if hasattr(self, 'control_panel'):
            try:
                self.control_panel.add_log(message, level)
            except:
                pass

    def select_image(self, callback=None):
        filename = filedialog.askopenfilename(
            title="Select Detection Image",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        if filename:
            self.image_path = filename
            self.log(f"Image selected: {os.path.basename(filename)}", "success")
            if callback:
                callback()

    def pause_macro(self):
        if not self.running:
            return
        with self.pause_lock:
            self.paused = not self.paused
            if self.paused:
                self.control_panel.update_status("Paused", COLORS['warning'])
                self.log("Macro paused", "warning")
            else:
                self.control_panel.update_status("Running", COLORS['success'])
                self.log("Resuming in 3 seconds...", "warning")
                for i in range(3, 0, -1):
                    if not self.running:
                        return
                    self.log(f"{i}...", "warning")
                    time.sleep(1)
                self.log("Macro resumed", "success")

    def start_macro(self):
        if not self.image_path or not os.path.exists(self.image_path):
            messagebox.showerror("Error", "Please select a valid image!")
            return
        if not self.start_lock.acquire(blocking=False):
            self.log("Start already in progress, please wait...", "warning")
            return
        try:
            if self.running:
                self.log("Macro is already running", "warning")
                return
            if self.countdown_thread and self.countdown_thread.is_alive():
                self.log("Waiting for previous countdown to finish...", "warning")
                self.stop_event.set()
                self.countdown_thread.join(timeout=5)
            self.running = True
            self.paused = False
            self.stop_event.clear()
            self.stats['start_time'] = time.time()
            self.control_panel.start_btn.set_enabled(False)
            self.control_panel.pause_btn.set_enabled(True)
            self.control_panel.stop_btn.set_enabled(True)
            self.control_panel.update_status("Running", COLORS['success'])
            self.log("Macro started - Multithreaded mode active", "success")
            self.save_settings()
            self.countdown_thread = threading.Thread(target=self.start_with_countdown, daemon=True)
            self.countdown_thread.start()
        finally:
            self.start_lock.release()

    def start_with_countdown(self):
        self.log("Starting in 3 seconds... Click into Discord window!", "warning")
        for i in range(3, 0, -1):
            if not self.running or self.stop_event.is_set():
                self.log("Countdown cancelled", "warning")
                return
            self.log(f"{i}...", "warning")
            time.sleep(1)
        if not self.running or self.stop_event.is_set():
            self.log("Start cancelled after countdown", "warning")
            return
        for thread in self.threads:
            if thread.is_alive():
                self.log("Warning: Old thread still running, waiting...", "warning")
        self.threads = []
        if self.owo_enabled.get():
            self.threads.append(threading.Thread(target=self.owo_loop, name="owo-thread", daemon=True))
        self.threads.append(threading.Thread(target=self.owoh_owob_loop, name="owoh-owob-thread", daemon=True))
        if self.owobuy_enabled.get():
            self.threads.insert(0, threading.Thread(target=self.owobuy_loop, name="owobuy-thread", daemon=True))
        if not self.running or self.stop_event.is_set():
            self.log("Start cancelled before thread launch", "warning")
            return
        for thread in self.threads:
            thread.start()
        self.log("All command threads started", "success")

    def stop_macro(self):
        self.running = False
        self.stop_event.set()
        self.paused = False
        try:
            # Clean up screenshots in local directory
            for pattern in ['macro_screenshot_*', 'antibot_ss.png']:
                for f in glob.glob(os.path.join(self.screenshot_dir, pattern)):
                    try:
                        if os.path.exists(f):
                            os.remove(f)
                    except Exception:
                        pass
        except Exception:
            pass
        self.log("Stopping macro... waiting for threads to exit.", "warning")
        self.control_panel.start_btn.set_enabled(True)
        self.control_panel.pause_btn.set_enabled(False)
        self.control_panel.pause_btn.text = "Pause"
        self.control_panel.pause_btn.draw_button()
        self.control_panel.stop_btn.set_enabled(False)
        self.control_panel.update_status("Stopped", COLORS['danger'])
        self.stats['start_time'] = None
        self.threads = []
        self.log("Macro stopped (threads exiting in background)", "error")
        self.save_settings()

    def is_correct_window_active(self):
        try:
            cmd = ["xdotool", "getactivewindow", "getwindowname"]
            window_name = subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode().strip()
            target = self.window_name.get().lower().strip()
            if not target:
                return True
            return target in window_name.lower()
        except Exception:
            return True

    def capture_screenshot(self, max_total_wait=10.0, retry_delay=0.5):
        with self.screenshot_lock:
            start_time = time.time()
    
            while time.time() - start_time < max_total_wait:
                try:
                    prefix = f"temp_screenshot_{int(time.time())}"
                    base_path = os.path.join(self.screenshot_dir, prefix + ".png")
                    pattern = os.path.join(self.screenshot_dir, prefix + "*.png")
    
                    subprocess.run(
                        ["scrot", base_path],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        timeout=2,
                    )
    
                    matches = glob.glob(pattern)
                    if matches:
                        latest = max(matches, key=os.path.getmtime)
    
                        img = Image.open(latest)
                        img_copy = img.copy()
                        img.close()
    
                        # Cleanup — race-safe
                        for f in matches:
                            try:
                                os.remove(f)
                            except FileNotFoundError:
                                pass
                            except Exception as e:
                                self.log(f"Screenshot cleanup warning: {e}", "warning")
    
                        return img_copy
    
                except Exception:
                    pass
                
                time.sleep(retry_delay)
    
            self.log(
                f"Screenshot unavailable after {max_total_wait}s, will retry later.",
                "warning",
            )
            return None


    def detect_antibot(self):
        use_ocr = OCR_AVAILABLE
        if use_ocr:
            return self.detect_antibot_ocr()
        else:
            return self.detect_antibot_image()

    def detect_antibot_ocr(self):
        try:
            screenshot = self.capture_screenshot()
            if screenshot is None:
                return False
            
            screenshot_gray = screenshot.convert('L')
            text = pytesseract.image_to_string(screenshot_gray, lang='eng')
            text_normalized = re.sub(r'\s+', ' ', text.lower().strip())
            
            antibot_patterns = [
                r'\bare\s+you\s+a\s+real\s+human\b',
                r'\bplease\s+use\s+the\s+link\s+below\b',
                r'\bplease\s+complete\s+this\s+within\s+10\s+minutes\b',
                r'https?://owobot\.com/captcha',
                r'\bplease\s+complete\s+your\s+captcha\s+to\s+verify\b'
            ]
            
            found = False
            matched_pattern = None
            for pattern in antibot_patterns:
                if re.search(pattern, text_normalized):
                    found = True
                    matched_pattern = pattern
                    break
            
            if found:
                self.stats['antibot_detections'] += 1
                self.lifetime_stats['antibot_detections'] += 1
                self.log(f"⚠ Anti-bot detected (OCR found: '{matched_pattern}')! Pausing macro.", "warning")
                return True
            return False
        except Exception as e:
            self.log(f"Error in OCR anti-bot detection: {e}", "error")
            traceback.print_exc()
            return False

    def detect_antibot_image(self):
        if not self.image_path or not os.path.exists(self.image_path):
            return False
        try:
            screenshot = self.capture_screenshot()
            if screenshot is None:
                return False
            
            template = Image.open(self.image_path)
            screen_array = np.array(screenshot)
            template_array = np.array(template)
            screen_h, screen_w = screen_array.shape[:2]
            template_h, template_w = template_array.shape[:2]
            found = False
            best_similarity = 0
            
            for scale in [0.8, 0.9, 1.0, 1.1, 1.2]:
                new_w = int(template_w * scale)
                new_h = int(template_h * scale)
                if new_w > screen_w or new_h > screen_h or new_w < 10 or new_h < 10:
                    continue
                resized_template = template.resize((new_w, new_h), Image.LANCZOS)
                template_resized_array = np.array(resized_template)
                step = 30
                margin = 50
                for y in range(margin, screen_h - new_h - margin, step):
                    for x in range(margin, screen_w - new_w - margin, step):
                        region = screen_array[y:y+new_h, x:x+new_w]
                        if region.shape == template_resized_array.shape:
                            diff = np.abs(region.astype(float) - template_resized_array.astype(float))
                            similarity = 1.0 - (np.mean(diff) / 255.0)
                            if similarity > best_similarity:
                                best_similarity = similarity
                            if similarity > 0.80:
                                found = True
                                break
                    if found:
                        break
                if found:
                    break
            
            if found:
                self.stats['antibot_detections'] += 1
                self.lifetime_stats['antibot_detections'] += 1
                self.log("⚠ Anti-bot popup detected! Pausing macro.", "warning")
                return True
            return False
        except Exception as e:
            self.log(f"Error in anti-bot detection: {e}", "error")
            traceback.print_exc()
            return False

    def wait_if_paused(self):
        with self.pause_lock:
            return not self.paused

    def send_command(self, text, command_type):
        if not self.running:
            return False
        with self.pause_lock:
            if self.paused or not self.running:
                return False
        if not self.is_correct_window_active():
            self.log(f"[{command_type}] Target window not active; skipping send.", "warning")
            return False
        if self.detect_antibot():
            self.log(f"[{command_type}] Anti-bot detected! Pausing macro.", "warning")
            with self.pause_lock:
                self.paused = True
            return False
        acquired = send_lock.acquire(timeout=5)
        if not acquired:
            self.log(f"[{command_type}] Failed to acquire send lock", "warning")
            return False
        try:
            with self.pause_lock:
                if self.paused or not self.running:
                    return False
            if not self.scheduler.wait_for_slot(timeout=10):
                self.log(f"[{command_type}] Scheduler timeout", "warning")
                return False

            self.scheduler.humanize_typing(text)

            final_pause = random.uniform(0.3, 0.5)
            time.sleep(final_pause)

            try:
                if platform.system() == 'Linux':
                    subprocess.run(['xdotool', 'key', 'Return'], check=True)
                else:
                    pyautogui.press('enter')
            except Exception as e:
                self.log(f"[{command_type}] Enter key error: {e}", "error")
                try:
                    pyautogui.press('enter')
                except:
                    pass

            time.sleep(0.2)

            self.stats['commands_sent'] += 1
            self.lifetime_stats['commands_sent'] += 1
            if command_type in self.lifetime_stats:
                self.lifetime_stats[command_type] += 1
            if command_type in self.stats:
                self.stats[command_type] += 1
            self.save_settings()
            return True
        except Exception as e:
            self.log(f"[{command_type}] Error: {str(e)}", "error")
            return False
        finally:
            send_lock.release()

    def owobuy_loop(self):
        self.log("[owobuy] Thread started", "info")
        while self.running and not self.stop_event.is_set():
            try:
                while self.running and not self.wait_if_paused():
                    time.sleep(0.1)
                    if self.stop_event.is_set():
                        break
                if not self.running or self.stop_event.is_set():
                    break
                if not self.is_correct_window_active():
                    self.log("[owobuy] Target window not active; waiting...", "warning")
                    while self.running and not self.stop_event.is_set() and not self.is_correct_window_active():
                        time.sleep(0.5)
                    continue
                if self.detect_antibot():
                    with self.pause_lock:
                        self.paused = True
                    time.sleep(1)
                    continue
                if self.send_command("owo buy 1", "owobuy"):
                    self.log("[owobuy] Sent: owo buy 1", "command")
                else:
                    time.sleep(1)
                    continue
                delay = self.scheduler.humanize_delay(self.owobuy_cooldown.get())
                self.log(f"[owobuy] Waiting {delay:.2f}s", "info")
                wait_steps = int(delay * 10)
                for step in range(wait_steps):
                    if not self.running or self.stop_event.is_set():
                        break
                    time.sleep(0.1)
            except Exception as e:
                self.log(f"[owobuy] Error: {str(e)}", "error")
                time.sleep(1)
        self.log("[owobuy] Thread stopped", "info")

    def owo_loop(self):
        self.log("[owo] Thread started", "info")
        while self.running and not self.stop_event.is_set():
            try:
                while self.running and not self.wait_if_paused():
                    time.sleep(0.1)
                    if self.stop_event.is_set():
                        break
                if not self.running or self.stop_event.is_set():
                    break
                if not self.is_correct_window_active():
                    self.log("[owo] Target window not active; waiting...", "warning")
                    while self.running and not self.stop_event.is_set() and not self.is_correct_window_active():
                        time.sleep(0.5)
                    continue
                if self.detect_antibot():
                    with self.pause_lock:
                        self.paused = True
                    time.sleep(1)
                    continue
                if self.send_command("owo", "owo"):
                    self.log("[owo] Sent: owo", "command")
                else:
                    time.sleep(1)
                    continue
                delay = self.scheduler.humanize_delay(self.owo_cooldown.get())
                self.log(f"[owo] Waiting {delay:.2f}s", "info")
                wait_steps = int(delay * 10)
                for step in range(wait_steps):
                    if not self.running or self.stop_event.is_set():
                        break
                    time.sleep(0.1)
            except Exception as e:
                self.log(f"[owo] Error: {str(e)}", "error")
                time.sleep(1)
        self.log("[owo] Thread stopped", "info")

    def owoh_owob_loop(self):
        self.log("[owoh-owob] Thread started", "info")
        while self.running and not self.stop_event.is_set():
            try:
                while self.running and not self.wait_if_paused():
                    time.sleep(0.1)
                    if self.stop_event.is_set():
                        break
                if not self.running or self.stop_event.is_set():
                    break
                if not self.is_correct_window_active():
                    self.log("[owoh-owob] Target window not active; waiting...", "warning")
                    while self.running and not self.stop_event.is_set() and not self.is_correct_window_active():
                        time.sleep(0.5)
                    continue
                if self.detect_antibot():
                    with self.pause_lock:
                        self.paused = True
                    time.sleep(1)
                    continue
                cmd1 = "/hunt" if self.use_slash_hunt_battle.get() else "owoh"
                if self.send_command(cmd1, "owoh"):
                    self.log(f"[owoh-owob] Sent: {cmd1}", "command")
                else:
                    time.sleep(1)
                    continue
                pair_gap = random.uniform(0.8, 1.5)
                time.sleep(pair_gap)
                cmd2 = "/battle" if self.use_slash_hunt_battle.get() else "owob"
                if self.send_command(cmd2, "owob"):
                    self.log(f"[owoh-owob] Sent: {cmd2}", "command")
                else:
                    time.sleep(1)
                    continue
                delay = self.scheduler.humanize_delay(self.owoh_owob_cooldown.get())
                self.log(f"[owoh-owob] Waiting {delay:.2f}s", "info")
                wait_steps = int(delay * 10)
                for step in range(wait_steps):
                    if not self.running or self.stop_event.is_set():
                        break
                    time.sleep(0.1)
            except Exception as e:
                self.log(f"[owoh-owob] Error: {str(e)}", "error")
                time.sleep(1)
        self.log("[owoh-owob] Thread stopped", "info")

    SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "settings.json")

    def load_settings(self):
        if os.path.exists(self.SETTINGS_FILE):
            try:
                with open(self.SETTINGS_FILE, "r") as f:
                    data = json.load(f)
                self.owobuy_cooldown.set(max(1.0, min(30.0, data.get("owobuy_cooldown", 5.0))))
                self.owo_cooldown.set(max(1.0, min(60.0, data.get("owo_cooldown", 10.0))))
                self.owoh_owob_cooldown.set(max(1.0, min(60.0, data.get("owoh_owob_cooldown", 15.0))))
                self.random_enabled.set(bool(data.get("random_enabled", True)))
                self.owobuy_enabled.set(bool(data.get("owobuy_enabled", True)))
                self.owo_enabled.set(bool(data.get("owo_enabled", True)))
                self.use_slash_hunt_battle.set(bool(data.get("use_slash_hunt_battle", False)))
                self.command_variance.set(float(data.get("command_variance", 0.15)))
                self.typing_delay_min.set(float(data.get("typing_delay_min", 0.01)))
                self.typing_delay_max.set(float(data.get("typing_delay_max", 0.05)))
                self.typing_pause_min.set(float(data.get("typing_pause_min", 0.2)))
                self.typing_pause_max.set(float(data.get("typing_pause_max", 0.5)))
                self.window_name.set(str(data.get("window_name", "Discord")))
                if "image_path" in data and os.path.exists(data["image_path"]):
                    self.image_path = data["image_path"]
                if "lifetime_stats" in data:
                    for key in self.lifetime_stats.keys():
                        self.lifetime_stats[key] = max(0, int(data["lifetime_stats"].get(key, 0)))
                self.log("Settings loaded successfully", "info")
            except Exception as e:
                self.log(f"Failed to load settings: {e}", "warning")

    def save_settings(self):
        data = {
            "owobuy_cooldown": self.owobuy_cooldown.get(),
            "owo_cooldown": self.owo_cooldown.get(),
            "owoh_owob_cooldown": self.owoh_owob_cooldown.get(),
            "random_enabled": self.random_enabled.get(),
            "owobuy_enabled": self.owobuy_enabled.get(),
            "owo_enabled": self.owo_enabled.get(),
            "use_slash_hunt_battle": self.use_slash_hunt_battle.get(),
            "command_variance": self.command_variance.get(),
            "typing_delay_min": self.typing_delay_min.get(),
            "typing_delay_max": self.typing_delay_max.get(),
            "typing_pause_min": self.typing_pause_min.get(),
            "typing_pause_max": self.typing_pause_max.get(),
            "window_name": self.window_name.get(),
            "image_path": self.image_path,
            "lifetime_stats": self.lifetime_stats
        }
        try:
            os.makedirs(os.path.dirname(self.SETTINGS_FILE), exist_ok=True)
            temp_file = self.SETTINGS_FILE + ".tmp"
            with open(temp_file, "w") as f:
                json.dump(data, f, indent=2)
            shutil.move(temp_file, self.SETTINGS_FILE)
        except Exception as e:
            self.log(f"Failed to save settings: {e}", "warning")

    def on_close(self):
        self.running = False
        self.stop_event.set()
        self.save_settings()
        self.root.destroy()

def main():
    try:
        root = tk.Tk()
        app = MacroGUI(root)
        root.protocol('WM_DELETE_WINDOW', app.on_close)
        root.mainloop()
    except Exception as e:
        app_log(f"Fatal error: {e}", "error")
        traceback.print_exc()

if __name__ == "__main__":
    app_log("=== Starting OwO Bot Macro ===", "info")
    app_log(f"Python version: {sys.version}", "info")
    app_log(f"Platform: {platform.system()}", "info")
    main()

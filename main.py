import ctypes
import json
import os
import sys
import time
import customtkinter as ctk
from tkinter import colorchooser, messagebox

try:
    import winreg
except ImportError:
    winreg = None

APP_NAME = "Aero"
CONFIG_FILE = "config.json"

user32 = ctypes.windll.user32
GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
LWA_ALPHA = 0x00000002

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

def base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def cfg_path():
    return os.path.join(base_dir(), CONFIG_FILE)

def log_path():
    return os.path.join(base_dir(), "aero.log")

def write_log(msg):
    stamp = time.strftime("%H:%M:%S")
    line = f"[{stamp}] {msg}\n"
    try:
        with open(log_path(), "a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        pass
    if "app" in globals() and hasattr(app, "log_box"):
        app.log_box.insert("end", line)
        app.log_box.see("end")

def load_cfg():
    data = {"alpha": 220, "tint": "#ffffff", "autostart": False}
    try:
        with open(cfg_path(), "r", encoding="utf-8") as f:
            data.update(json.load(f))
    except Exception:
        pass
    return data

def save_cfg(data):
    with open(cfg_path(), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def enum_windows():
    hwnds = []
    @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
    def callback(hwnd, lparam):
        if user32.IsWindowVisible(hwnd):
            cls = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(hwnd, cls, 256)
            if cls.value == "CabinetWClass":
                hwnds.append(hwnd)
        return True
    user32.EnumWindows(callback, 0)
    return hwnds

def apply_transparency(alpha):
    count = 0
    for hwnd in enum_windows():
        exstyle = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, exstyle | WS_EX_LAYERED)
        user32.SetLayeredWindowAttributes(hwnd, 0, int(alpha), LWA_ALPHA)
        count += 1
    return count

def clear_transparency():
    count = 0
    for hwnd in enum_windows():
        exstyle = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, exstyle & ~WS_EX_LAYERED)
        count += 1
    return count

def get_startup_command():
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"'
    return f'"{sys.executable}" "{os.path.abspath(__file__)}"'

def add_startup():
    if not winreg:
        return False
    try:
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER,
                               r"Software\Microsoft\Windows\CurrentVersion\Run")
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, get_startup_command())
        winreg.CloseKey(key)
        write_log(f"Startup set: {get_startup_command()}")
        return True
    except Exception as e:
        write_log(f"Startup enable failed: {e}")
        return False

def remove_startup():
    if not winreg:
        return False
    try:
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER,
                               r"Software\Microsoft\Windows\CurrentVersion\Run")
        try:
            winreg.DeleteValue(key, APP_NAME)
            write_log("Startup removed")
        except FileNotFoundError:
            write_log("Startup entry not found")
        winreg.CloseKey(key)
        return True
    except Exception as e:
        write_log(f"Startup disable failed: {e}")
        return False

cfg = load_cfg()

class AeroApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        global app
        app = self

        self.title(APP_NAME)
        self.geometry("760x560")
        self.minsize(760, 560)
        self.resizable(False, False)

        self.alpha = ctk.IntVar(value=int(cfg.get("alpha", 220)))
        self.tint = ctk.StringVar(value=str(cfg.get("tint", "#ffffff")))
        self.autostart = ctk.BooleanVar(value=bool(cfg.get("autostart", False)))

        self.build_ui()
        self.after(300, self.apply)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        write_log("App started")

    def build_ui(self):
        root = ctk.CTkFrame(self, corner_radius=18, fg_color="#f3f6fb")
        root.pack(fill="both", expand=True, padx=16, pady=16)

        ctk.CTkLabel(root, text="Aero", font=ctk.CTkFont(size=28, weight="bold")).pack(anchor="w", padx=18, pady=(18, 0))
        ctk.CTkLabel(root, text="Light theme transparency control").pack(anchor="w", padx=18, pady=(0, 16))

        panel = ctk.CTkFrame(root, corner_radius=14, fg_color="#ffffff")
        panel.pack(fill="x", padx=18, pady=(0, 12))

        ctk.CTkLabel(panel, text="Transparency", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=14, pady=(12, 0))
        self.slider = ctk.CTkSlider(panel, from_=0, to=255, number_of_steps=255, command=self.on_slider)
        self.slider.set(self.alpha.get())
        self.slider.pack(fill="x", padx=14, pady=(6, 4))

        self.opacity_value = ctk.CTkLabel(panel, text=str(self.alpha.get()))
        self.opacity_value.pack(anchor="w", padx=14, pady=(0, 12))

        ctk.CTkLabel(panel, text="Color", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=14, pady=(4, 0))
        row = ctk.CTkFrame(panel, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=10)

        self.tint_entry = ctk.CTkEntry(row, textvariable=self.tint)
        self.tint_entry.pack(side="left", fill="x", expand=True)

        ctk.CTkButton(row, text="Palette", width=100, command=self.pick_color).pack(side="left", padx=(10, 0))

        controls = ctk.CTkFrame(panel, fg_color="transparent")
        controls.pack(fill="x", padx=14, pady=(0, 14))

        self.start_btn = ctk.CTkSwitch(controls, text="Start with Windows", command=self.toggle_startup)
        self.start_btn.pack(side="left")
        if self.autostart.get():
            self.start_btn.select()

        ctk.CTkButton(controls, text="Apply", command=self.apply, width=120).pack(side="right")
        ctk.CTkButton(controls, text="Clear", command=self.clear, width=120).pack(side="right", padx=8)

        log_panel = ctk.CTkFrame(root, corner_radius=14, fg_color="#ffffff")
        log_panel.pack(fill="both", expand=True, padx=18, pady=(0, 18))

        ctk.CTkLabel(log_panel, text="Log", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=14, pady=(12, 6))
        self.log_box = ctk.CTkTextbox(log_panel)
        self.log_box.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        self.status = ctk.CTkLabel(root, text="Ready")
        self.status.pack(anchor="w", padx=18, pady=(0, 12))

    def on_slider(self, value):
        self.opacity_value.configure(text=str(int(float(value))))

    def pick_color(self):
        c = colorchooser.askcolor(initialcolor=self.tint.get())[1]
        if c:
            self.tint.set(c)
            write_log(f"Color selected: {c}")

    def toggle_startup(self):
        self.autostart.set(not self.autostart.get())
        if self.autostart.get():
            ok = add_startup()
            self.status.configure(text="Startup enabled" if ok else "Startup enable failed")
        else:
            ok = remove_startup()
            self.status.configure(text="Startup disabled" if ok else "Startup disable failed")

    def apply(self):
        try:
            alpha = int(float(self.slider.get()))
            save_cfg({"alpha": alpha, "tint": self.tint.get(), "autostart": self.autostart.get()})
            if self.autostart.get():
                add_startup()
            else:
                remove_startup()
            count = apply_transparency(alpha)
            msg = f"Transparency applied to {count} Explorer windows"
            self.status.configure(text=msg)
            write_log(msg)
        except Exception as e:
            write_log(f"Apply failed: {e}")
            messagebox.showerror(APP_NAME, str(e))

    def clear(self):
        try:
            count = clear_transparency()
            msg = f"Transparency cleared from {count} Explorer windows"
            self.status.configure(text=msg)
            write_log(msg)
        except Exception as e:
            write_log(f"Clear failed: {e}")
            messagebox.showerror(APP_NAME, str(e))

    def on_close(self):
        save_cfg({"alpha": int(float(self.slider.get())), "tint": self.tint.get(), "autostart": self.autostart.get()})
        write_log("App closed")
        self.destroy()

if __name__ == "__main__":
    app = AeroApp()
    app.mainloop()

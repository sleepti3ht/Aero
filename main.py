import ctypes
import json
import os
import subprocess
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

ctypes.windll.user32.SetWindowCompositionAttribute.restype = ctypes.c_bool

ACCENT_ENABLE_GRADIENT = 1
ACCENT_ENABLE_TRANSPARENTGRADIENT = 2
ACCENT_ENABLE_BLURBEHIND = 3
ACCENT_ENABLE_ACRYLICBLURBEHIND = 4
WCA_ACCENT_POLICY = 19

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class ACCENT_POLICY(ctypes.Structure):
    _fields_ = [
        ("AccentState", ctypes.c_uint),
        ("AccentFlags", ctypes.c_uint),
        ("GradientColor", ctypes.c_uint),
        ("AnimationId", ctypes.c_uint),
    ]

class WINDOWCOMPOSITIONATTRIBDATA(ctypes.Structure):
    _fields_ = [
        ("Attribute", ctypes.c_uint),
        ("Data", ctypes.c_void_p),
        ("SizeOfData", ctypes.c_size_t),
    ]

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
    data = {"alpha": 140, "tint": "#50f2f2f2", "autostart": False}
    try:
        with open(cfg_path(), "r", encoding="utf-8") as f:
            data.update(json.load(f))
    except Exception:
        pass
    return data

def save_cfg(data):
    with open(cfg_path(), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def rgb_to_abgr(color_hex, alpha):
    color_hex = color_hex.lstrip("#")
    if len(color_hex) == 8:
        color_hex = color_hex[2:]
    r = int(color_hex[0:2], 16)
    g = int(color_hex[2:4], 16)
    b = int(color_hex[4:6], 16)
    return (int(alpha) << 24) | (b << 16) | (g << 8) | r

def apply_acrylic_to_hwnd(hwnd, color_hex, alpha):
    accent = ACCENT_POLICY()
    accent.AccentState = ACCENT_ENABLE_ACRYLICBLURBEHIND
    accent.AccentFlags = 2
    accent.GradientColor = rgb_to_abgr(color_hex, alpha)
    accent.AnimationId = 0

    data = WINDOWCOMPOSITIONATTRIBDATA()
    data.Attribute = WCA_ACCENT_POLICY
    data.Data = ctypes.cast(ctypes.pointer(accent), ctypes.c_void_p)
    data.SizeOfData = ctypes.sizeof(accent)

    return user32.SetWindowCompositionAttribute(hwnd, ctypes.byref(data))

def get_self_hwnd():
    return int(app.winfo_id())

def add_startup():
    if not winreg:
        return False
    try:
        exe = sys.executable if getattr(sys, "frozen", False) else f'"{sys.executable}" "{os.path.abspath(__file__)}"'
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r"Software\Microsoft\Windows\CurrentVersion\Run",
                             0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, exe)
        winreg.CloseKey(key)
        return True
    except Exception as e:
        write_log(f"Startup enable failed: {e}")
        return False

def remove_startup():
    if not winreg:
        return False
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r"Software\Microsoft\Windows\CurrentVersion\Run",
                             0, winreg.KEY_SET_VALUE)
        winreg.DeleteValue(key, APP_NAME)
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

        self.alpha = ctk.IntVar(value=int(cfg.get("alpha", 140)))
        self.tint = ctk.StringVar(value=str(cfg.get("tint", "#50f2f2f2")))
        self.autostart = ctk.BooleanVar(value=bool(cfg.get("autostart", False)))

        self.build_ui()
        self.after(300, self.apply_effect)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        write_log("App started")

    def build_ui(self):
        root = ctk.CTkFrame(self, corner_radius=18)
        root.pack(fill="both", expand=True, padx=16, pady=16)

        ctk.CTkLabel(root, text="Aero", font=ctk.CTkFont(size=28, weight="bold")).pack(anchor="w", padx=18, pady=(18, 0))
        ctk.CTkLabel(root, text="Acrylic + GradientColor test window").pack(anchor="w", padx=18, pady=(0, 16))

        top = ctk.CTkFrame(root, corner_radius=14)
        top.pack(fill="x", padx=18, pady=(0, 12))

        ctk.CTkLabel(top, text="Opacity", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=14, pady=(12, 0))
        self.slider = ctk.CTkSlider(top, from_=0, to=255, number_of_steps=255, command=self.on_slider)
        self.slider.set(self.alpha.get())
        self.slider.pack(fill="x", padx=14, pady=(6, 4))

        self.opacity_value = ctk.CTkLabel(top, text=str(self.alpha.get()))
        self.opacity_value.pack(anchor="w", padx=14, pady=(0, 12))

        ctk.CTkLabel(top, text="Tint color", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=14, pady=(4, 0))
        row = ctk.CTkFrame(top, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=10)

        self.tint_entry = ctk.CTkEntry(row, textvariable=self.tint)
        self.tint_entry.pack(side="left", fill="x", expand=True)

        ctk.CTkButton(row, text="Palette", width=100, command=self.pick_color).pack(side="left", padx=(10, 0))

        controls = ctk.CTkFrame(top, fg_color="transparent")
        controls.pack(fill="x", padx=14, pady=(0, 14))

        self.start_btn = ctk.CTkSwitch(controls, text="Start with Windows", command=self.toggle_startup)
        self.start_btn.pack(side="left")
        if self.autostart.get():
            self.start_btn.select()

        ctk.CTkButton(controls, text="Apply", command=self.apply_effect, width=120).pack(side="right")
        ctk.CTkButton(controls, text="Clear", command=self.clear_effect, width=120).pack(side="right", padx=8)

        log_panel = ctk.CTkFrame(root, corner_radius=14)
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
            write_log(f"Tint selected: {c}")

    def toggle_startup(self):
        self.autostart.set(not self.autostart.get())
        if self.autostart.get():
            ok = add_startup()
            self.status.configure(text="Startup enabled" if ok else "Startup enable failed")
        else:
            ok = remove_startup()
            self.status.configure(text="Startup disabled" if ok else "Startup disable failed")

    def apply_effect(self):
        try:
            alpha = int(float(self.slider.get()))
            tint = self.tint.get().strip()
            if not tint.startswith("#") or len(tint) not in (7, 9):
                raise ValueError("Tint color must be like #RRGGBB or #AARRGGBB")
            hwnd = get_self_hwnd()
            ok = apply_acrylic_to_hwnd(hwnd, tint, alpha)
            save_cfg({"alpha": alpha, "tint": tint, "autostart": self.autostart.get()})
            if self.autostart.get():
                add_startup()
            else:
                remove_startup()
            msg = f"Acrylic applied: {bool(ok)} | alpha={alpha} | tint={tint}"
            self.status.configure(text=msg)
            write_log(msg)
        except Exception as e:
            write_log(f"Apply failed: {e}")
            messagebox.showerror(APP_NAME, str(e))

    def clear_effect(self):
        try:
            hwnd = get_self_hwnd()
            accent = ACCENT_POLICY()
            accent.AccentState = 0
            accent.AccentFlags = 0
            accent.GradientColor = 0
            accent.AnimationId = 0
            data = WINDOWCOMPOSITIONATTRIBDATA()
            data.Attribute = WCA_ACCENT_POLICY
            data.Data = ctypes.cast(ctypes.pointer(accent), ctypes.c_void_p)
            data.SizeOfData = ctypes.sizeof(accent)
            user32.SetWindowCompositionAttribute(hwnd, ctypes.byref(data))
            self.status.configure(text="Effect cleared")
            write_log("Effect cleared")
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
import ctypes
import json
import os
import sys
import time
import customtkinter as ctk
from tkinter import messagebox

try:
    import winreg
except ImportError:
    winreg = None

APP_NAME = "Aero"
CONFIG_FILE = "config.json"
LOG_FILE = "aero.log"
ICON_FILE = "icon.ico"

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

user32 = ctypes.windll.user32
GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
LWA_ALPHA = 0x00000002


def resource_path(relative_path):
    if getattr(sys, "frozen", False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


def base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def cfg_path():
    return os.path.join(base_dir(), CONFIG_FILE)


def log_path():
    return os.path.join(base_dir(), LOG_FILE)


def write_log(msg):
    stamp = time.strftime("%H:%M:%S")
    line = f"[{stamp}] {msg}\n"
    try:
        with open(log_path(), "a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        pass


def load_cfg():
    data = {"alpha": 220, "autostart": False}
    try:
        with open(cfg_path(), "r", encoding="utf-8") as f:
            data.update(json.load(f))
    except Exception:
        pass
    return data


def save_cfg(data):
    with open(cfg_path(), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def apply_opacity(hwnd, alpha):
    exstyle = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    user32.SetWindowLongW(hwnd, GWL_EXSTYLE, exstyle | WS_EX_LAYERED)
    return user32.SetLayeredWindowAttributes(hwnd, 0, int(alpha), LWA_ALPHA)


def clear_opacity(hwnd):
    exstyle = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    user32.SetWindowLongW(hwnd, GWL_EXSTYLE, exstyle & ~WS_EX_LAYERED)


def enum_explorer_windows():
    hwnds = []
    excludes = {user32.GetShellWindow(), user32.FindWindowW("Shell_TrayWnd", None)}

    @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
    def callback(hwnd, lparam):
        if hwnd in excludes:
            return True
        if not user32.IsWindowVisible(hwnd):
            return True
        cls = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, cls, 256)
        if cls.value in ("CabinetWClass", "ExplorerWClass"):
            hwnds.append(hwnd)
        return True

    user32.EnumWindows(callback, 0)
    return hwnds


def get_startup_command():
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"'
    return f'"{sys.executable}" "{os.path.abspath(__file__)}"'


def add_startup():
    if not winreg:
        return False
    try:
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run")
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, get_startup_command())
        winreg.CloseKey(key)
        return True
    except Exception:
        return False


def remove_startup():
    if not winreg:
        return False
    try:
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run")
        try:
            winreg.DeleteValue(key, APP_NAME)
        except FileNotFoundError:
            pass
        winreg.CloseKey(key)
        return True
    except Exception:
        return False


cfg = load_cfg()


class AeroApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        global app
        app = self

        icon_path = resource_path(ICON_FILE)
        try:
            self.iconbitmap(icon_path)
        except Exception:
            pass

        self.title("Aero")
        self.geometry("700x340")
        self.minsize(700, 340)
        self.resizable(False, False)

        self.alpha_var = ctk.IntVar(value=int(cfg.get("alpha", 220)))
        self.autostart_var = ctk.BooleanVar(value=bool(cfg.get("autostart", False)))

        self.build_ui()
        self.after(300, self.apply_effect)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def build_ui(self):
        outer = ctk.CTkFrame(self, corner_radius=18)
        outer.pack(fill="both", expand=True, padx=16, pady=16)

        ctk.CTkLabel(outer, text="Aero", font=ctk.CTkFont(size=28, weight="bold")).pack(anchor="w", padx=18, pady=(18, 0))
        ctk.CTkLabel(outer, text="Explorer opacity controller").pack(anchor="w", padx=18, pady=(0, 14))

        card = ctk.CTkFrame(outer, corner_radius=14)
        card.pack(fill="x", padx=18, pady=(0, 12))

        ctk.CTkLabel(card, text="Opacity", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=14, pady=(12, 0))
        self.slider = ctk.CTkSlider(card, from_=0, to=255, number_of_steps=255, command=self.on_alpha_change)
        self.slider.set(self.alpha_var.get())
        self.slider.pack(fill="x", padx=14, pady=(6, 4))

        self.alpha_label = ctk.CTkLabel(card, text=str(self.alpha_var.get()))
        self.alpha_label.pack(anchor="w", padx=14, pady=(0, 12))

        buttons = ctk.CTkFrame(card, fg_color="transparent")
        buttons.pack(fill="x", padx=14, pady=(0, 14))

        self.start_switch = ctk.CTkSwitch(buttons, text="Start with Windows", command=self.toggle_startup)
        self.start_switch.pack(side="left")
        if self.autostart_var.get():
            self.start_switch.select()

        ctk.CTkButton(buttons, text="Apply", command=self.apply_effect, width=110).pack(side="right")
        ctk.CTkButton(buttons, text="Clear", command=self.clear_effect, width=110).pack(side="right", padx=8)

        self.status = ctk.CTkLabel(outer, text="Ready")
        self.status.pack(anchor="w", padx=18, pady=(0, 18))

    def on_alpha_change(self, value):
        self.alpha_label.configure(text=str(int(float(value))))

    def toggle_startup(self):
        self.autostart_var.set(not self.autostart_var.get())
        ok = add_startup() if self.autostart_var.get() else remove_startup()
        self.status.configure(
            text="Startup enabled" if self.autostart_var.get() and ok else "Startup disabled" if ok else "Startup error"
        )
        self.save_state()

    def apply_effect(self):
        try:
            alpha = int(float(self.slider.get()))
            hwnds = enum_explorer_windows()
            for hwnd in hwnds:
                apply_opacity(hwnd, alpha)
            self.alpha_var.set(alpha)
            self.save_state()
            self.status.configure(text=f"Applied to {len(hwnds)} Explorer windows")
            write_log(f"Applied to {len(hwnds)} Explorer windows")
        except Exception as e:
            self.status.configure(text="Apply failed")
            messagebox.showerror(APP_NAME, str(e))

    def clear_effect(self):
        try:
            hwnds = enum_explorer_windows()
            for hwnd in hwnds:
                clear_opacity(hwnd)
            self.status.configure(text=f"Cleared from {len(hwnds)} Explorer windows")
            write_log(f"Cleared from {len(hwnds)} Explorer windows")
        except Exception as e:
            messagebox.showerror(APP_NAME, str(e))

    def save_state(self):
        save_cfg({
            "alpha": int(float(self.slider.get())),
            "autostart": self.autostart_var.get()
        })

    def on_close(self):
        self.save_state()
        self.destroy()


if __name__ == "__main__":
    app = AeroApp()
    app.mainloop()

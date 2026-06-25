import ctypes
import json
import os
import sys
import time
import threading

import customtkinter as ctk
from tkinter import messagebox
from PIL import Image
import pystray
from pystray import MenuItem as item

try:
    import winreg
except ImportError:
    winreg = None

def base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

APP_NAME = "Aero"
CONFIG_FILE = "config.json"
LOG_FILE = "aero.log"
ICON_FILE = "icon.ico"

CUSTOM_THEME_DIR = os.path.join(base_dir(), "themes")

THEMES = ["blue", "dark-blue", "green"]

PALETTE = {
    "Blue": "#3b82f6",
    "Sky": "#0ea5e9",
    "Cyan": "#06b6d4",
    "Teal": "#14b8a6",
    "Green": "#22c55e",
    "Lime": "#84cc16",
    "Yellow": "#eab308",
    "Orange": "#f97316",
    "Red": "#ef4444",
    "Pink": "#ec4899",
    "Purple": "#a855f7",
    "Gray": "#9ca3af",
}

def make_custom_theme(accent_hex, theme_name="custom"):
    os.makedirs(CUSTOM_THEME_DIR, exist_ok=True)
    path = os.path.join(CUSTOM_THEME_DIR, f"{theme_name}.json")

    base_theme_path = os.path.join(
        os.path.dirname(ctk.__file__),
        "assets",
        "themes",
        "blue.json"
    )

    with open(base_theme_path, "r", encoding="utf-8") as f:
        theme = json.load(f)

    if "CTkFont" not in theme:
        theme["CTkFont"] = {"family": "Segoe UI"}

    theme["CTkButton"]["fg_color"] = [accent_hex, accent_hex]
    theme["CTkButton"]["hover_color"] = [accent_hex, accent_hex]
    theme["CTkButton"]["text_color"] = ["#ffffff", "#ffffff"]

    theme["CTkSlider"]["progress_color"] = [accent_hex, accent_hex]
    theme["CTkSlider"]["button_color"] = [accent_hex, accent_hex]
    theme["CTkSlider"]["button_hover_color"] = [accent_hex, accent_hex]

    theme["CTkSwitch"]["progress_color"] = [accent_hex, accent_hex]
    theme["CTkSwitch"]["button_color"] = [accent_hex, accent_hex]
    theme["CTkSwitch"]["button_hover_color"] = [accent_hex, accent_hex]

    theme["CTkOptionMenu"]["fg_color"] = [accent_hex, accent_hex]
    theme["CTkOptionMenu"]["button_color"] = [accent_hex, accent_hex]
    theme["CTkOptionMenu"]["button_hover_color"] = [accent_hex, accent_hex]
    theme["CTkOptionMenu"]["text_color"] = ["#ffffff", "#ffffff"]

    theme["CTkSegmentedButton"]["selected_color"] = [accent_hex, accent_hex]
    theme["CTkSegmentedButton"]["selected_hover_color"] = [accent_hex, accent_hex]

    with open(path, "w", encoding="utf-8") as f:
        json.dump(theme, f, indent=2, ensure_ascii=False)

    return path

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


def cfg_path():
    return os.path.join(base_dir(), CONFIG_FILE)


def log_path():
    return os.path.join(base_dir(), LOG_FILE)


def write_log(message):
    stamp = time.strftime("%H:%M:%S")
    line = f"[{stamp}] {message}\n"
    try:
        with open(log_path(), "a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        pass


def load_cfg():
    data = {
        "alpha": 220,
        "autostart": False,
        "appearance_mode": "Light",
        "theme": "blue",
        "theme_path": "",
        "accent_name": "Blue",
        "accent_hex": "#3b82f6",
    }
    try:
        with open(cfg_path(), "r", encoding="utf-8") as f:
            data.update(json.load(f))
    except Exception:
        pass
    return data


def save_cfg(data):
    try:
        with open(cfg_path(), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def get_explorer_windows():
    hwnds = []
    excludes = {user32.GetShellWindow(), user32.FindWindowW("Shell_TrayWnd", None)}

    @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
    def callback(hwnd, lparam):
        if hwnd in excludes or not user32.IsWindowVisible(hwnd):
            return True
        cls = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, cls, 256)
        if cls.value in ("CabinetWClass", "ExplorerWClass"):
            hwnds.append(hwnd)
        return True

    user32.EnumWindows(callback, 0)
    return hwnds


def set_window_opacity(hwnd, alpha):
    exstyle = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    user32.SetWindowLongW(hwnd, GWL_EXSTYLE, exstyle | WS_EX_LAYERED)
    user32.SetLayeredWindowAttributes(hwnd, 0, int(alpha), LWA_ALPHA)


def clear_window_opacity(hwnd):
    exstyle = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    user32.SetWindowLongW(hwnd, GWL_EXSTYLE, exstyle & ~WS_EX_LAYERED)


def startup_command():
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"'
    return f'"{sys.executable}" "{os.path.abspath(__file__)}"'


def enable_startup():
    if not winreg:
        return False
    try:
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run")
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, startup_command())
        winreg.CloseKey(key)
        return True
    except Exception:
        return False


def disable_startup():
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


class AeroApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.cfg = load_cfg()
        self.alpha_var = ctk.IntVar(value=int(self.cfg.get("alpha", 220)))
        self.autostart_var = ctk.BooleanVar(value=bool(self.cfg.get("autostart", False)))
        self.appearance_var = ctk.StringVar(value=self.cfg.get("appearance_mode", "Light"))
        self.theme_var = ctk.StringVar(value=self.cfg.get("theme", "blue"))
        self.theme_path = self.cfg.get("theme_path", "")
        self.accent_hex = self.cfg.get("accent_hex", "#3b82f6")

        ctk.set_appearance_mode(self.appearance_var.get())

        if self.theme_path and os.path.exists(self.theme_path):
            try:
                ctk.set_default_color_theme(self.theme_path)
            except Exception:
                self.theme_path = ""
                ctk.set_default_color_theme("blue")
        else:
            ctk.set_default_color_theme("blue")

        self.title_font = ctk.CTkFont(family="Segoe UI", size=25, weight="bold")
        self.header_font = ctk.CTkFont(family="Segoe UI", size=15, weight="bold")
        self.body_font = ctk.CTkFont(family="Segoe UI", size=13)
        self.button_font = ctk.CTkFont(family="Segoe UI", size=13, weight="bold")
        self.status_font = ctk.CTkFont(family="Segoe UI", size=12)

        self.tray_icon = None
        self.tray_thread = None
        self.is_hidden = False
        self.monitor_running = True
        self.applied_hwnds = set()

        icon_path = resource_path(ICON_FILE)
        try:
            self.iconbitmap(icon_path)
        except Exception:
            pass

        self.title("Aero")
        self.geometry("780x420")
        self.minsize(780, 420)
        self.resizable(False, False)

        self.build_ui()
        self.protocol("WM_DELETE_WINDOW", self.hide_to_tray)

        self.after(250, self.apply_current_opacity)
        self.after(1000, self.monitor_explorer_windows)

    def build_ui(self):
        self.outer = ctk.CTkFrame(self, corner_radius=18)
        self.outer.pack(fill="both", expand=True, padx=16, pady=16)

        header = ctk.CTkFrame(self.outer, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(16, 10))

        ctk.CTkLabel(header, text="Aero", font=self.title_font).pack(anchor="w")
        ctk.CTkLabel(header, text="Explorer opacity controller", font=self.body_font).pack(anchor="w", pady=(2, 0))

        self.tabs = ctk.CTkTabview(self.outer)
        self.tabs.pack(fill="both", expand=True, padx=18, pady=(4, 10))
        self.tabs.add("Main")
        self.tabs.add("Appearance")

        self.build_main_tab(self.tabs.tab("Main"))
        self.build_appearance_tab(self.tabs.tab("Appearance"))

        self.status_bar = ctk.CTkLabel(self.outer, text="Ready", anchor="w", font=self.status_font)
        self.status_bar.pack(fill="x", padx=20, pady=(0, 14))

    def build_main_tab(self, parent):
        card = ctk.CTkFrame(parent, corner_radius=14)
        card.pack(fill="both", expand=True, padx=12, pady=12)

        ctk.CTkLabel(card, text="Opacity", font=self.header_font).pack(anchor="w", padx=16, pady=(14, 0))

        self.slider = ctk.CTkSlider(card, from_=0, to=255, number_of_steps=255, command=self.on_alpha_change)
        self.slider.set(self.alpha_var.get())
        self.slider.pack(fill="x", padx=16, pady=(8, 4))

        self.alpha_label = ctk.CTkLabel(card, text=str(self.alpha_var.get()), font=self.body_font)
        self.alpha_label.pack(anchor="w", padx=16, pady=(0, 14))

        controls = ctk.CTkFrame(card, fg_color="transparent")
        controls.pack(fill="x", padx=16, pady=(0, 16))

        self.start_switch = ctk.CTkSwitch(
            controls,
            text="Start with Windows",
            command=self.toggle_startup,
            font=self.body_font
        )
        self.start_switch.pack(side="left")

        if self.autostart_var.get():
            self.start_switch.select()

        ctk.CTkButton(
            controls,
            text="Clear",
            command=self.clear_effect,
            width=120,
            font=self.button_font
        ).pack(side="right")

    def build_appearance_tab(self, parent):
        card = ctk.CTkFrame(parent, corner_radius=14)
        card.pack(fill="both", expand=True, padx=12, pady=12)

        ctk.CTkLabel(card, text="Appearance", font=self.header_font).pack(anchor="w", padx=16, pady=(14, 6))

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        content.grid_columnconfigure(0, weight=1)
        content.grid_columnconfigure(1, weight=1)
        content.grid_rowconfigure(0, weight=1)

        left = ctk.CTkFrame(content, corner_radius=12)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=8)

        right = ctk.CTkFrame(content, corner_radius=12)
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=8)

        ctk.CTkLabel(left, text="Light / Dark", font=self.body_font).pack(anchor="w", padx=16, pady=(14, 4))

        self.appearance_switch = ctk.CTkSwitch(
            left,
            text="Dark mode",
            command=self.toggle_appearance_switch,
            font=self.body_font
        )
        self.appearance_switch.pack(anchor="w", padx=16, pady=(0, 12))

        if self.appearance_var.get() == "Dark":
            self.appearance_switch.select()
        else:
            self.appearance_switch.deselect()

        ctk.CTkLabel(right, text="Main color", font=self.body_font).pack(anchor="w", padx=16, pady=(14, 4))

        self.color_button = ctk.CTkButton(
            right,
            text="Choose color",
            command=self.choose_main_color,
            font=self.button_font,
            height=36
        )
        self.color_button.pack(anchor="w", padx=16, pady=(6, 8))

        self.default_button = ctk.CTkButton(
            right,
            text="Default",
            command=self.reset_appearance_defaults,
            font=self.button_font,
            height=36
        )
        self.default_button.pack(anchor="w", padx=16, pady=(0, 10))

    def reset_appearance_defaults(self):
        self.theme_path = ""
        self.theme_var.set("blue")
        self.accent_hex = "#3b82f6"
        ctk.set_default_color_theme("blue")
        self.save_state()
        self.apply_theme_live()
        self.set_status("Appearance reset to default")

    def choose_main_color(self):
        from tkinter import colorchooser
        _, hex_color = colorchooser.askcolor(initialcolor=self.accent_hex, title="Choose main color")
        if not hex_color:
            return
        self.accent_hex = hex_color
        self.theme_path = make_custom_theme(hex_color, "user_accent")
        self.save_state()
        self.apply_theme_live()
        self.set_status("Accent color updated")

    def toggle_appearance_switch(self):
        choice = "Dark" if self.appearance_switch.get() else "Light"
        self.change_appearance_mode(choice)

    def apply_theme_live(self):
        try:
            if self.theme_path and os.path.exists(self.theme_path):
                ctk.set_default_color_theme(self.theme_path)
            else:
                ctk.set_default_color_theme("blue")

            for widget in (getattr(self, "status_bar", None), getattr(self, "tabs", None),
                           getattr(self, "outer", None)):
                if widget is not None:
                    widget.destroy()

            self.build_ui()

            self.slider.set(self.alpha_var.get())
            self.alpha_label.configure(text=str(self.alpha_var.get()))

            if self.appearance_var.get() == "Dark":
                self.appearance_switch.select()
            else:
                self.appearance_switch.deselect()
        except Exception as e:
            messagebox.showerror(APP_NAME, str(e))

    def set_status(self, text):
        self.status_bar.configure(text=text)

    def on_alpha_change(self, value):
        alpha = int(float(value))
        self.alpha_label.configure(text=str(alpha))
        self.alpha_var.set(alpha)
        self.apply_current_opacity()

    def apply_current_opacity(self):
        try:
            alpha = int(self.alpha_var.get())
            current = set(get_explorer_windows())

            for hwnd in current:
                set_window_opacity(hwnd, alpha)

            self.applied_hwnds = current
            self.save_state()
            self.set_status(f"Opacity set to {alpha}")
        except Exception as e:
            self.set_status("Apply failed")
            messagebox.showerror(APP_NAME, str(e))

    def clear_effect(self):
        try:
            hwnds = get_explorer_windows()
            for hwnd in hwnds:
                clear_window_opacity(hwnd)

            self.alpha_var.set(255)
            self.slider.set(255)
            self.alpha_label.configure(text="255")
            self.applied_hwnds.clear()
            self.save_state()

            text = f"Opacity reset to 255 for {len(hwnds)} Explorer windows"
            self.set_status(text)
            write_log(text)
        except Exception as e:
            messagebox.showerror(APP_NAME, str(e))

    def monitor_explorer_windows(self):
        if not self.monitor_running:
            return

        try:
            alpha = int(self.alpha_var.get())
            current = set(get_explorer_windows())
            new_hwnds = current - self.applied_hwnds

            if new_hwnds:
                for hwnd in new_hwnds:
                    set_window_opacity(hwnd, alpha)
                self.applied_hwnds |= new_hwnds
                self.set_status(f"Applied to {len(current)} Explorer windows")
        except Exception:
            pass

        self.after(1000, self.monitor_explorer_windows)

    def toggle_startup(self):
        enabled = not self.autostart_var.get()
        self.autostart_var.set(enabled)
        ok = enable_startup() if enabled else disable_startup()
        self.set_status("Startup enabled" if enabled and ok else "Startup disabled" if ok else "Startup error")
        self.save_state()

    def change_appearance_mode(self, choice):
        self.appearance_var.set(choice)
        ctk.set_appearance_mode(choice)
        self.save_state()

    def save_state(self):
        save_cfg({
            "alpha": int(self.alpha_var.get()),
            "autostart": self.autostart_var.get(),
            "appearance_mode": self.appearance_var.get(),
            "theme_path": getattr(self, "theme_path", ""),
            "accent_hex": self.accent_hex,
        })

    def create_tray_icon(self):
        if self.tray_icon is not None:
            return

        try:
            tray_image = Image.open(resource_path(ICON_FILE))
        except Exception:
            tray_image = Image.new("RGBA", (64, 64), (0, 120, 215, 255))

        menu = pystray.Menu(
            item("Show", self.tray_show, default=True),
            item("Exit", self.tray_exit),
        )

        self.tray_icon = pystray.Icon(APP_NAME, tray_image, APP_NAME, menu)

        def run_icon():
            try:
                self.tray_icon.run()
            except Exception:
                pass

        self.tray_thread = threading.Thread(target=run_icon, daemon=True)
        self.tray_thread.start()

    def hide_to_tray(self):
        if self.is_hidden:
            return
        self.is_hidden = True
        self.withdraw()
        self.create_tray_icon()
        self.set_status("Running in tray")
        write_log("Minimized to tray")

    def restore_from_tray(self):
        self.deiconify()
        self.lift()
        self.focus_force()
        self.is_hidden = False
        self.set_status("Restored from tray")
        write_log("Restored from tray")

    def tray_show(self, icon=None, item=None):
        self.after(0, self.restore_from_tray)

    def tray_exit(self, icon=None, item=None):
        self.after(0, self.quit_app)

    def quit_app(self):
        self.monitor_running = False
        try:
            self.save_state()
        except Exception:
            pass

        try:
            if self.tray_icon:
                self.tray_icon.stop()
        except Exception:
            pass

        self.destroy()


if __name__ == "__main__":
    app = AeroApp()
    app.mainloop()

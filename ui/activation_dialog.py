"""
Modal dialog shown when no valid license is found.
"""

import threading
import customtkinter as ctk


class ActivationDialog(ctk.CTkToplevel):
    """
    Blocks app launch until user enters a valid key or closes the window.
    Result is stored in self.activated (bool).
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Активация Doc Converter")
        self.resizable(False, False)
        self.geometry("420x280")
        self.grab_set()           # modal
        self.focus_force()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self.activated = False
        self._build_ui()
        self.after(0, self._center)

    def _center(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() - self.winfo_width()) // 2
        y = (self.winfo_screenheight() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

    def _build_ui(self):
        pad = {"padx": 28, "pady": 0}

        ctk.CTkLabel(
            self, text="Требуется активация",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(pady=(24, 4))

        ctk.CTkLabel(
            self,
            text="Введите лицензионный ключ в формате XXXX-XXXX-XXXX-XXXX",
            text_color="gray",
            wraplength=360,
        ).pack(**pad, pady=(0, 16))

        self._key_var = ctk.StringVar()
        self._entry = ctk.CTkEntry(
            self,
            textvariable=self._key_var,
            placeholder_text="XXXX-XXXX-XXXX-XXXX",
            width=300,
            font=ctk.CTkFont(family="Courier New", size=14),
            justify="center",
        )
        self._entry.pack(**pad, pady=(0, 8))
        self._entry.bind("<Return>", lambda _: self._on_activate())

        self._status = ctk.CTkLabel(self, text="", text_color="gray", height=20)
        self._status.pack(**pad, pady=(0, 12))

        self._btn = ctk.CTkButton(
            self, text="Активировать", width=200, command=self._on_activate
        )
        self._btn.pack(pady=(0, 20))

    def _set_status(self, text: str, color: str = "gray"):
        self._status.configure(text=text, text_color=color)

    def _on_activate(self):
        key = self._key_var.get().strip()
        if not key:
            self._set_status("Введите ключ", "#c0392b")
            return

        self._btn.configure(state="disabled")
        self._entry.configure(state="disabled")
        self._set_status("Подключение к серверу...", "gray")

        threading.Thread(target=self._do_activate, args=(key,), daemon=True).start()

    def _do_activate(self, key: str):
        from utils.license_client import activate, ActivationError
        try:
            activate(key)
            self.after(0, self._on_success)
        except ActivationError as e:
            self.after(0, self._on_error, str(e))

    def _on_success(self):
        self._set_status("Активация успешна!", "#1a7a3e")
        self.activated = True
        self.after(800, self.destroy)

    def _on_error(self, msg: str):
        self._set_status(msg, "#c0392b")
        self._btn.configure(state="normal")
        self._entry.configure(state="normal")

    def _on_close(self):
        self.activated = False
        self.destroy()

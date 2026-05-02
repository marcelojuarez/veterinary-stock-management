"""
Diálogo de Actualización
Muestra al usuario la información de la nueva versión y gestiona
la descarga con barra de progreso.
Compatible con Tkinter (escritorio).
"""

import threading
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from typing import Callable, Optional

from services.update_service import UpdateInfo, UpdateService


class UpdateDialog(tk.Toplevel):
    """
    Ventana modal que:
      - Muestra versión actual vs nueva, notas de release y fecha.
      - Ofrece "Actualizar ahora" o "Recordar después".
      - Si el update es obligatorio (mandatory=True), no muestra el botón de posponer.
      - Muestra barra de progreso durante la descarga.
    """

    _BG = "#1e2130"
    _ACCENT = "#4f8ef7"
    _TEXT = "#e8eaf0"
    _MUTED = "#8b93a7"
    _SUCCESS = "#43c98d"
    _ERROR = "#e05c5c"
    _CARD = "#272b3d"

    def __init__(
        self,
        parent: tk.Tk,
        update_info: UpdateInfo,
        current_version: str,
        service: UpdateService,
        on_postpone: Optional[Callable] = None,
    ):
        super().__init__(parent)
        self.update_info = update_info
        self.current_version = current_version
        self.service = service
        self.on_postpone = on_postpone
        self._installer_path: Optional[Path] = None

        self._build_ui()
        self._center(parent)

        # Modal
        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)

    # ── UI ─────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        self.configure(bg=self._BG)
        self.title("Actualización disponible")
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        pad = {"padx": 24, "pady": 6}

        # ── Cabecera ──────────────────────────────────────────────────────────
        header = tk.Frame(self, bg=self._ACCENT, height=4)
        header.pack(fill="x")

        tk.Label(
            self,
            text="🚀  Nueva versión disponible",
            font=("Segoe UI", 15, "bold"),
            bg=self._BG,
            fg=self._TEXT,
        ).pack(pady=(20, 2))

        tk.Label(
            self,
            text=f"v{self.current_version}  →  v{self.update_info.latest_version}",
            font=("Segoe UI", 11),
            bg=self._BG,
            fg=self._ACCENT,
        ).pack()

        tk.Label(
            self,
            text=f"Publicado el {self.update_info.release_date}",
            font=("Segoe UI", 9),
            bg=self._BG,
            fg=self._MUTED,
        ).pack(pady=(0, 10))

        # ── Notas de release ──────────────────────────────────────────────────
        card = tk.Frame(self, bg=self._CARD, padx=16, pady=12)
        card.pack(fill="x", padx=24, pady=(0, 16))

        tk.Label(
            card,
            text="Novedades",
            font=("Segoe UI", 9, "bold"),
            bg=self._CARD,
            fg=self._MUTED,
        ).pack(anchor="w")

        tk.Label(
            card,
            text=self.update_info.release_notes or "Sin descripción.",
            font=("Segoe UI", 10),
            bg=self._CARD,
            fg=self._TEXT,
            wraplength=380,
            justify="left",
        ).pack(anchor="w", pady=(4, 0))

        # ── Advertencia obligatoria ───────────────────────────────────────────
        if self.update_info.mandatory:
            tk.Label(
                self,
                text="⚠️  Esta actualización es obligatoria.",
                font=("Segoe UI", 9, "bold"),
                bg=self._BG,
                fg="#f0c040",
            ).pack(**pad)

        # ── Barra de progreso (oculta hasta que empieza la descarga) ─────────
        self._progress_frame = tk.Frame(self, bg=self._BG)
        self._progress_frame.pack(fill="x", padx=24, pady=(0, 4))

        self._status_label = tk.Label(
            self._progress_frame,
            text="",
            font=("Segoe UI", 9),
            bg=self._BG,
            fg=self._MUTED,
        )
        self._status_label.pack(anchor="w")

        self._progress_bar = ttk.Progressbar(
            self._progress_frame,
            orient="horizontal",
            length=400,
            mode="determinate",
        )
        # No se empaqueta aún

        # ── Botones ───────────────────────────────────────────────────────────
        btn_frame = tk.Frame(self, bg=self._BG)
        btn_frame.pack(pady=(4, 20), padx=24, fill="x")

        self._update_btn = tk.Button(
            btn_frame,
            text="  Actualizar ahora  ",
            font=("Segoe UI", 10, "bold"),
            bg=self._ACCENT,
            fg="white",
            activebackground="#3a74e0",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            command=self._start_download,
        )
        self._update_btn.pack(side="left")

        if not self.update_info.mandatory:
            self._postpone_btn = tk.Button(
                btn_frame,
                text="Recordar después",
                font=("Segoe UI", 10),
                bg=self._BG,
                fg=self._MUTED,
                activebackground=self._BG,
                activeforeground=self._TEXT,
                relief="flat",
                cursor="hand2",
                command=self._on_postpone,
            )
            self._postpone_btn.pack(side="right")

    # ── Lógica ─────────────────────────────────────────────────────────────────

    def _start_download(self):
        """Inicia la descarga en un hilo secundario."""
        self._update_btn.config(state="disabled", text="Descargando...")
        if hasattr(self, "_postpone_btn"):
            self._postpone_btn.config(state="disabled")

        self._status_label.config(text="Iniciando descarga...")
        self._progress_bar.pack(fill="x", pady=(4, 0))

        thread = threading.Thread(target=self._download_worker, daemon=True)
        thread.start()

    def _download_worker(self):
        """Hilo de descarga (fuera del hilo principal de Tk)."""
        path = self.service.download_installer(
            self.update_info,
            progress_callback=self._on_progress,
        )
        # Volver al hilo de Tk para actualizar la UI
        self.after(0, self._on_download_done, path)

    def _on_progress(self, percent: int):
        self.after(0, self._update_progress_ui, percent)

    def _update_progress_ui(self, percent: int):
        self._progress_bar["value"] = percent
        self._status_label.config(text=f"Descargando...  {percent}%")

    def _on_download_done(self, installer_path: Optional[Path]):
        if installer_path is None:
            self._status_label.config(
                text="❌  Error en la descarga. Intentá de nuevo más tarde.",
                fg=self._ERROR,
            )
            self._update_btn.config(state="normal", text="  Reintentar  ")
            if hasattr(self, "_postpone_btn"):
                self._postpone_btn.config(state="normal")
            return

        self._installer_path = installer_path
        self._status_label.config(
            text="✅  Descarga completa. Instalando...",
            fg=self._SUCCESS,
        )
        self._progress_bar["value"] = 100

        # Pequeña pausa visual antes de instalar
        self.after(800, self._run_installer)

    def _run_installer(self):
        self.service.install_update(self._installer_path)
        # install_update llama a sys.exit(), así que esto no se ejecuta normalmente
        self.destroy()

    def _on_postpone(self):
        if self.on_postpone:
            self.on_postpone()
        self.destroy()

    def _on_close(self):
        if self.update_info.mandatory:
            messagebox.showwarning(
                "Actualización obligatoria",
                "Esta actualización es obligatoria y no puede posponerse.",
                parent=self,
            )
            return
        self._on_postpone()

    # ── Utilidades ─────────────────────────────────────────────────────────────

    def _center(self, parent: tk.Tk):
        self.update_idletasks()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_x()
        py = parent.winfo_y()
        w = self.winfo_reqwidth()
        h = self.winfo_reqheight()
        x = px + (pw - w) // 2
        y = py + (ph - h) // 2
        self.geometry(f"+{x}+{y}")
"""
Diálogo de Actualización
Compatible con macOS, Windows y Linux (usa colores del sistema).
"""

import threading
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from typing import Callable, Optional

from services.update_service import UpdateInfo, UpdateService


class UpdateDialog(tk.Toplevel):

    _ACCENT = "#4f8ef7"
    _MUTED = "gray40"
    _SUCCESS = "#2a9d5c"
    _ERROR = "#cc3333"

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

        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)

    def _build_ui(self):
        self.title("Actualización disponible")
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # ── Barra de acento superior ──────────────────────────────────────────
        tk.Frame(self, bg=self._ACCENT, height=4).pack(fill="x")

        # ── Título ────────────────────────────────────────────────────────────
        tk.Label(
            self,
            text="🚀  Nueva versión disponible",
            font=("Helvetica", 15, "bold"),
        ).pack(pady=(20, 2), padx=24)

        tk.Label(
            self,
            text=f"v{self.current_version}  →  v{self.update_info.latest_version}",
            font=("Helvetica", 11),
            fg=self._ACCENT,
        ).pack()

        tk.Label(
            self,
            text=f"Publicado el {self.update_info.release_date}",
            font=("Helvetica", 9),
            fg=self._MUTED,
        ).pack(pady=(0, 10))

        # ── Separador ─────────────────────────────────────────────────────────
        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=24)

        # ── Notas de release ──────────────────────────────────────────────────
        notes_frame = tk.Frame(self, padx=24, pady=10)
        notes_frame.pack(fill="x")

        tk.Label(
            notes_frame,
            text="NOVEDADES",
            font=("Helvetica", 8, "bold"),
            fg=self._MUTED,
        ).pack(anchor="w")

        tk.Label(
            notes_frame,
            text=self.update_info.release_notes or "Sin descripción.",
            font=("Helvetica", 10),
            wraplength=380,
            justify="left",
        ).pack(anchor="w", pady=(4, 0))

        # ── Advertencia obligatoria ───────────────────────────────────────────
        if self.update_info.mandatory:
            tk.Label(
                self,
                text="⚠️  Esta actualización es obligatoria.",
                font=("Helvetica", 9, "bold"),
                fg="#b8860b",
            ).pack(padx=24, pady=(0, 4))

        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=24)

        # ── Progreso ──────────────────────────────────────────────────────────
        self._progress_frame = tk.Frame(self, padx=24)
        self._progress_frame.pack(fill="x", pady=(8, 0))

        self._status_label = tk.Label(
            self._progress_frame,
            text="",
            font=("Helvetica", 9),
            fg=self._MUTED,
        )
        self._status_label.pack(anchor="w")

        self._progress_bar = ttk.Progressbar(
            self._progress_frame,
            orient="horizontal",
            length=400,
            mode="determinate",
        )

        # ── Botones ───────────────────────────────────────────────────────────
        btn_frame = tk.Frame(self, padx=24)
        btn_frame.pack(pady=(10, 20), fill="x")

        self._update_btn = tk.Button(
            btn_frame,
            text="  Actualizar ahora  ",
            font=("Helvetica", 10, "bold"),
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
                font=("Helvetica", 10),
                fg=self._MUTED,
                relief="flat",
                cursor="hand2",
                command=self._on_postpone,
            )
            self._postpone_btn.pack(side="right")

    # ── Lógica ─────────────────────────────────────────────────────────────────

    def _start_download(self):
        self._update_btn.config(state="disabled", text="Descargando...")
        if hasattr(self, "_postpone_btn"):
            self._postpone_btn.config(state="disabled")
        self._status_label.config(text="Iniciando descarga...")
        self._progress_bar.pack(fill="x", pady=(4, 0))
        threading.Thread(target=self._download_worker, daemon=True).start()

    def _download_worker(self):
        path = self.service.download_installer(
            self.update_info,
            progress_callback=self._on_progress,
        )
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
        self._status_label.config(text="✅  Descarga completa. Instalando...", fg=self._SUCCESS)
        self._progress_bar["value"] = 100
        self.after(800, self._run_installer)

    def _run_installer(self):
        self.service.install_update(self._installer_path)
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

    def _center(self, parent: tk.Tk):
        self.update_idletasks()
        w = self.winfo_reqwidth()
        h = self.winfo_reqheight()
        x = parent.winfo_x() + (parent.winfo_width() - w) // 2
        y = parent.winfo_y() + (parent.winfo_height() - h) // 2
        self.geometry(f"+{x}+{y}")
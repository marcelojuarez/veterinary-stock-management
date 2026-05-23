import logging
import os
import sys
import subprocess

logger = logging.getLogger(__name__)

def send_to_printer(file_path):
    """
    Motor de impresión unificado.
    Prioriza Windows con SumatraPDF y fallback a Win32API.
    En Mac solo abre el archivo para previsualizar.
    """
    if not file_path or not os.path.exists(file_path):
        logger.error("Archivo no encontrado en %s", file_path)
        return False

    # --- LÓGICA PARA WINDOWS (Producción) ---
    if sys.platform == "win32":
        sumatra_candidates = [
            r"C:\Program Files\SumatraPDF\SumatraPDF.exe",
            r"C:\Program Files (x86)\SumatraPDF\SumatraPDF.exe",
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "SumatraPDF", "SumatraPDF.exe"),
        ]
        sumatra = next((p for p in sumatra_candidates if os.path.exists(p)), None)
        try:
            if sumatra:
                subprocess.Popen([sumatra, "-print-to-default", "-silent", file_path])
            else:
                # Fallback nativo — no requiere dependencias externas
                os.startfile(file_path, "print")
            return True
        except Exception as e:
            logger.error("Error de impresión en Windows: %s", e)
            return False

    # --- LÓGICA PARA MAC (Desarrollo) ---
    elif sys.platform == "darwin":
        # Como no te interesa imprimir en Mac, solo lo abrimos para que veas que se generó bien
        subprocess.run(["open", file_path], check=True)
        return True

    return False
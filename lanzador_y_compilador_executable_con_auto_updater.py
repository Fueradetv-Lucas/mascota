import os
import sys
import json
import time
import shutil
import threading
import urllib.request
import subprocess
import tkinter as tk
from tkinter import messagebox, ttk

APP_NAME = "MascotaVirtual3D"
CURRENT_VERSION = "2.5.0"
# Cambia esta URL por la de tu servidor, GitHub Releases o JSON de versiones futuro
UPDATE_CHECK_URL = "https://raw.githubusercontent.com/mi-usuario/mascota-virtual/main/version.json"
HTML_FILE_NAME = "index.html"

def get_resource_path(relative_path):
    """ Obtiene la ruta absoluta de un recurso, compatible con PyInstaller (.exe) """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class AutoUpdater:
    def __init__(self, current_version, update_url):
        self.current_version = current_version
        self.update_url = update_url

    def parse_version(self, v_str):
        """ Convierte string '2.5.0' en tupla de enteros (2, 5, 0) """
        try:
            return tuple(map(int, v_str.strip().split('.')))
        except Exception:
            return (0, 0, 0)

    def check_for_updates(self, on_update_found_callback):
        """ Revisa en segundo plano si existe una versión superior """
        def worker():
            try:
                # Intento de petición HTTP con timeout
                req = urllib.request.Request(self.update_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=5) as response:
                    data = json.loads(response.read().decode('utf-8'))
                    latest_version = data.get("version", "0.0.0")
                    download_url = data.get("exe_url", "")
                    changelog = data.get("changelog", "Mejoras generales y corrección de errores.")

                    if self.parse_version(latest_version) > self.parse_version(self.current_version):
                        on_update_found_callback(latest_version, download_url, changelog)
            except Exception as e:
                print(f"[AutoUpdater] No se pudo verificar actualizaciones: {e}")

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()

    def download_and_install_update(self, download_url, status_callback):
        """ Descarga el nuevo .exe y prepara el reinicio de actualización """
        try:
            temp_exe = os.path.join(os.environ.get("TEMP", "."), "MascotaVirtual_New.exe")
            status_callback("Descargando actualización...")

            # Descarga con reporte de progreso
            urllib.request.urlretrieve(download_url, temp_exe)
            status_callback("Instalando actualización...")

            # Script batch temporal para reemplazar el .exe actual al cerrarse
            current_exe = sys.executable
            updater_bat = os.path.join(os.environ.get("TEMP", "."), "update_runner.bat")
            
            bat_content = f"""@echo off
timeout /t 2 /nobreak > nul
move /y "{temp_exe}" "{current_exe}"
start "" "{current_exe}"
del "%~f0"
"""
            with open(updater_bat, "w") as f:
                f.write(bat_content)

            # Ejecuta el script de reemplazo y cierra el proceso actual
            subprocess.Popen([updater_bat], shell=True)
            sys.exit(0)
        except Exception as err:
            messagebox.showerror("Error de Actualización", f"No se pudo completar la actualización:\n{err}")

def show_update_dialog(latest_ver, download_url, changelog):
    """ Muestra una ventana de diálogo estilizada en Windows si hay una actualización """
    root = tk.Tk()
    root.title("Actualización Disponible")
    root.geometry("420x240")
    root.resizable(False, False)
    root.configure(bg="#0f172a")

    # Centrar ventana
    root.eval('tk::PlaceWindow . center')

    lbl_title = tk.Label(root, text=f"🎉 ¡Nueva Versión v{latest_ver} Disponible!", font=("Segoe UI", 12, "bold"), fg="#00f0ff", bg="#0f172a")
    lbl_title.pack(pady=(15, 5))

    txt_notes = tk.Text(root, height=4, width=45, font=("Segoe UI", 9), bg="#1e293b", fg="#e2e8f0", borderwidth=0, highlightthickness=0)
    txt_notes.insert(tk.END, f"Notas de la versión:\n{changelog}")
    txt_notes.config(state=tk.DISABLED)
    txt_notes.pack(pady=5)

    lbl_status = tk.Label(root, text="", font=("Segoe UI", 8), fg="#38bdf8", bg="#0f172a")
    lbl_status.pack(pady=2)

    def start_download():
        btn_update.config(state=tk.DISABLED)
        btn_cancel.config(state=tk.DISABLED)
        updater = AutoUpdater(CURRENT_VERSION, UPDATE_CHECK_URL)
        def update_status(text):
            lbl_status.config(text=text)
            root.update()

        threading.Thread(target=updater.download_and_install_update, args=(download_url, update_status), daemon=True).start()

    btn_frame = tk.Frame(root, bg="#0f172a")
    btn_frame.pack(pady=10)

    btn_update = tk.Button(btn_frame, text="Actualizar Ahora", font=("Segoe UI", 9, "bold"), bg="#0078d4", fg="white", activebackground="#106ebe", activeforeground="white", width=15, borderwidth=0, command=start_download)
    btn_update.pack(side=tk.LEFT, padx=5)

    btn_cancel = tk.Button(btn_frame, text="Más tarde", font=("Segoe UI", 9), bg="#334155", fg="white", activebackground="#475569", activeforeground="white", width=12, borderwidth=0, command=root.destroy)
    btn_cancel.pack(side=tk.LEFT, padx=5)

    root.mainloop()

def launch_app():
    """ Inicia el visor WebView2 o el navegador nativo para mostrar la app """
    html_path = get_resource_path(HTML_FILE_NAME)

    if not os.path.exists(html_path):
        messagebox.showerror("Error de Archivo", f"No se encontró el archivo base {HTML_FILE_NAME}.")
        return

    # Iniciar comprobador de actualizaciones
    updater = AutoUpdater(CURRENT_VERSION, UPDATE_CHECK_URL)
    updater.check_for_updates(lambda latest, url, notes: show_update_dialog(latest, url, notes))

    # Intentar usar pywebview para ventana nativa fluida de Windows
    try:
        import webview
        webview.create_window(
            title=f"{APP_NAME} — v{CURRENT_VERSION}",
            url=html_path,
            width=1100,
            height=750,
            resizable=True,
            min_size=(900, 600),
            background_color='#0b1329'
        )
        webview.start()
    except ImportError:
        # Respaldo si pywebview no está instalado: servidor local estático + Edge app mode
        import http.server
        import socketserver
        import webbrowser

        PORT = 8991
        os.chdir(os.path.dirname(html_path))
        
        handler = http.server.SimpleHTTPRequestHandler
        httpd = socketserver.TCPServer(("", PORT), handler)

        def run_server():
            httpd.serve_forever()

        t = threading.Thread(target=run_server, daemon=True)
        t.start()

        # Abrir en modo App de Microsoft Edge sin marcos de navegador
        edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
        url = f"http://localhost:{PORT}/{HTML_FILE_NAME}"
        
        if os.path.exists(edge_path):
            subprocess.Popen([edge_path, f"--app={url}"])
        else:
            webbrowser.open(url)

def build_executable():
    """ Script automatizado para compilar a .exe con PyInstaller """
    print("===========================================")
    print(" COMPILANDO EJECUTABLE MASCOTA VIRTUAL 3D  ")
    print("===========================================\n")

    try:
        import PyInstaller
    except ImportError:
        print("Instalando PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller", "pywebview"])

    # Comando PyInstaller para crear un único .exe sin consola
    cmd = [
        "pyinstaller",
        "--noconsole",
        "--onefile",
        f"--add-data={HTML_FILE_NAME};.",
        f"--name={APP_NAME}",
        "app_launcher.py"
    ]

    print("Ejecutando proceso de compilación...")
    subprocess.check_call(cmd)

    print("\n¡COMPILACIÓN EXITOSA!")
    print(f"Encuentra tu ejecutable en la carpeta: {os.path.abspath('dist')}/{APP_NAME}.exe")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--build":
        build_executable()
    else:
        launch_app()
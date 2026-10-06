import os, sys, json, threading, queue, urllib.request, subprocess
import tkinter as tk
from tkinter import messagebox

APP_NAME = "MascotaVirtual3D"
CURRENT_VERSION = "2.5.0"
# Cambia "Fueradetv-Lucas/mascota" por tu usuario/repositorio de GitHub
UPDATE_CHECK_URL = "https://raw.githubusercontent.com/Fueradetv-Lucas/mascota/main/version.json"
HTML_FILE_NAME = "index.html"


def get_resource_path(relative_path):
    base_path = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base_path, relative_path)


def parse_version(v):
    try:
        return tuple(int(x) for x in v.strip().lstrip("v").split("."))
    except Exception:
        return (0, 0, 0)


def fetch_update_info():
    try:
        req = urllib.request.Request(UPDATE_CHECK_URL, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read().decode("utf-8"))
        if parse_version(data.get("version", "0")) > parse_version(CURRENT_VERSION):
            return data
    except Exception as e:
        print(f"[AutoUpdater] No se pudo verificar actualizaciones: {e}")
    return None


def apply_update(download_url, status):
    """Descarga el nuevo .exe y lo reemplaza al cerrar la app actual."""
    if not getattr(sys, "frozen", False):
        status("Actualización solo disponible en el .exe compilado.")
        return
    tmp = os.environ.get("TEMP", ".")
    new_exe = os.path.join(tmp, f"{APP_NAME}_New.exe")
    status("Descargando actualización...")
    urllib.request.urlretrieve(download_url, new_exe)
    status("Instalando actualización...")
    current_exe = sys.executable
    bat = os.path.join(tmp, "update_runner.bat")
    with open(bat, "w") as f:
        f.write(f'''@echo off
:retry
timeout /t 2 /nobreak > nul
move /y "{new_exe}" "{current_exe}" > nul 2>&1
if errorlevel 1 goto retry
start "" "{current_exe}"
del "%~f0"
''')
    subprocess.Popen(["cmd", "/c", bat], creationflags=0x08000000)  # sin ventana
    os._exit(0)


def update_worker():
    """Corre en un hilo: consulta y, si hay versión nueva, muestra el diálogo Tk en ESE hilo."""
    info = fetch_update_info()
    if not info:
        return
    root = tk.Tk()
    root.title("Actualización Disponible")
    root.geometry("420x240")
    root.resizable(False, False)
    root.configure(bg="#0f172a")
    root.attributes("-topmost", True)

    tk.Label(root, text=f"🎉 ¡Nueva Versión v{info['version']} Disponible!",
             font=("Segoe UI", 12, "bold"), fg="#00f0ff", bg="#0f172a").pack(pady=(15, 5))
    txt = tk.Text(root, height=4, width=45, font=("Segoe UI", 9), bg="#1e293b",
                  fg="#e2e8f0", borderwidth=0, highlightthickness=0)
    txt.insert(tk.END, "Notas de la versión:\n" + info.get("changelog", "Mejoras generales."))
    txt.config(state=tk.DISABLED)
    txt.pack(pady=5)
    lbl = tk.Label(root, text="", font=("Segoe UI", 8), fg="#38bdf8", bg="#0f172a")
    lbl.pack(pady=2)

    q = queue.Queue()

    def poll():
        try:
            while True:
                lbl.config(text=q.get_nowait())
        except queue.Empty:
            pass
        root.after(150, poll)

    def start_download():
        btn_up.config(state=tk.DISABLED)
        btn_no.config(state=tk.DISABLED)

        def run():
            try:
                apply_update(info.get("exe_url", ""), q.put)
            except Exception as e:
                q.put(f"Error: {e}")
        threading.Thread(target=run, daemon=True).start()

    frame = tk.Frame(root, bg="#0f172a")
    frame.pack(pady=10)
    btn_up = tk.Button(frame, text="Actualizar Ahora", font=("Segoe UI", 9, "bold"), bg="#0078d4",
                       fg="white", width=15, borderwidth=0, command=start_download)
    btn_up.pack(side=tk.LEFT, padx=5)
    btn_no = tk.Button(frame, text="Más tarde", font=("Segoe UI", 9), bg="#334155",
                       fg="white", width=12, borderwidth=0, command=root.destroy)
    btn_no.pack(side=tk.LEFT, padx=5)
    root.eval("tk::PlaceWindow . center")
    poll()
    root.mainloop()


def launch_app():
    html_path = get_resource_path(HTML_FILE_NAME)
    if not os.path.exists(html_path):
        messagebox.showerror("Error de Archivo", f"No se encontró {HTML_FILE_NAME}.")
        return

    threading.Thread(target=update_worker, daemon=True).start()

    try:
        import webview
    except ImportError:
        import webbrowser
        webbrowser.open("file:///" + html_path.replace("\\", "/"))
        return
    webview.create_window(title=f"{APP_NAME} — v{CURRENT_VERSION}", url=html_path,
                          width=1100, height=750, resizable=True, min_size=(900, 600),
                          background_color="#0b1329")
    webview.start()


def build_executable():
    try:
        import PyInstaller  # noqa
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller", "pywebview"])
    cmd = [sys.executable, "-m", "PyInstaller", "--noconsole", "--onefile", "--clean",
           f"--add-data={HTML_FILE_NAME};.", f"--name={APP_NAME}", "app_launcher.py"]
    subprocess.check_call(cmd)
    print(f"\n¡COMPILACIÓN EXITOSA! -> {os.path.abspath('dist')}\\{APP_NAME}.exe")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--build":
        build_executable()
    else:
        launch_app()

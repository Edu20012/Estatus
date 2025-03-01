import threading
import time
import psutil
import socket
import platform  # Nuevo: Para detectar el sistema operativo
from flask import Flask
app = Flask(__name__)

# Verificación de servicios solo en Windows
SISTEMA_WINDOWS = platform.system() == "Windows"
if SISTEMA_WINDOWS:
    try:
        import win32serviceutil
    except ImportError:
        print("\nAdvertencia: pywin32 no instalado. Verificación de servicios deshabilitada.")
        win32serviceutil = None
else:
    win32serviceutil = None


class MonitorThread(threading.Thread):
    def __init__(self, proceso_nombre, servicio_nombre=None, puerto=None, intervalo=5):
        super().__init__()
        self.proceso_nombre = proceso_nombre
        self.servicio_nombre = servicio_nombre
        self.puerto = puerto
        self.intervalo = intervalo
        self.detener = threading.Event()
        self.lock = threading.Lock()

    def verificar_proceso(self):
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] == self.proceso_nombre:
                return True
        return False

    def verificar_servicio_windows(self):
        if not SISTEMA_WINDOWS or not self.servicio_nombre:
            return "No aplicable"

        if not win32serviceutil:
            return "Requiere pywin32"

        try:
            status = win32serviceutil.QueryServiceStatus(self.servicio_nombre)
            return "Ejecutando" if status[1] == 4 else "Detenido"
        except Exception as e:
            return f"Error: {str(e)}"

    def verificar_puerto(self):
        if not self.puerto:
            return "No configurado"

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        try:
            sock.connect(('localhost', self.puerto))
            return "Abierto"
        except (ConnectionRefusedError, socket.timeout):
            return "Cerrado"
        finally:
            sock.close()

    def run(self):
        while not self.detener.is_set():
            with self.lock:
                print("\n--- Estado de la Aplicación ---")
                print(f"Proceso '{self.proceso_nombre}': {'✅ Activo' if self.verificar_proceso() else '❌ Inactivo'}")

                if self.servicio_nombre:
                    print(f"Servicio '{self.servicio_nombre}': {self.verificar_servicio_windows()}")

                print(f"Puerto {self.puerto}: {self.verificar_puerto()}")
                print("-------------------------------")

            time.sleep(self.intervalo)

    def parar(self):
        self.detener.set()


if __name__ == "__main__":
    # CONFIGURACIÓN PERSONALIZABLE (¡Edita estos valores!)
    monitoreador = MonitorThread(
        proceso_nombre="python.exe",  # Ej: "chrome.exe", "mysqld.exe"
        servicio_nombre="W3SVC",  # Ej: "MySQL", solo para Windows
        puerto=5000,  # Ej: 8080, 3306
        intervalo=3  # Segundos entre verificaciones
    )

    try:
        print("Iniciando monitoreo (Presiona Ctrl+C para detener)...")
        monitoreador.start()
        monitoreador.join()
    except KeyboardInterrupt:
        monitoreador.parar()
        print("\nMonitoreo detenido.")


@app.route('/')
def hello():
    return "¡Servidor activo!"

if __name__ == '__main__':
    app.run(port=5000)
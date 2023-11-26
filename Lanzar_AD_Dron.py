# Lanzar_AD_Dron.py
import subprocess
import sys

if len(sys.argv) > 1:
    numero_dron = sys.argv[1]

    # Añade aquí los argumentos necesarios
    ip1 = "192.168.1.17:1234"
    ip2 = "192.168.1.17:9092"
    ip3 = "192.168.1.17:9999"

    subprocess.run(["python", "AD_Dron.py", ip1, ip2, ip3, numero_dron,"True"], text=True)

else:
    print("Número de dron no proporcionado.")

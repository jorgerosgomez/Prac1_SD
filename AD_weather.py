import sys
import socket
import json


ruta = "bd_Clima.json"

def ejecutar_servidor(puerto):
    
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.bind(("0.0.0.0", int(puerto)))
    servidor.listen(1)
    print(f"Esperando conexión en el puerto {puerto}...")

    # Aceptar una nueva conexión
    conn, addr = servidor.accept()
    print(f"Conexión establecida desde {addr}")

    try:
        while True:
            data = conn.recv(1024).decode()
            if not data:
                break  # Si no hay datos, el cliente se desconectó

            ciudad = json.loads(data)["ciudad"]
            datos = cargar_datos_clima()
            temperatura = datos.get(ciudad, 15)
            respuesta = {"ciudad": ciudad, "temperatura": temperatura}
 
            
            conn.send(json.dumps(respuesta).encode())

    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()
        servidor.close()

        

def cargar_datos_clima():
    with open(ruta, "r") as file:
        try:
            datos = json.load(file)
            clima_ciudades = {item["ciudad"]: item["temperatura"] for item in datos["lista ciudades"]}
        except json.JSONDecodeError:
            datos = {}
            print("Error: El archivo JSON está vacío o tiene un formato incorrecto.")
    return clima_ciudades



if __name__=="__main__":
    
    
    
    if len(sys.argv) != 2:
        print( "Error parametros incorrectos")
    
    puerto = sys.argv[1]
    ejecutar_servidor(puerto)
    
    
    
    
   
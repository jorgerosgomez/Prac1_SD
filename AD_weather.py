import sys
import socket
import json


ruta = "bd_Clima.json"

# Función para iniciar el servidor en un puerto específico
def iniciar_servidor(puerto):

    # Crear un socket y enlazarlo al puerto especificado
    servidor = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    servidor.bind(("localhost", int(puerto)))
    servidor.listen(1) 
    print(f"Esperando conexion en el puerto {puerto}...")   

    while True:
        conn, addr = servidor.accept() # Aceptar una nueva conexión
        print(f"Conexión establecida desde {addr}")

        # Recibir datos de la conexión
        data = conn.recv(1024).decode()
        ciudad = json.loads(data)["ciudad"]

        #Cargar datos desde la base de datos
        datos = guardar_json()

        #Buscar la temperatura de la ciudad solicitada
        if ciudad in datos:
            temperatura = datos[ciudad]
            respuesta = {"ciudad": ciudad, "temperatura": temperatura}
        else:
            respuesta = {"ciudad": ciudad, "temperatura": "Desconocida"}
    
        #Enviar respuesta a engine
        conn.send(json.dumps(respuesta).encode())
        conn.close

#Funcion para cargar datos desde un archivo JSON
def guardar_json():
    with open(ruta, "r") as file:
        try:
            datos = json.load(file)
        except json.JSONDecodeError:
            datos = {}
            print("Error JSON vacío")
    return datos

if __name__ == "__main":
    if len(sys.argv) != 2:
        print("Error: parámetros incorrectos")
        sys.exit(1)

    puerto = sys.argv[1]

    # Iniciar el servidor en el puerto especificado
    iniciar_servidor(puerto)
    
   
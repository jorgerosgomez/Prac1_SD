import sys
import socket
import json


ruta = "bd_Clima.json"

def iniciar_servidor(puerto):

    servidor = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    servidor.bind(("localhost", int(puerto)))
    servidor.listen(1) 
    print(f"Esperando conexion en el puerto {puerto}...")   

def guardar_json():
    
    
    with open(ruta,"r") as file:
        try:
            datos = json.load(file)
        except json.JSONDecodeError:
            datos= {}
            print("Error JSON vacio")
    return datos




if __name__=="__main__":
    
    

    
    if len(sys.argv) != 2:
        print( "Error parametros incorrectos")
    
    puerto = sys.argv[1]
    datos =  guardar_json() 
    iniciar_servidor(puerto)
    
   
import json
import socket
import sys
import time
import threading
import string
import secrets



def calcular_lrc(mensaje):
    bytes_mensaje = mensaje.encode('utf-8')
    
    lrc = 0
    # Calcular el LRC usando XOR
    for byte in bytes_mensaje:
        lrc ^= byte
     # Convertir el resultado a una cadena hexadecimal
    lrc_hex = format(lrc, '02X')
    
    return lrc_hex
def extraer_data(mensaje):
    print("por implementar")
    return mensaje
def genera_token():
 
    caracteres = string.ascii_letters + string.digits
    token = ''.join(secrets.choice(caracteres) for _ in range(7))
    return token


def procesar_cliente(cliente_conexion):
    print("llega")
    try:
        
        enq = cliente_conexion.recv(1024).decode()

        if enq == "<ENQ>": 
            ack = "<ACK>"
            cliente_conexion.send(ack.encode())
            mensaje = cliente_conexion.recv(1024).decode()
            print(mensaje)
            mensaje =extraer_data(mensaje) #mensaje filtrado
            if mensaje is not None:
                
                print(f"Datos recibidos: {mensaje}")
                cliente_conexion.send(ack.encode())
                cliente_conexion.send(genera_token().encode()) 
        else:
            print("No llegó el <ENQ>")
            cliente_conexion.close()
    except socket.error as err:
        print(f"Error de socket: {err}")
    except Exception as err:
        print(f"Error de cliente: {err}")
    finally:
        cliente_conexion.close()




def registro(puerto):
    try:
        #abrimos la conexion con sockets y nos ponemos a la escucha
        print(socket.gethostbyname("localhost"))
        conexion = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conexion.bind(("localhost", puerto))
        conexion.listen(1)
        #establecemos un tiempo de maximo en el que el servidor no tiene conxiones y si no las tiene lo cierra
        conexion.settimeout(60)


        print(f"Escuchando en el puerto {puerto}...")
        while True:
            cliente_conexion, cliente_direccion = conexion.accept()
            print(f"Se ha establecido conexion con {cliente_direccion}")

            hilo = threading.Thread(target=procesar_cliente , args=(cliente_conexion,))
            hilo.start()

    except KeyboardInterrupt:
        print("Registro de Drones detenido.")
        conexion.close()
    except Exception as e:
        print(f"Error: {e}")



    

if __name__ == "__main__":
    if len(sys.argv) != 2:
            print("Error debes pasar los argumentos indicados (Puerto)")
            sys.exit(1)
    
    puerto = sys.argv[1]
    if puerto.isnumeric():  # Corregir aquí
        registro(int(puerto))
    else:
        print("Error de puerto")
        sys.exit(1)

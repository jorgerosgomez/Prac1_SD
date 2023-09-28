import socket
import sys
import time
import threading


def procesar_cliente(cliente_conexion):
    try:
        enq = cliente_conexion.recv(1024).decode()

        if enq == "<ENQ>": 
            ack = "<ACK>"
            cliente_conexion.send(ack.encode())
            # Procesar datos
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
        conexion = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conexion.bind(("localhost", puerto))
        conexion.listen(1)
        #establecemos un tiempo de maximo en el que el servidor no tiene conxiones y si no las tiene lo cierra
        conexion.settimeout(360)


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
        respuesta = input("No se ha establecido el número adecuado de argumentos - Puerto\n ¿Quiere insertarlo de forma manual? S/N ")
        if respuesta == "N" or respuesta == "n":
            sys.exit(1)
        else:
            puerto = input("Inserte un Puerto (Numerico): ")

    if puerto.isnumeric():  # Corregir aquí
        registro(int(puerto))
    else:
        print("Error de puerto")
        sys.exit(1)

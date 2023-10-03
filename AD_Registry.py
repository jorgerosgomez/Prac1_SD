import json
import socket
import sys
import time
import threading
import string
import secrets

file_bd_engine =  r'C:\Users\jorge\Desktop\uni\SD\Prac 1\bd_Engine.json'

def calcular_lrc(mensaje):
    bytes_mensaje = mensaje.encode('utf-8')
    
    lrc = 0
    # Calcular el LRC usando XOR
    for byte in bytes_mensaje:
        lrc ^= byte
     # Convertir el resultado a una cadena hexadecimal
    lrc_hex = format(lrc, '02X')
    
    return lrc_hex
def incluir_json(file_Dron, dato):
                    
    try:
                        
        with open(file_Dron, 'r') as file:
            try:
                json_data = json.load(file)
            except json.JSONDecodeError:
                    json_data = {}
                        
        json_data.setdefault("lista_de_objetos", []).append(dato)
                        
        with open(file_Dron, 'w') as file:
            json.dump(json_data, file, indent=2)  # indent para una escritura más bonita

    except FileNotFoundError:
        print(f'No se encontró el archivo en la ruta: {file_Dron}')

    except Exception as e:
        print(f'Ocurrió un error: {e}')

def genera_token():
 
    caracteres = string.ascii_letters + string.digits
    token = ''.join(secrets.choice(caracteres) for _ in range(7))
    return token
def desencriptar_paquete(paquete):
   #COMPRUEBA QUE EXISTA EL STX
    inicio = paquete.find("<STX>")
    if inicio == -1:
        print("STX no encontrado")
        return None

    # COMPRUEBA QUE EXISTA EL ETX
    fin = paquete.find("<ETX>")
    if fin == -1:
        print("ETX no encontrado")
        return None

    #EXTRAE EL PAQUETE ELIMINANDO LAS CABECERAS
    data = paquete[inicio + len("<STX>"):fin]

    #REARAMOS EL PAQUETE ORIGINAL SIN EL LRC PARA CALCULARLO 
    lrc_calculado = calcular_lrc(f"<STX>{data}<ETX>")

    # BUSCAMOS EL LRC DEL PAQUETE ORIGINAL
    lrc_inicio = fin + len("<ETX>")
    lrc_fin = lrc_inicio + 2
    lrc_paquete = paquete[lrc_inicio:lrc_fin]

    # Y LO COMPARAMOS
    if lrc_calculado != lrc_paquete:       
        print(f"Error en LRC: {lrc_paquete} != {lrc_calculado}")
        return None

    # Decodificar la DATA (asumiendo que está en formato JSON)
    try:
        datos_json = json.loads(data)
        return datos_json
    except json.JSONDecodeError as e:
        print(f"Error al decodificar JSON: {e}")
        return None


def procesar_cliente(cliente_conexion):
    try:
        
        enq = cliente_conexion.recv(1024).decode()

        if enq == "<ENQ>": 
            ack = "<ACK>"
            cliente_conexion.send(ack.encode())
            mensaje = cliente_conexion.recv(1024).decode()
            mensaje = desencriptar_paquete(mensaje) #mensaje filtrado
            if mensaje is not None:
            
                
                cliente_conexion.send(ack.encode())
                token= genera_token()
                cliente_conexion.send(token.encode()) 
               
                try:
                   
                    primera_clave = next(iter(mensaje))
                 # Cambiar el atributo "token" para la primera clave
                    mensaje[primera_clave]["token"] = token
                except StopIteration:
                    print("El objeto JSON está vacío")
                except Exception as e:
                    print(f'Ocurrió un error: {e}')
               
                incluir_json(file_bd_engine,mensaje)
                
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

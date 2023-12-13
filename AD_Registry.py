import json
import socket
import sys
import time
import threading
import string
import secrets
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
import os
import shutil
from cryptography.hazmat.primitives.asymmetric import padding
from flask import Flask, request,jsonify
from flask_restful import Resource, Api
from datetime import datetime, timedelta
from flask_sslify import SSLify


App =Flask(__name__)
api =  Api(App) 
SSLify =  SSLify(App)

class RegistroAPI(Resource):
    def post(self):
        data = request.get_json()  # Obtener el JSON del cuerpo de la solicitud
        if data and 'id' in data and 'alias' in data:
            token, caducidad = genera_token().split('/')
            # Construir el nuevo objeto con la información proporcionada y el token generado
            nuevo_registro = {
                data['id']: {
                    "alias": data['alias'],
                    "token": token,
                    "Expiracion": caducidad
                }
            }
            incluir_json(file_bd_engine, nuevo_registro)  # Guardar el nuevo registro
            return jsonify(nuevo_registro)
        else:
            return jsonify({"error": "Faltan datos en la solicitud"}), 400

api.add_resource(RegistroAPI, '/registro')

def iniciar_flask():
    App.run(ssl_context='adhoc', debug=True, use_reloader=False, host='0.0.0.0', port=5001)
    

###################
file_bd_engine =  'bd_Engine.json'

def eliminar_claves(carpeta="claves_drones"):
    if os.path.exists(carpeta):
        shutil.rmtree(carpeta)

def cifrar_con_clave_publica(mensaje, clave_publica):
    
   
    if isinstance(mensaje, str):
        mensaje_bytes = mensaje.encode('utf-8')
    else:
        mensaje_bytes = mensaje
   
    
    mensaje_cifrado = clave_publica.encrypt(
        mensaje_bytes,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    return mensaje_cifrado


def guardar_clave(id_dron, clave_publica_pem):
    directorio = "claves_drones"
    archivo_clave = f"{directorio}/{id_dron}.pem"

    # Crear el directorio si no existe
    if not os.path.exists(directorio):
        os.makedirs(directorio)

    # Guardar la clave pública en un archivo PEM
    with open(archivo_clave, 'wb') as file:
        file.write(clave_publica_pem)


def cargar_clave_publica(id_dron):
    ruta_archivo = f"claves_drones/{id_dron}.pem"

    # Leer el archivo PEM
    with open(ruta_archivo, 'rb') as file:
        clave_publica_pem = file.read()

    # Cargar la clave pública
    clave_publica = serialization.load_pem_public_key(
        clave_publica_pem,
        backend=default_backend()
    )

    return clave_publica

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
    caducidad  = int(time.time()) + 20
    return f"{token}/{caducidad}"
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
            byte_cp =cliente_conexion.recv(2048)
           
            
           
            
            mensaje = cliente_conexion.recv(1024).decode()
         
           
            mensaje = desencriptar_paquete(mensaje) #mensaje filtrado
            if mensaje is not None:
            
                id_dron = list(mensaje.keys())[0]
                
                guardar_clave(id_dron,byte_cp)
                
                cliente_conexion.send(ack.encode())
                cargar_clave_publica(id_dron)
                cp =  cargar_clave_publica(id_dron)
                token= genera_token()
                encriptado = cifrar_con_clave_publica(token,cp)
                cliente_conexion.send(encriptado)
               
                try:
                   
                    primera_clave = next(iter(mensaje))
                 # Cambiar el atributo "token" para la primera clave
                    mensaje[primera_clave]["token"] ,mensaje[primera_clave]["Expiracion"]  = token.split("/")
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
        hostname = socket.gethostname()
        IPAddr = socket.gethostbyname(hostname)
        print("Your Computer IP Address is:" + IPAddr)
        conexion = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conexion.bind(("0.0.0.0", puerto))
        conexion.listen(50)
        #establecemos un tiempo de maximo en el que el servidor no tiene conxiones y si no las tiene lo cierra
        conexion.settimeout(600)


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
    if puerto.isnumeric(): 
               
        eliminar_claves()
         # Iniciar el servidor de Flask en un hilo separado
        flask_thread = threading.Thread(target=iniciar_flask)
        flask_thread.daemon = True
        flask_thread.start()
    
        registro(int(puerto))
        eliminar_claves()
        
    else:
        print("Error de puerto")
        sys.exit(1)

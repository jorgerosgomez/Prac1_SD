import socket
import sys
import json
import time
from time import sleep
from kafka import KafkaConsumer,KafkaProducer
import threading
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric import padding
import os
from cryptography.hazmat.backends import default_backend
import requests
from termcolor import colored
import ctypes
import os
import platform




file_Dron= 'Dron.json'



def color_windows():
    
    version = platform.version().split('.')
    if os.name == 'nt' and platform.release() == '10' and (int(version[0]), int(version[1]), int(version[2])) >= (10, 0, 14393):
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)

def registrar_mediante_api(self):
    
    url = f"https://{self.IP_Registry}:5001/registro"
    print(url)
    data = {
        "id": self.id,
        "alias": self.Alias
    }
    headers = {'Content-Type': 'application/json'}

    response = requests.post(url, json=data, headers=headers, verify=False)
    if response.status_code == 200:
        print("Registro exitoso.")
        self.token = response.json()[str(self.id)]['token']  # Almacenar el token
        threading.Thread(target=contador_expiracion).start()
        
    else:
        print("Error en el registro:", response.status_code)

def cargar_clave_publica():
    directorio = "claves_pub_engine_drones"
    nombre_archivo = "publica_engine_drones.pem"
    ruta_archivo = os.path.join(directorio, nombre_archivo)

    if not os.path.exists(ruta_archivo):
        print("Archivo de clave pública no encontrado.")
        return None

    with open(ruta_archivo, 'rb') as archivo_clave:
        clave_publica_bytes = archivo_clave.read()

    clave_publica = serialization.load_pem_public_key(
        clave_publica_bytes,
        backend=default_backend()
    )
    return clave_publica


def cifrar_con_clave_publica(mensaje, clave_publica):
    
    
    try:
        if isinstance(mensaje, str):
            mensaje_bytes = mensaje.encode('utf-8')
        else:
            mensaje_bytes = mensaje
    
        print(mensaje_bytes)
        mensaje_cifrado = clave_publica.encrypt(
            mensaje_bytes,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
    except Exception as e:
       print(f"es aqui : {e}")
    return mensaje_cifrado


def guardar_clave_publica(clave_publica_bytes):
    directorio = "claves_pub_engine_drones"
    nombre_archivo = "publica_engine_drones.pem"

    
    if not os.path.exists(directorio):
        os.makedirs(directorio)

    ruta_archivo = os.path.join(directorio, nombre_archivo)

   
    with open(ruta_archivo, 'wb') as archivo_clave:
        archivo_clave.write(clave_publica_bytes)


def eliminar_archivo(nombre_archivo, directorio):
  
   
    ruta_archivo = os.path.join(directorio, nombre_archivo)

    # Comprobar si el archivo existe
    if os.path.exists(ruta_archivo):
       
        os.remove(ruta_archivo)
        print(f"El archivo {ruta_archivo} ha sido eliminado.")
    else:
        print(f"El archivo {ruta_archivo} no existe.")

def desencriptar_con_clave_privada(clave_privada, mensaje_cifrado):
    try:
        mensaje_descifrado = clave_privada.decrypt(
            mensaje_cifrado,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return mensaje_descifrado
    except Exception as e:
        print(f"Error al desencriptar: {e}")
        return None

def cargar_clave_privada(id_dron):
    directorio = "claves_pri_dron"
    nombre_archivo = f"{id_dron}.pem"
    ruta_archivo = os.path.join(directorio, nombre_archivo)

    # Verificar si el archivo existe
    if not os.path.exists(ruta_archivo):
        print(f"No se encontró la clave para el dron con ID {id_dron}")
        return None

    # Leer la clave privada del archivo
    with open(ruta_archivo, 'rb') as archivo_clave:
        clave_privada_bytes = archivo_clave.read()
    
    # Deserializar la clave privada
    try:
        clave_privada = serialization.load_pem_private_key(
            clave_privada_bytes,
            password=None,
            backend=default_backend()
        )
        return clave_privada
    except Exception as e:
        print(f"Error al cargar la clave privada: {e}")
        return None


def guardar_clave_privada(id_dron, clave_privada_bytes):
    directorio = "claves_pri_dron"
    nombre_archivo = f"{id_dron}.pem"

    # Crear directorio si no existe
    if not os.path.exists(directorio):
        os.makedirs(directorio)

    ruta_archivo = os.path.join(directorio, nombre_archivo)

    # Guardar la clave privada en formato bytes
    with open(ruta_archivo, 'wb') as archivo_clave:
        archivo_clave.write(clave_privada_bytes)

def genera_claves():
   
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    public_key = private_key.public_key()
    
    private_key_serializada = private_key.private_bytes(
        encoding= serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
        
    )
    public_key_serializada = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    return private_key_serializada, public_key_serializada
    



def registrar_archivo():
    with open('dron.json', 'r') as file:
        return json.load(file)


config_destinos = {

    'auto_offset_reset' : 'latest', 
    'enable_auto_commit': False,
    'value_deserializer': lambda m: json.loads(m.decode('utf-8'))
}
config_mapa={
    'value_deserializer' :  lambda m: m.decode('utf-8')
}

def inicializar_productor(broker_address):
    return KafkaProducer(bootstrap_servers=broker_address,
            security_protocol="SSL",
            ssl_check_hostname=False,  # AL SER AUTOFIRMADO DEBERIAMOS HABER ESPECIFICADO LA IP CON LA QUE IBAMOS A TRABJAR PERO ES MEJOR NO HACER EL CHECK
            ssl_cafile="claves\mycert.crt",  
            ssl_certfile="claves\mycert.crt",  
            ssl_keyfile="claves/mykey.key",   
            value_serializer=lambda v: json.dumps(v).encode('utf-8'))

def inicializar_consumidor(topic_name, broker_address, consumer_config=None):
    if consumer_config is None:
        consumer_config = {}

    #ssl por defecto
    ssl_config = {
        'security_protocol': 'SSL',
        'ssl_check_hostname': False, 
        'ssl_cafile': 'claves/mycert.crt', 
        'ssl_certfile': 'claves/mycert.crt',  
        'ssl_keyfile': 'claves/mykey.key',  
    }
    # Configuracion
    default_config = {
        'bootstrap_servers': broker_address
    }

    final_config = {**default_config, **consumer_config, **ssl_config}


    # Inicializar el consumidor con la configuración final
    consumer = KafkaConsumer(topic_name, **final_config)
    return consumer
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
def consultar_mapa():
    global cerrar_hilos,perdida_conexion
     
    consultar_mapa =inicializar_consumidor('mapa',IP_Puerto_Broker)
    
    while cerrar_hilos:
          
        messages = consultar_mapa.poll(timeout_ms=15000)  # Obtiene los mensajes disponibles

        last_message = None
        for tp, msgs in messages.items():
            if msgs:
                last_message = msgs[-1]  # Tomar el último mensaje de la lista
               

        if not messages:
            perdida_conexion =True
            sys.exit()
        if last_message:
            mensaje_decodificado = last_message.value.decode('utf-8')
            mapa = mensaje_decodificado
            print(mapa)
               
def contador_expiracion():
    sleep(20)
    global ack_autenticado
    global final
    if ack_autenticado == False and final == False:
        print(" \n Su autenticación expiró solicite un nuevo token si quiere autenticarse en el especataculo \n -->", end="")
        
    

        


    
class AD_Drone:
    #CREAMOS LA CLASE DRON
    def __init__(self,id,Alias, IP_Engine, Puerto_Engine, Ip_Puerto_Broker,IP_Registry , Puerto_Registry,token =None):
        self.Alias= Alias
        self.id =  id #id del dispositivo
        self.IP_Engine= IP_Engine
        self.Puerto_Engine= Puerto_Engine
        self.Ip_Puerto_Broker =  Ip_Puerto_Broker
        self.token = token
        self.IP_Registry = IP_Registry
        self.Puerto_Registry= Puerto_Registry
        self.posicion = (0, 0)  # Posición inicial
    
    def conectar_al_servidor(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as cliente_conexion:
                servidor = (self.IP_Registry, self.Puerto_Registry)
                cliente_conexion.connect(servidor)
                enq = "<ENQ>"
                cliente_conexion.send(enq.encode())

                #Esperamos el ACK del servidor
                ack = cliente_conexion.recv(1024).decode()
                if ack == "<ACK>":
                    clave_privada, clave_publica = genera_claves()
                    guardar_clave_privada(self.id, clave_privada)
                    cliente_conexion.send(clave_publica)
                    print("Conexión exitosa.")
                    
                    opcion = input("option:\n1-Dar de alta\n2-Editar\n3-Dar de baja\n-->")
                    self.ejecutar_menu_registrar(opcion,cliente_conexion)
                else:
                    print(f"No hemos recibido el ACK, cerramos conexion: {ack}")
                    cliente_conexion.close()

        except socket.error as err:
            print(f"Error de socket: {err}")
            
        except Exception as e:
            print(f"ERROR:  {e}")
    
    def unirse_espectaculo(self):
        global ack_autenticado
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as servidor:
            servidor.connect((self.IP_Engine, self.Puerto_Engine))
            data_token = f"<STX>{self.id},{self.token}<ETX>"
            data_token = data_token + calcular_lrc(data_token)
         
            cp_engine = servidor.recv(2048)
            guardar_clave_publica(cp_engine)
            cp_engine= None
      

            data_cifrado = cifrar_con_clave_publica(data_token,cargar_clave_publica())
            print(data_cifrado)
            
            servidor.send(data_cifrado)          
            respuesta =  servidor.recv(1024).decode()
            consumer_destino =inicializar_consumidor('destinos',IP_Puerto_Broker,config_destinos)
            if respuesta == "<ACK>":
                ack_autenticado = True
                hilo_mapa=threading.Thread(target=consultar_mapa)
                print("autenticacion correcta")
                x_actual , y_actual = self.posicion
                payload = {
                    'ID': self.id,
                    'POS': (x_actual,y_actual)
                }
                
                for mensajes in consumer_destino:
                        
                                
                        destinos =  mensajes.value
                        break
                producer.send(topic='movimientos',value=payload)
                hilo_mapa.start()
                while True:    
                    
                    messages = consumer_destino.poll(timeout_ms=1000)  # Obtiene los mensajes disponibles

                    last_message = None
                    for tp, msgs in messages.items():
                        if msgs:
                            last_message = msgs[-1]  # Tomar el último mensaje de la lista

                    if last_message:
                        destinos = last_message.value

                    nombre_forma = destinos["Nombre"] 
                    for drones in destinos["Drones"]:
                        if drones["ID"]== self.id:
                            destino = tuple(map(int, drones["POS"].split(',')))
                    
                            print(f"El dron con ID {self.id} debe de {self.posicion} moverse a la posición {destino}")
                           
                            sleep(1.5)
                            self.mover_drone(destino)
                            if perdida_conexion == True:
                                print("PERDIDA DE CONEXION ABAJO")
                                print("Perdida de conexion con el servidor,Vuelvo a la base y me desconecto...")
                                sys.exit()
                                    
                            if nombre_forma == "Base" and self.posicion == (0,0):
                                sleep(2)
                                cerrar_hilos = False
                                print("El espectaculo ha terminado, Me desconecto...")
                                sys.exit()
                       
                                                        
                                            
                    
                            
                    
                        
                    
                
                
            elif respuesta == "<NACK>":
                print("error de autenticaion")
            else:
                print("Error por identificar")
   
    def mover_drone(self, destino):
        x_actual , y_actual = self.posicion
        x_final, y_final =  destino
           
        if x_actual < x_final:
            x_actual += 1
        elif x_actual > x_final:
            x_actual -= 1
                    
        if y_actual < y_final:
            y_actual += 1
        elif y_actual > y_final:
            y_actual -= 1
            
        self.posicion = (x_actual,y_actual)
        
            
        time.sleep(1)  # Esperar un segundo entre cada movimiento
            # Publicar la ubicación en Kafka
        nuestro_topic = 'movimientos'
        payload = {
            'ID': self.id,
            'POS': (x_actual,y_actual)
        }
        producer.send(topic=nuestro_topic,value=payload)
        sleep(1.5)
                 
    
    
    def registrar(self):
        #logica del registrar en AD_Registry
            
  
        eleccion=input("Registrar mediante socket ---> 1\nRegistras mediante API--->2\n")
        if(eleccion == "1"):
            try:
                self.conectar_al_servidor()
            except ConnectionRefusedError as e:
                    print(f"Error de tipo: {e}")
            except (socket.error, OSError) as e:
                    print(f"Error de socket: {e}")
            except Exception as e:
                    print(f"Error: {e}")
        elif(eleccion == "2"):
            registrar_mediante_api(self,)
        else:
            print("error al seleccionar una opcion")
    
    def ejecutar_menu_registrar(self, opcion, cliente_conexion):
        try:
            if opcion == '1':
                self.Dar_alta(cliente_conexion)
            elif opcion == '2':
                self.Editar()
            elif opcion == '3':
                self.Dar_baja()
            else:
                print("Opción no válida.")
                sys.exit(1)
        except Exception as e:
            print(f"Error en la ejecución del menú: {e}")
            sys.exit(1)
    
    def Dar_alta(self,cliente_conexion):
       
            stx, etx = "<STX>","<ETX>"
            dato =  {
                f"{self.id}":{
                    "alias": f"{self.Alias}",
                    "token": None
                }
            }   
          

            json_dato= json.dumps(dato)
            lrc =  calcular_lrc(stx + json_dato + etx)
            envio=  stx+ json_dato +etx +lrc
            cliente_conexion.send(envio.encode())
            ack = cliente_conexion.recv(1024).decode()
            if ack == "<ACK>":
                print("Mensaje enviado correctamente")
                print("tiene 20 segundos para conectarse")
                threading.Thread(target=contador_expiracion).start()
                token = cliente_conexion.recv(1024)
                c_pri= cargar_clave_privada(self.id)
                
                token = desencriptar_con_clave_privada(c_pri,token)
                token = token.decode('utf-8')

                self.token, self.Expiracion = token.split("/")
                
                cliente_conexion.close()
       
    def Dar_baja(self):
         print("por implementar")
    def Editar(self):
         print("por implementar")


#Separamos en dos los datos introducidos por parametros con el formato <IP:PUERTO>

def separar_arg(arg):
    parte=arg.split(':')
    return parte[0] , int(parte[1])    

if __name__ == "__main__":
    try:
        if len(sys.argv) == 5:
            print("Error de argumentos")
            sys.exit(1)
        else:
            color_windows()
            ack_autenticado = False 
            perdida_conexion =False
            final = False
            #registramos todos los puertos e ips introducidos por paramentros
            IP_Engine , Puerto_Engine =  separar_arg(sys.argv[1])
            IP_Puerto_Broker =  sys.argv[2]
            IP_Registry , Puerto_Registry =  separar_arg(sys.argv[3])
            producer =inicializar_productor(IP_Puerto_Broker)
            print("Puertos registrados...")
            drone_encontrado =False
            cerrar_hilos =True
            mapa = ""
            
            bd_json =registrar_archivo()
        
            id= int(input("Por favor, establece la ID del dispositivo\n-->"))

        
            Alias =  f"Dron {id}"
                # Crear una instancia de AD_Drone
            drone = AD_Drone(id,Alias, IP_Engine, Puerto_Engine, IP_Puerto_Broker, IP_Registry, Puerto_Registry)
     
                
            while True:
                menu = input("Elige una de las opciones:\n" +
                            "1-Registrar\n" +
                            "2-Unirse al espectaculo\n" +
                            "3-Salir\n-->")
                if menu == '1':
                    drone.registrar()
                elif menu == '2':
                    drone.unirse_espectaculo()
                elif menu == '3':
                    print("Saliendo...")
                    eliminar_archivo(f"{drone.id}.pem","claves_pri_dron")
                    final =True
                    break
                else:
                    print("Error de menú")
    except KeyboardInterrupt:
        print("DRON CERRADO MANUALMENTE...")
        
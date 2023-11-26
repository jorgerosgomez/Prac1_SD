import socket
import sys
import json
import time
from time import sleep
from kafka import KafkaConsumer,KafkaProducer
import threading



file_Dron= 'Dron.json'



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
    return KafkaProducer(bootstrap_servers=broker_address, value_serializer=lambda v: json.dumps(v).encode('utf-8'))

def inicializar_consumidor(topic_name, broker_address, consumer_config=None):
    if consumer_config is None:
        consumer_config = {}

    # Configuracion
    default_config = {
        'bootstrap_servers': broker_address
    }

    final_config = {**default_config, **consumer_config}

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
    if ack_autenticado == False:
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
            servidor.send(data_token.encode())          
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
        
            try:
               self.conectar_al_servidor()
            except ConnectionRefusedError as e:
                print(f"Error de tipo: {e}")
            except (socket.error, OSError) as e:
                print(f"Error de socket: {e}")
            except Exception as e:
                print(f"Error: {e}")

    
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
                token = cliente_conexion.recv(1024).decode()
                
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
            ack_autenticado = False 
            perdida_conexion =False
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
                    break
                else:
                    print("Error de menú")
    except KeyboardInterrupt:
        print("DRON CERRADO MANUALMENTE...")
import socket
import sys
import json
import time
from kafka import KafkaConsumer,KafkaProducer



file_Dron= 'Dron.json'


def inicializar_productor(broker_address):
    return KafkaProducer(bootstrap_servers=broker_address, value_serializer=lambda v: json.dumps(v).encode('utf-8'))

def inicializar_consumidor(topic, broker_address):
    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=broker_address,
        value_deserializer=lambda x: json.loads(x.decode('utf-8')),
    )
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




class AD_Drone:
    #CREAMOS LA CLASE DRON
    def __init__(self,id,Alias,IP_Engine , Puerto_Engine, Ip_Puerto_Broker,IP_Registry , Puerto_Registry):
        self.Alias= Alias
        self.id =  id #id del dispositivo
        self.IP_Engine= IP_Engine
        self.Puerto_Engine= Puerto_Engine
        self.Ip_Puerto_Broker =  Ip_Puerto_Broker
        self.IP_Registry = IP_Registry
        self.Puerto_Registry= Puerto_Registry
        self.posicion = (1, 1)  # Posición inicial
    
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
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as servidor:
            servidor.connect((self.IP_Engine, self.Puerto_Engine))
            
            data_token = f"<STX>{self.id},{self.token}<ETX>"
            data_token = data_token + calcular_lrc(data_token)
            servidor.send(data_token.encode())          
            respuesta =  servidor.recv(1024).decode()
            if respuesta == "<ACK>":
                print("autenticacion correcta")
                consumer =inicializar_consumidor('destinos',IP_Puerto_Broker)
                for mensajes in consumer:
                    # Procesa el primer mensaje recibido y luego rompe el bucle
                    destinos =  mensajes.value
                    consumer.close()  # Cierra el consumidor después de procesar el primer mensaje
                    break
                for drones in destinos["Drones"]:
                    if drones["ID"]== self.id:
                        destino = tuple(map(int, drone["POS"].split(',')))
                        print(f"El dron con ID {self.id} debe moverse a la posición {destino}")
                        #logica para moverse 
                        #self.posicion --> destino # cada vez que se mueva mandar un mensaje al topic movimiento
    
                        while self.posicion != destino:
                            self.mover_drone(destino)
                            #leer un topic de kafka que sea error
                            if error == True:
                                destino= (1,1)
                                while self.posicion != destino:
                                    self.mover_drone(destino)
                                print("Las condiciones son adversas volvemos a la base") 
                                exit(1)
                        #leer topic mapa y print 
                        
                    
                    else:
                        print(f"No se encontro destino para el dron con id:{self.id}")
                
                        
                    
                
                
            elif respuesta == "<NACK>":
                print("error de autenticaion")
            else:
                print("Error por identificar")
   
    def mover_drone(self, destino):
        x_actual , y_actual = self.posicion
        x_final, y_final = map(int, destino['POS'].split(','))
           
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
        nuetro_topic = 'movimientos'
        payload = {
            'ID': self.id,
            'POS': f"{x_actual},{y_actual}"
        }
        producer.send(topic=nuetro_topic,value=payload)
        print(f"Dron {self.id} se mueve a {x_actual},{y_actual}")
                 
    
    
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
                token = cliente_conexion.recv(1024).decode()
                dato[f"{id}"]['token'] =  token
                self.token = token
                incluir_json(file_Dron,dato) 
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
   
    if len(sys.argv) !=  4:
        print("Error de argumentos")
        sys.exit(1)
    else:
        #registramos todos los puertos e ips introducidos por paramentros
        IP_Engine , Puerto_Engine =  separar_arg(sys.argv[1])
        IP_Puerto_Broker =  sys.argv[2]
        IP_Registry , Puerto_Registry =  separar_arg(sys.argv[3])
        producer =inicializar_productor(IP_Puerto_Broker)
        print("Puertos registrados...")
        id= int(input("Por favor, establece la ID del dispositivo\n-->"))
        Alias =  input("Por favor, establece el alias del dispositivo\n-->")
         # Crear una instancia de AD_Drone
        drone = AD_Drone(id,Alias, IP_Engine, Puerto_Engine, IP_Puerto_Broker, IP_Registry, Puerto_Registry)
        while True:
            menu = input("Elige una de las opciones:\n" +
                        "1-Registrar\n" +
                        "2-Unirse al espectaculo\n" +
                        "3-Comprobar funcionamiento\n" +
                        "4-Salir\n-->")
            if menu == '1':
                drone.registrar()
            elif menu == '2':
                drone.unirse_espectaculo()
            elif menu == '3':
                print("Saliendo...")
                sys.exit(0)
            else:
                print("Error de menú")
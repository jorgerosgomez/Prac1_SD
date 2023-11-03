from time import sleep
import sys
from kafka import KafkaProducer , KafkaConsumer
from kafka.admin import KafkaAdminClient, NewTopic
from json import dumps
from threading import Lock
import json
import threading
import socket
import re
import time



file_engine = 'bd_Engine.json'
condicion_drones = threading.Condition()
drones_autenticados = []

# Configuración del servidor de clima
clima_servidor = "AD_weather"
clima_puerto = 12345  # El puerto del servidor de clima


def crecion_topics(administrador):
   #definimos los topics a crear
    topics = ["destinos","movimientos","mapa","error_topic"]
    num_partitions = 1
    replication_factor = 1
    #hacemos una lista de topics 
    topic_nuevo =   [NewTopic(name=topic, num_partitions=num_partitions, replication_factor=replication_factor) for topic in topics]
    #los creamos mediante la instacia de administrador de kafka_admin
    administrador.create_topics(new_topics=topic_nuevo, validate_only=False)

def verificar_drones_desconectados():
    while True:
        drones_a_eliminar = [drone for drone in drones_autenticados if drone.tiempo_sin_movimiento > 5]
        for drone in drones_a_eliminar:
            print(f"El dron con id {drone.identificador} ha perdido la conexión y se ha eliminado")
            drones_autenticados.remove(drone)
        time.sleep(1)  # verifica cada segundo si los drones no se han movido en 5 segundos

# Función para consultar el servidor de clima
def consultar_clima(clima_servidor,flag):
    while True:
        try:
            # Ciudad para consultar (reemplaza con la ciudad deseada)
            ciudad = "madrid"
            
            # Crear una solicitud en formato JSON
            solicitud = {"ciudad": ciudad}
            clima_servidor.send(json.dumps(solicitud).encode())

            # Recibir la respuesta del servidor de clima
            respuesta = clima_servidor.recv(1024).decode()
            datos_clima = json.loads(respuesta)
            temperatura = datos_clima["temperatura"]

            # Realizar acciones basadas en los datos del clima
            if float(temperatura) <= 0.0:
                with flag_lock:
                    flag == True

        except Exception as e:
            print(f"Error al consultar el servidor de clima: {str(e)}")

        time.sleep(5)  # Consulta cada 60 segundos
    

def inicializar_productor(broker_address):
    return KafkaProducer(bootstrap_servers=broker_address, value_serializer=lambda v: json.dumps(v).encode('utf-8'))


def inicializar_consumidor(topic, broker_address):
    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=broker_address,
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )
    return consumer


def leer_destinos(file_destinos):
    
    
    with open(file_destinos, 'r') as file:
        try:
            json_data = json.load(file)
        except json.JSONDecodeError:
            
                json_data = {}
    return json_data
    
    
    
    
def calcular_lrc(mensaje):
    bytes_mensaje = mensaje.encode('utf-8')
    
    lrc = 0
    # Calcular el LRC usando XOR
    for byte in bytes_mensaje:
        lrc ^= byte
     # Convertir el resultado a una cadena hexadecimal
    lrc_hex = format(lrc, '02X')
    
    return lrc_hex

def desempaquetar_string(paquete):
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

    data = paquete[inicio + len("<STX>"):fin]

    lrc_calculado = calcular_lrc(f"<STX>{data}<ETX>")

    # BUSCAMOS EL LRC DEL PAQUETE ORIGINAL
    lrc_inicio = fin + len("<ETX>")
    lrc_fin = lrc_inicio + 2
    lrc_paquete = paquete[lrc_inicio:lrc_fin]

    # Y LO COMPARAMOS
    if lrc_calculado != lrc_paquete:       
        print(f"Error en LRC: {lrc_paquete} != {lrc_calculado}")
        return None

    # Devolver la DATA como una cadena
    return data


def escuchar_conexiones(servidor, ad_engine):
    while True:
        conexion, direccion = servidor.accept()
        print(f"Conexión entrante de {direccion}")
        threading.Thread(target=manejar_conexion, args=(conexion, ad_engine)).start()


def iniciar_servidor(puerto, ad_engine):
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.bind(("0.0.0.0", int(puerto)))
    servidor.listen(20)
    servidor.settimeout(90)

    print(f"Escuchando en el puerto {puerto}")
    threading.Thread(target=escuchar_conexiones, args=(servidor, ad_engine)).start()
 
        
def manejar_conexion(conexion,ad_engine):
    #recibir datos del cliente (en este caso, asumimos que recibes id y token como cadena)
    global drones_autenticados, condicion_drones
    try:
        data = conexion.recv(1024).decode()
        data =desempaquetar_string(data)
        
        if not data:
            conexion.send("Formato incorrecto").encode()
            conexion.close()#le cerramos la conexion
        
        id_dron , token_dron = data.split(',')
        if ad_engine.conectar_dron(int(id_dron), token_dron):
            print( "Conexión exitosa")
            dron = Dron(identificador=int(id_dron),posicion=(0,0)) 
            with condicion_drones:
                drones_autenticados.append(dron)
                condicion_drones.notify()
            conexion.send("<ACK>".encode())
        else:
            print("No se pudo conectar el dron")
            conexion.send("<NACK>".encode())
    except Exception as e:
        print(f"Error: {e}")
        # Enviar respuesta al cliente
        conexion.send("<ACK>".encode())
    finally:
        # Cerrar la conexion
        conexion.close()
    
def separar_arg(arg):
    parte=arg.split(':')
    return parte[0] , int(parte[1]) 

def pintar_mapa(drones_autenticados, dimension=20):
    GREEN = '\033[92m'
    RED = '\033[91m'
    END = '\033[0m'
    
    # Convertir la lista de drones en un diccionario basado en el identificador del dron
    drones_dict = {dron.identificador: dron for dron in drones_autenticados}
    
    # Crear un mapa inicial vacío
    mapa = [[' ' for _ in range(dimension)] for _ in range(dimension)]
    
    for dron in drones_dict.values():
        x, y = dron.posicion
        if mapa[x][y] == ' ':
            mapa[x][y] = str(dron.identificador) 
        else:
            # Si hay más de un dron en la misma posición, mostrar el dron con ID menor
            mapa[x][y] = str(min(int(mapa[x][y]), dron.identificador))
    
    linea = []
    linea.append('    ' + ' '.join([f"{i:02}" for i in range(dimension)]))
    for i in range(dimension):
        linea_elemento = []
        for cell in mapa[i]:
            if cell != ' ':
                dron_id = int(cell)
                if drones_dict[dron_id].llego_a_destino: 
                    linea_elemento.append(GREEN + cell + END)
                else:
                    linea_elemento.append(RED + cell + END)
            else:
                linea_elemento.append(cell)
        linea.append(f"{i:02} | [" + "] [".join(linea_elemento) + "] | " + f"{i:02}")
    linea.append('    ' + ' '.join([f"{i:02}" for i in range(dimension)]))
    
    mapa = '\n'.join(linea)
    print(mapa)
    return mapa
    
class Dron:
    def __init__(self, identificador, posicion):
        self.identificador = identificador
        self.posicion = list(posicion)
        self.llego_a_destino = False
        self.ultimo_movimiento = None
    def llego_destino(self):
        self.llego_a_destino = True    

    def reset(self):
        self.llego_a_destino =False
        self.posicion= list(0,0)#posible fallo
    def actualizar_posicion(self, posicion):
        self.posicion = list(map(int, posicion.split(',')))
        self.ultimo_movimiento = time.time()
    def tiempo_sin_movimiento(self):
        return time.time() - self.ultimo_movimiento

class AD_Engine:
    
    def __init__(self):
        with open(file_engine) as f:
            self.lista_de_objetos = json.load(f)['lista_de_objetos']
        
        self.drones_conectados = 0

    def verificar(self,id,token):
        print("entra verificar")
        with open(file_engine) as f:
            self.lista_de_objetos = json.load(f)['lista_de_objetos']
        print(self.lista_de_objetos)
        for dron_info in self.lista_de_objetos:
            if str(id) in dron_info and dron_info[str(id)]['token'] == token:
                
                return True
        return False
    def conectar_dron(self, id, token):
        print(self.drones_conectados)
        
        if self.drones_conectados < int(numero_drones) and self.verificar(id, token):
            self.drones_conectados += 1
            return True
        else:
            print("false conectar")
            return False


if __name__ == "__main__":

    
    
    if len(sys.argv) != 5:
        print("Error de argumentos..")
        sys.exit(1)
        
       
        
    contador_conexiones = 0
    file_destinos = "fichero_destinos.json"
    flag = False
    flag_lock =  Lock()
    motor = AD_Engine()  
    puerto_escucha, numero_drones, ip_puerto_broker, ip_puerto_weather = sys.argv[1:5]
    ip_weather, puerto_weather = separar_arg(ip_puerto_weather)
    administrador  = KafkaAdminClient(bootstrap_servers = ip_puerto_broker)
    crecion_topics(administrador) 
    destinos = leer_destinos(file_destinos)
    producer = inicializar_productor(ip_puerto_broker)
    consumer = inicializar_consumidor('movimiento', ip_puerto_broker)
    iniciar_servidor(puerto_escucha, motor) 
    numero_drones_figura = len(destinos["figuras"][0]["Drones"])
    #esperamos que los drones necesarios se conecten desde el hilo 
    with condicion_drones:
        while len(drones_autenticados) < numero_drones_figura:
            print("Esperando la conexion de drones necesarios para iniciar el espectaculo....")
            condicion_drones.wait()
    input("Se han conectado los drones necesarios, pulse cualquier tecla para iniciar el espectaculo")
    threading.Thread(target=verificar_drones_desconectados).start()
    
    #conectarse al servidor de clima
    clima_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clima_socket.connect((clima_servidor, clima_puerto))
    threading.Thread(target=consultar_clima, args=(clima_socket)).start()#por implementar
    
    for figura in destinos["figuras"]:
        # Informa el inicio de la figura
        print(f"Comenzando a formar la figura: {figura['Nombre']}")

        # Manda la figura entera al broker destino
        producer.send('destinos', figura)

        # hasta que todos los drones no llegen a su destino de figura ...
        while not all(drone.llego_a_destino for drone in drones_autenticados):
            with flag_lock:
                flag_actual = flag
            if flag_actual:
                mensaje_error = "Error."
                producer.send('error_topic', value=mensaje_error.encode('utf-8'))
                producer.close()
                break 
                
            for posicion_actualizada in consumer:
                for drone in drones_autenticados:
                    if drone.identificador == posicion_actualizada["ID"] :
                            drone.actualizar_posicion(posicion_actualizada['POS'])
                            mapa = pintar_mapa(drones_autenticados)    
                            producer.send('mapa', value=mapa.encode('utf-8'))
                            break
                if all(drone.llego_a_destino for drone in drones_autenticados):
                    break                

        # final de fig
        print(f"Figura {figura['Nombre']} completada")
        #Estaran con llega_A_destino en true
        for dron in drones_autenticados:
            dron.reset()
    print("ha llegado el espectaculo al final")
    topic_borrar = ["destinos", "movimientos","mapa"]
    administrador.delete_topics(topic_borrar)
    producer.close()
    consumer.close()
    clima_socket.close()
    """
    #producer = KafkaProducer(bootstrap_servers='localhost:9092')
    drones_autenticados = []
    destinos = extraer_destinos("./fichero_destinos.txt")
    print(destinos)

    for i in range(1, 5):  # i va desde 1 hasta 4
        drone = Dron(i, (1, 1))
        drones_autenticados.append(drone)
    
    espacio = EspacioAereo(20, drones_autenticados)
    print("\t\t EL ESPECTÁCULO COMIENZA...")
    espacio.imprimir_mapa() 
    sleep(5)
    espacio.simulacion(destinos, drones_autenticados)
    """
    
    
  
from time import sleep
import sys
from kafka import KafkaProducer , KafkaConsumer
from kafka.admin import KafkaAdminClient, NewTopic
from json import dumps
from threading import Lock
import json
import threading
import socket
import time
import requests
import os 
from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/drones', methods=['GET'])
def get_drones():
    # Lógica para obtener la información de los drones
    drones_dict = [dron.to_dict() for dron in drones_autenticados]
    return jsonify(drones_dict)

@app.route('/')
def init():
    return "hello word"


@app.after_request
def after_request(response):
    response.headers["Access-Control-Allow-Origin"] = "*" # <- You can change "*" for a domain for example "http://localhost"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS, PUT, DELETE"
    response.headers["Access-Control-Allow-Headers"] = "Accept, Content-Type, Content-Length, Accept-Encoding, X-CSRF-Token, Authorization"
    return response  









file_engine = 'bd_Engine.json'
clima_adverso = False 
condicion_drones = threading.Condition()
drones_autenticados = []
GREEN = '\033[92m'
RED = '\033[91m'
END = '\033[0m'
Api_Key = "b0aa597e242f93ff1ec1681b38eea56b"



def iniciar_flask():
    app.run(host="0.0.0.0", debug=True, use_reloader=False, port=5000)  # Asegúrate de elegir un puerto adecuado

def pintando_mapas(drones_autenticados):
    global debe_continuar

    while debe_continuar:
        
        print(pintar_mapa(drones_autenticados))
        sleep(1)


def inicializar_json():
    data_inicial = {"lista_de_objetos": []}
    with open(file_engine, 'w') as file:
        json.dump(data_inicial, file, indent=4)

def limpia_registros():
    global debe_continuar
    while debe_continuar:
        try:
            with open(file_engine,"r") as file:
                datos = json.load(file)
            datos["lista_de_objetos"] = [obj for obj in datos["lista_de_objetos"] for key in obj if int(obj[key]["Expiracion"]) > time.time()]

        
            
            with open(file_engine, 'w') as file:
                json.dump(datos, file, indent=4)
        
        except Exception as e:
            print("Error de limpieza del json")
        sleep(1.5)
    
def complementar_destinos(destinos):
    destinos_data =  destinos
    ids = set(
        drone["ID"] for figura in destinos_data["figuras"] for drone in figura["Drones"]
    )
    for figura in destinos_data["figuras"]:
        ids_existentes = {drone["ID"] for drone in figura["Drones"]}
        for id in ids:
            if id not in ids_existentes:
                figura["Drones"].append({"ID": id, "POS": "0,0"})
    
    return destinos_data
    
    
    
def creacion_topics(administrador):
   #definimos los topics a crear
    topics = ["destinos","movimientos","mapa","error_topic"]
    num_partitions = 1
    replication_factor = 1
    #hacemos una lista de topics 
    topic_nuevo =   [NewTopic(name=topic, num_partitions=num_partitions, replication_factor=replication_factor) for topic in topics]
    #los creamos mediante la instacia de administrador de kafka_admin
    administrador.create_topics(new_topics=topic_nuevo, validate_only=False)

def verificar_drones_desconectados():
    global debe_continuar
    while debe_continuar :
        drones_a_eliminar = [drone for drone in drones_autenticados if drone.tiempo_sin_movimiento() > 8]
        for drone in drones_a_eliminar:
            print(f"El dron con id {drone.identificador} ha perdido la conexión y se ha eliminado")
            drones_autenticados.remove(drone)
        time.sleep(1)  # verifica cada segundo si los drones no se han movido en 5 segundos
    print("SE CIERRA")

#comprueba clima
def consultar_clima(lock):
    global clima_adverso
    global debe_continuar 
    API_URL = "http://api.openweathermap.org/data/2.5/weather?"
    while debe_continuar:
        try:
            with open("bd_Clima.txt", 'r') as file:
                nombre_ciudad = file.readline().strip()
            
            url_peticion = f"{API_URL}appid={Api_Key}&q={nombre_ciudad}"
            response = requests.get(url_peticion)
            response.raise_for_status()  # Lanza una excepción para respuestas no exitosas

            datos_clima = response.json()
            if 'main' in datos_clima:
                print("llega")
                temperatura_kelvin = datos_clima['main']['temp']
                temperatura_celsius = temperatura_kelvin - 273
                print(f"Temperatura en {nombre_ciudad}: {temperatura_celsius:.2f}°C")

                if temperatura_celsius < 0:
                    with lock:
                        print("Temperatura bajo cero,clima adverso DRONES A BASE.")
                        clima_adverso = True
                        debe_continuar = False

        except Exception as e:
            print(f"Error inesperado: {str(e)}")
            with lock:
                clima_adverso = True
            debe_continuar = False

            

        time.sleep(5)  # Consulta cada 5 segundos
    

def inicializar_productor(broker_address):
    return KafkaProducer(bootstrap_servers=broker_address)


def inicializar_consumidor(topic, broker_address):
    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=broker_address,
        enable_auto_commit=True, 
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
    global debe_continuar
    while debe_continuar:
        try:
            conexion, direccion = servidor.accept()
        except OSError :
            pass
        
        threading.Thread(target=manejar_conexion, args=(conexion, ad_engine,lock,)).start()
    


def iniciar_servidor(puerto, ad_engine):
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.bind(("0.0.0.0", int(puerto)))
    servidor.listen(20)
    servidor.settimeout(3000)

    print(f"Escuchando en el puerto {puerto}")
    hilo_conexiones= threading.Thread(target=escuchar_conexiones, args=(servidor, ad_engine))
    hilo_conexiones.start()
    return (servidor, hilo_conexiones)
 
        
def manejar_conexion(conexion,ad_engine,lock):
    
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
            with lock:
                with condicion_drones:
                    drones_autenticados.append(dron)             
                    condicion_drones.notify()
            conexion.send("<ACK>".encode())
        else:
            print("No se pudo conectar el dron")
            conexion.send("<NACK>".encode())
    except OSError:
        pass
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

    
    # Convertir la lista de drones en un diccionario basado en el identificador del dron
    drones_dict = {dron.identificador: dron for dron in drones_autenticados}
    
    # Crear un mapa inicial vacío
    mapa = [[' ' for _ in range(dimension)] for _ in range(dimension)]
    
    for dron in drones_dict.values():
        y, x = dron.posicion
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
        
    def actualizar_posicion(self, posicion):
        self.posicion = posicion
        self.ultimo_movimiento = time.time()
    def tiempo_sin_movimiento(self):
        if self.ultimo_movimiento is None:
            # Manejar adecuadamente si ultimo_movimiento es None
            # Por ejemplo, puedes inicializarlo con el tiempo actual
            self.ultimo_movimiento = time.time()
            return 0
        else:
            return time.time() - self.ultimo_movimiento
    def to_dict(self):
        return {
            "identificador": self.identificador,
            "posicion": self.posicion,
            "llego_a_destino": self.llego_a_destino,
            # Incluye otros campos que necesites enviar
    }


class AD_Engine:
    
    def __init__(self):
        with open(file_engine) as f:
            self.lista_de_objetos = json.load(f)['lista_de_objetos']
        
        self.drones_conectados = 0

    def verificar(self,id,token):
        with open(file_engine) as f:
            self.lista_de_objetos = json.load(f)['lista_de_objetos']
        for dron_info in self.lista_de_objetos:
            if str(id) in dron_info and dron_info[str(id)]['token'] == token:
                
                return True
        return False
    def conectar_dron(self, id, token):
        
        if self.drones_conectados < int(numero_drones) and self.verificar(id, token):
            self.drones_conectados += 1
            return True
        else:
            print("false conectar")
            return False


if __name__ == "__main__":

    
    
    if len(sys.argv) != 4:
        print("Error de argumentos..")
        sys.exit(1)
    try:    
        
        flask_thread = threading.Thread(target=iniciar_flask)
        flask_thread.start()
        inicializar_json()
        
        debe_continuar =True        
        clima_adverso = False  
        hilo_limpieza= threading.Thread(target=limpia_registros)
        hilo_limpieza.start()
        lock = threading.Lock()        
        contador_conexiones = 0
        file_destinos = "fichero_destinos.json"
        salir_con_fallo = False
        
        
        motor = AD_Engine()  
        puerto_escucha, numero_drones, ip_puerto_broker = sys.argv[1:4]
        administrador  = KafkaAdminClient(bootstrap_servers = ip_puerto_broker)
        try:
            creacion_topics(administrador) 
        except Exception as e:
            print(f"No se han creado los topics porque ya existen")
            
        destinos = leer_destinos(file_destinos)
        producer = inicializar_productor(ip_puerto_broker)
        consumer = inicializar_consumidor('movimientos', ip_puerto_broker)
        servidor , hilo_conexiones = iniciar_servidor(puerto_escucha, motor) 
        numero_drones_figura = len(destinos["figuras"][0]["Drones"])
        #esperamos que los drones necesarios se conecten desde el hilo 
        with condicion_drones:
            while len(drones_autenticados) < numero_drones_figura:
                print("Esperando la conexion de drones necesarios para iniciar el espectaculo....")
                condicion_drones.wait()
        input("Se han conectado los drones necesarios, pulse cualquier tecla para iniciar el espectaculo")
        threading.Thread(target=verificar_drones_desconectados).start()
        destinos = complementar_destinos(destinos)
        figura_base = {
            "Nombre": "Base",
            "Drones": [{"ID": dron.identificador, "POS": "0,0"} for dron in drones_autenticados]
        }
        print(figura_base)
        
        destinos["figuras"].append(figura_base)
        
    
        
        consultas_clima= threading.Thread(target=consultar_clima, args=(lock,))#consultas al clima
        consultas_clima.start()
        mostrar_mapa  = threading.Thread(target=pintando_mapas, args=(drones_autenticados,))
        mostrar_mapa.start()
    
        
        
        for figura in destinos["figuras"]:
            # Informa el inicio de la figura
            with lock:
                if clima_adverso:
                    break
            print(f"Comenzando a formar la figura: {figura['Nombre']}")

            sleep(1)
            # Manda la figura entera al broker destino
            producer.send('destinos', json.dumps(figura).encode('utf-8'))

            # hasta que todos los drones no llegen a su destino de figura ...
            while not all(drone.llego_a_destino for drone in drones_autenticados):
                #cuando lo ejecuto con el .bat llega hasta aqui, si los ejecuto indivudualmente pasa
        
                    

                    mensaje = consumer.poll(10000)  # Espera hasta 10,000 ms (10 segundos) para recibir un mensaje

                    if not mensaje:
                        print("Los drones se han desconectado")
                        salir_con_fallo =True
                        break
                    for tp, posiciones_actualizadas in mensaje.items():
                        for posicion_actualizada in posiciones_actualizadas:
                            with lock:
                                if clima_adverso:
                                    figura_actual = figura_base
                                else:
                                    figura_actual = figura
                            producer.send('destinos', json.dumps(figura_actual).encode('utf-8'))
                            posicion_actualizada = posicion_actualizada.value
                            for drone in drones_autenticados:
                                if drone.identificador == posicion_actualizada["ID"] :
                                        drone.actualizar_posicion(list(posicion_actualizada['POS']))
                                        destino_drone = next((list(map(int, d['POS'].split(','))) for d in figura_actual['Drones'] if d['ID'] == drone.identificador), None)
                                        if destino_drone and drone.posicion == destino_drone:
                                            drone.llego_a_destino = True
                                        mapa = pintar_mapa(drones_autenticados)    
                                        producer.send('mapa', value=mapa.encode('utf-8'))
                                        break
                            if all(drone.llego_a_destino for drone in drones_autenticados):
                                break  
                                
            
            if salir_con_fallo == True:
                break
            
                # final de fig
            print(f"Figura {figura['Nombre']} completada")
            #Estaran con llega_A_destino en true
            pintar_mapa(drones_autenticados)
            sleep(2)
            for dron in drones_autenticados:
                dron.reset()
        print("ha llegado el espectaculo al final")
        debe_continuar =False #lo usamos para cerrar los hilos
    
        try:
            
            producer.close()
            consumer.close()
        
            servidor.close()
        
        except Exception as e:
            print("saliendo...")
    except KeyboardInterrupt as k:
        
        debe_continuar = False
        sleep(10)
        try:
            
            producer.close()
            consumer.close()
      
            servidor.close()
        
        except Exception as e:
            print("saliendo...")
        print("hemos detenido al ejecucion de forma segura")  

        
        
    
from time import sleep
import sys
from kafka import KafkaProducer
from json import dumps
import json
import threading
import socket
import re



file_engine = 'bd_Engine.json'
drones_autenticados =[]



"""
def enviar_posiciones(drones_autenticados): 
    
    for dron in drones_autenticados:
        dron_id =  dron["id"]
        dron_posicion = dron["posicion"]
        serialized_position = f"{dron_posicion[0]},{dron_posicion[1]}".encode('utf-8')
        nombre_topic =  f"dron_posicion_{dron_id}"
        producer.send(nombre_topic,value=serialized_position)
"""

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

def extraer_destinos(ruta):
    with open(ruta, 'r') as file:
        content = file.read()

    #el patron busca cadenas que comiencen y terminen con una etiqueta (<TRIANGLE></TRIANGLE> ... )
    # y que contengan conjuntos de tres numeros entre ellas.
    pattern = r"<([A-Z]+)>\s*((?:<\d+><\d+><\d+>\s*)+)</\1>"

    destinos = {}

    for match in re.finditer(pattern, content):
        
         #extrae el nombre de la figura (por ejemplo, "TRIANGLE") de la coincidencia actual.
        figura = match.group(1)
        #extrae las coordenadas de la figura de la coincidencia actual.
        #estas coordenadas estan entre las etiquetas de inicio y fin de la figura.
        datos_bloque = content[match.start(2):match.end(2)]
        coordenadas = re.findall(r"<(\d+)><(\d+)><(\d+)>", datos_bloque)
        
        destinos_figura = []
        #itera sobre cada conjunto de coordenadas extraido
        for coord in coordenadas:
            #añade las coordenadas  a la lista
            id_val, x_val, y_val = coord
            destinos_figura.append({
                "id": int(id_val),
                "posicion": (int(x_val), int(y_val))
            })

        destinos[figura] = destinos_figura
        

    return destinos

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
            drones_autenticados.append(dron)
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


class EspacioAereo:#CREAMOS LA CLASE ESPACIO AEREO DONDE SIMULAREMOS UN ESPACIO 2D
    def __init__(self, dimension, lista_drones):#INICIALIZAMOS LA CLASE CON LAS VARIABLES
        self.dimension = dimension #DIMENSION QUE SERA DxD
        self.lista_drones = lista_drones #UNA LISTA DE DRONES QUE SERAN LOS DRONES PREVIAMENTE AUTENTICADOS
        self.mapa = [[' ' for _ in range(dimension)] for _ in range(dimension)] #UNA VARIABLE MAPA
        self.inicializar_mapa() #E INICIALIZAMOS CON LOS DRONES DENTRO QUE TENGAMOS EN NUESTRA LISTA DE DRONES AUTENTICADOS
        
    def inicializar_mapa(self):#INICIALIAR EL MAPA CONSISTE EN  MAPEAR EL MAPA COLOCANDO DRON EN LA POSICION QUE TOCA
        for dron in self.lista_drones:
            x, y = dron.posicion
            if self.mapa[x][y] == ' ':
                self.mapa[x][y] = str(dron.identificador) #EN LA POSCION DONDE HAY DRON SE ESCRIBIRA SU ID
            else:
                #SI HAY MAS DE UN DRON SERA EL ID CON MENOR NUMERO DE TODOS EL QUE APARECERA POR PANTALLA 
                self.mapa[x][y] = str(min(int(self.mapa[x][y]), dron.identificador))
                
    def actualizar_mapa(self): #ACTUALIZAR EL MAPA CONSISTE EN RESFRESCAR EL MAPA YA QUE LOS DRONES HABRAN CAMBIADO DE POSICION 
        self.mapa = [[' ' for _ in range(self.dimension)] for _ in range(self.dimension)]
        self.inicializar_mapa()
    
    def imprimir_mapa(self):  #AQUI IMPRIMIMOS EL MAPA 
        GREEN = '\033[92m'
        RED = '\033[91m'
        END = '\033[0m'
        lines = []
        lines.append('    ' + ' '.join([f"{i:02}" for i in range(self.dimension)]))
        for i in range(self.dimension):
            line_elements = []
            for cell in self.mapa[i]:
                if cell != ' ':
                    dron_id = int(cell)
                    if self.lista_drones[dron_id - 1].llego_a_destino:  # -1 porque la lista comienza en 0
                        line_elements.append(RED + cell + END)
                    else:
                        line_elements.append(GREEN + cell + END)
                else:
                    line_elements.append(cell)
            line = f"{i:02} | [" + "] [".join(line_elements) + "] | " + f"{i:02}"
            lines.append(line)
        lines.append('    ' + ' '.join([f"{i:02}" for i in range(self.dimension)]))
        
        full_map = '\n'.join(lines)
        print(full_map)
        #clean_map = re.sub(r'\033\[\d+m', '', full_map)
        #producer.send('mapa', value=clean_map.encode('utf-8'))
        
    

    def obtener_destino(self, dron_id, destinos):# ESTA FUNCION NOS CALCULARA DELVUELVE LA POSCION DE DESTINO DE CADA DRON
       
        for formacion, drones in destinos.items():
            for drone in drones:
                if drone["id"] == dron_id:
                    return drone["posicion"]
        return None
    
    def mover_drones_hacia_destinos(self, destinos):# ESTA FUNCION MUEVE LOS DRONES HACIA EL DESTINO QUE DEBEN IR Y ACTUALIZA EL MAPA
        for dron in self.lista_drones:
            destino = self.obtener_destino(dron.identificador, destinos)
            if destino:
                dron.mover_hacia_destino(destino)
        self.actualizar_mapa()
    def todos_llegaron_a_destino(self, drones): #COMPRUEBA SI TODOS LOS DRONES HAN LLEGADO AL DESTINO PARA ACABAR LA FUNCION Y SEGUIR CON LA SIGUIENTE FIGURA
        for dron in drones:
            if not dron.llego_a_destino:
                return False
        return True
    def simulacion(self, destinos_completos, drones_autenticados):
        for formacion_nombre in destinos_completos.keys():
            input(f"pulse cualquier boton para comenzar con la figura: {formacion_nombre}")
            print(f"Comenzando simulación para {formacion_nombre}...")
            #reseteamos la variable de ha llegado a su destino de los drones
            for dron in drones_autenticados:
                dron.reset()    
                        
            destinos = {formacion_nombre: destinos_completos[formacion_nombre]}
            
            
            while not self.todos_llegaron_a_destino(drones_autenticados):
                self.mover_drones_hacia_destinos(destinos)
                #enviar_posiciones(drones_autenticados)
                    
        
                print("\nMapa después de mover:")
                sleep(1)
                self.imprimir_mapa()
                

            print(f"\nTodos los drones han llegado a su destino para {formacion_nombre}!")
        
        print("\nSimulación completa para todas las formaciones!")
        
        #
        #producer.close()
        sys.exit(0)  # Termina el programa


class Dron:
    def __init__(self, identificador, posicion):
        self.identificador = identificador
        self.posicion = list(posicion)
        self.llego_a_destino = False
        
    def mover_hacia_destino(self, destino):
        dx = destino[0] - self.posicion[0]
        dy = destino[1] - self.posicion[1]
        
        if dx > 0: self.posicion[0] += 1
        elif dx < 0: self.posicion[0] -= 1

        if dy > 0: self.posicion[1] += 1
        elif dy < 0: self.posicion[1] -= 1

        if tuple(self.posicion) == destino:
            self.llego_a_destino = True
    def reset(self):
        self.llego_a_destino =False

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
        
    motor = AD_Engine()  
    puerto_escucha, numero_drones, ip_puerto_broker, ip_puerto_weather = sys.argv[1:5]
    ip_weather, puerto_weather = separar_arg(ip_puerto_weather)
    destinos = extraer_destinos("./fichero_destinos.txt")
    #productor_kafka = KafkaProducer(bootstrap_servers=f'{ip_puerto_broker}', value_serializer=lambda x: x.encode('utf-8'))
    iniciar_servidor(puerto_escucha, motor) 
    
   
    entrada=input("Pulse enter para empezar el espectáculo")   
    while entrada:
        print("No pulsate la tecla enter...")
        entrada = input("Pulse enter para empezar el espectáculo")
        
    espacio = EspacioAereo(20, drones_autenticados)
    print("\t\t EL ESPECTÁCULO COMIENZA...")
    espacio.imprimir_mapa() 
    sleep(5)
    espacio.simulacion(destinos, drones_autenticados)
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
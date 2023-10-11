from time import sleep
import sys
from kafka import KafkaProducer
from json import dumps
import json
import threading
import socket
import re


numero_drones = 100

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


def iniciar_servidor(puerto, ad_engine):
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.bind(('localhost', puerto))
    servidor.listen()

    print(f"Escuchando en el puerto {puerto}")

    while True:
        conexion, direccion = servidor.accept()
        print(f"Conexión entrante de {direccion}")

        #iniciar un hilo para manejar la conexion
        threading.Thread(target=manejar_conexion, args=(conexion,ad_engine)).start()
        
def manejar_conexion(conexion,ad_engine):
    #recibir datos del cliente (en este caso, asumimos que recibes id y token como cadena)
    try:
        data = conexion.recv(1024)
        data =desempaquetar_string(data)
        if not data:
            conexion.send("Formato incorrecto").encode()
            conexion.close()#le cerramos la conexion
        
        id_dron , token_dron = data.split(',')
        if ad_engine.conectar_dron(int(id_dron), token_dron):
            print( "Conexión exitosa")
            dron = Dron(identificador=int(id_dron), x=1, y=1) 
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
        #CREAMOS LAS VARIABLE DE COLOR PARA PODER PINTAR LOS DRONES SEGUN SE ESTAN MOVIENDO 
        print('    ' + ' '.join([f"{i:02}" for i in range(self.dimension)]))
        for i in range(self.dimension):
            line = []
            for cell in self.mapa[i]:
                if cell != ' ':
                    dron_id = int(cell)
                    if self.lista_drones[dron_id - 1].llego_a_destino:  # -1 porque la lista comienza en 0
                        line.append(RED + cell + END)
                    else: #DEPENDE SI EL DRON EN CUESTION DE LA LISTA LLEGO A SU DESTINO SE PINTARA DE UN COLOR  U OTRO
                        line.append(GREEN + cell + END)
                else:
                    line.append(cell)
            print(f"{i:02} | [" + "] [".join(line) + "] | " + f"{i:02}")
        print('    ' + ' '.join([f"{i:02}" for i in range(self.dimension)]))

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
    def simulacion(self, destinos, drones_autenticados):#HACE LA SIMULACION DEL ESPECTACULO
        from time import sleep
            
        while not self.todos_llegaron_a_destino(drones_autenticados):
            self.mover_drones_hacia_destinos(destinos)
            print("\nMapa después de mover:")
            sleep(1)
            self.imprimir_mapa()

        print("\nTodos los drones han llegado a su destino!")
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

class AD_Engine:
    
    def __init__(self, json_file):
        with open(json_file) as f:
            self.lista_de_objetos = json.load(f)['lista_de_objetos']

    def verificar(self,id,token):
        for dron_info in self.lista_de_objetos:
            if str(id) in dron_info and dron_info[str(id)]['token'] == token:
                return True
        return False
    def conectar_dron(self, id, token):
        if self.drones_conectados < numero_drones and self.verificar_dron(id, token):
            self.drones_conectados += 1
            return True
        else:
            return False


if __name__ == "__main__":

    if len(sys.argv) != 5:
        print("Error de argumentos..")
        sys.exit(1)
  
    destinos = extraer_destinos("./fichero_destinos.txt")


    
    drones_autenticados = []
        
    for i in range(1, 61):
        drone = Dron(identificador=i, posicion=(0,0))
        drones_autenticados.append(drone)
    print(len(drones_autenticados))

 
    espacio = EspacioAereo(20, drones_autenticados)
    print("\t\t EL ESPECTACULO COMIENZA...")
    espacio.imprimir_mapa() 
    sleep(5)
    espacio.simulacion(destinos, drones_autenticados)
    """"
    puerto_escucha, numero_drones, ip_puerto_broker, ip_puerto_weather = sys.argv[1:5]
    espacio = EspacioAereo(20, 20)
    ip_weather, puerto_weather = separar_arg(ip_puerto_weather)
    productor_kafka = KafkaProducer(bootstrap_servers=ip_puerto_broker, value_serializer=lambda x: dumps(x).encode('utf-8'))
    """
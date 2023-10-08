from time import sleep
import sys
from kafka import KafkaProducer
from json import dumps
import json
import threading
import socket
import re




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
            dron = Dron(identificador=int(id_dron), x=0, y=0) 
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


class Dron:
    def __init__(self, identificador, x, y):
        self.identificador = identificador
        self.llego_a_destino = False
        self.x = x
        self.y = y

    def mover(self, dx, dy):
        """Desplaza el dron en las direcciones dx y dy."""
        self.x += dx
        self.y += dy

    def establecer_destino(self, destino_x, destino_y):
        """Establece un destino para el dron."""
        self.destino_x = destino_x
        self.destino_y = destino_y
        self.llego_a_destino = False  # Resetear la condicion

    def comprobar_destino(self):
        """Comprueba si el dron ha llegado a su destino."""
        if self.x == self.destino_x and self.y == self.destino_y:
            self.llego_a_destino = True
        return self.llego_a_destino

class EspacioAereo:
    def __init__(self, filas, columnas):
        self.mapa = [[' ' for _ in range(columnas)] for _ in range(filas)]

    def colocar_dron(self, dron):
        x, y = dron.x, dron.y
        self.mapa[x][y] = dron  # Guardar la posición específica del dron

    def pintar_dron(self):
        # Imprimir las coordenadas superiores
        print('    ' + ' '.join(f'{i:02d}' for i in range(len(self.mapa[0]))))

        for i in range(len(self.mapa)):
            # Imprimir el número de fila
            print(f'{i:02d} |', end=' ')
            
            for j in range(len(self.mapa[0])):
                dron = self.mapa[i][j]
                if dron != ' ':
                    if dron.llego_a_destino:
                        print(f'\033[32m[{dron.identificador}]\033[0m', end=' ')  # Verde
                    else:
                        print(f'\033[31m[{dron.identificador}]\033[0m', end=' ')  # Rojo
                else:
                    print('[ ]', end=' ')

            print(f'| {i:02d}')  # Imprimir el número de fila al final

        # Imprimir las coordenadas inferiores
        print('    ' + ' '.join(f'{i:02d}' for i in range(len(self.mapa[0]))))

    def mover_dron(self, dron, tecla):
        x, y = dron.x, dron.y
        nueva_posicion = self.calcular_nueva_posicion(x, y, tecla)
        self.mapa[x][y] = ' '  # Limpiar la posición actual
        dron.x, dron.y = nueva_posicion
        self.colocar_dron(dron)

    def calcular_nueva_posicion(self, x, y, tecla):
        # Moverse
        if tecla == 'w':
            x -= 1
        elif tecla == 's':
            x += 1
        elif tecla == 'a':
            y -= 1
        elif tecla == 'd':
            y += 1
        return x, y

    def obtener_movimiento_hasta_posicion(self, dron, objetivo):
        dx = objetivo[0] - dron.x
        dy = objetivo[1] - dron.y

        if dx > 0:
            return 's'
        elif dx < 0:
            return 'w'
        elif dy > 0:
            return 'd'
        elif dy < 0:
            return 'a'
        else:
            return None  # Si ya estamos en la posición objetivo


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
     
    drones_autenticados = []    
   # ruta = input("Introduce ruta del fichero a procesar --> \n")
    destinos = extraer_destinos("C:\\Users\\jorge\\Desktop\\uni\\SD\\Prac 1\\fichero_destinos.txt")
    

    puerto_escucha, numero_drones, ip_puerto_broker, ip_puerto_weather = sys.argv[1:5]
    espacio = EspacioAereo(20, 20)
    ip_weather, puerto_weather = separar_arg(ip_puerto_weather)
    productor_kafka = KafkaProducer(bootstrap_servers=ip_puerto_broker, value_serializer=lambda x: dumps(x).encode('utf-8'))

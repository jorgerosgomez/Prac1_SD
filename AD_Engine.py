from time import sleep
import sys
from kafka import KafkaProducer
from  json import dumps



def separar_arg(arg):
    parte=arg.split(':')
    return parte[0] , int(parte[1]) 


class Dron:
    def __init__(self, identificador, x, y):
        self.identificador = identificador
        self.llego_a_destino = False
        self.x = x
        self.y = y

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
    
    def __init__(self) -> None:
        pass











if __name__ == "__main__":


    
    if len(sys.argv) != 5:
        print("Error de argumentos..")
        sys.exit(1)
  

    puerto_escucha, numero_drones, ip_puerto_broker, ip_puerto_weather =  sys.argv[1:5]
    espacio = EspacioAereo(20, 20)
    ip_weather, puerto_weather =  separar_arg	(ip_puerto_weather)
    productor_kafka = KafkaProducer(bootstrap_servers= ip_puerto_broker, value_serializer=lambda x: dumps(x).encode('utf-8'))

    
        
    
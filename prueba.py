import socket

def start_server():
    HOST = '0.0.0.0'  # Escucha en todas las interfaces
    PORT = 65432      # Puerto donde se escucharán las conexiones

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f'Esperando conexiones en {HOST}:{PORT}...')
        conn, addr = s.accept()
        conn.settimeout(90)
        with conn:
            print(f'Conexión establecida con {addr}')
            conn.sendall(b'Hola, cliente! Gracias por conectarte.')

if __name__ == "__main__":
    start_server()
    

import json
import time
from confluent_kafka import Producer

# Configuración del productor de Kafka
producer_config = {
    'bootstrap.servers': 'localhost:9092',  # Cambia esto a la dirección de tu servidor Kafka
    'client.id': 'drone_producer'
}

producer = Producer(producer_config)

# Cargar el archivo JSON
with open('destinos.json', 'r') as file:
    data = json.load(file)

# Acceder a la información de los drones en la figura
figura = data['figuras'][0]  # Supongo que solo hay una figura en tu archivo

# Obtener la lista de drones en la figura
drones = figura['Drones']

# Función para mover un dron a su siguiente posición adyacente
def move_drone(self, destino):
    x_actual , y_actual = self.posicion
    x_final, y_final = map(int, destino['POS'].split(','))
    while (x_actual, y_actual) != (x_final, y_final):
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
        topic = 'movimientos'
        payload = {
            'ID': self.id,
            'POS': f"{x_actual},{y_actual}"
        }
        producer.produce(topic, value=json.dumps(payload))
        print(f"Dron {self.id} se mueve a {x_actual},{y_actual}")

# Mover los drones uno por uno
for dron in drones:
    if dron['POS'] != figura['POS']:
        move_drone(dron)

# Imprimir la posición final de los drones
for dron in drones:
    print(f"Dron {dron['ID']} ha llegado a su posición final en {dron['POS']}")



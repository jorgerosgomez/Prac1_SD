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
def move_drone(dron):
    x, y = 1, 1  # Posición inicial
    x_final, y_final = map(int, dron['POS'].split(','))
    while (x, y) != (x_final, y_final):
        if x < x_final and y < y_final:
            x += 1
            y += 1
        elif x > x_final and y > y_final:
            x -= 1
            y -= 1
        elif x > x_final and y == y_final:
            x += 1
        elif x > x_final and y == y_final:
            x -= 1
        elif x == x_final and y < y_final:
            y += 1
        elif x == x_final and y > y_final:
            y -= 1
        elif x < x_final and y > y_final:
            x =+ 1
            y -= 1
        elif x > x_final and y < y_final:
            x -= 1

            y += 1
        dron['POS'] = f"{x},{y}"
        time.sleep(1)  # Esperar un segundo entre cada movimiento
        # Publicar la ubicación en Kafka
        topic = 'movimientos'
        payload = {
            'ID': dron['ID'],
            'POS': dron['POS']
        }
        producer.produce(topic, key=str(dron['ID']), value=json.dumps(payload))
        producer.flush()
        print(f"Dron {dron['ID']} se mueve a {dron['POS']}")

# Mover los drones uno por uno
for dron in drones:
    if dron['POS'] != figura['POS']:
        move_drone(dron)

# Imprimir la posición final de los drones
for dron in drones:
    print(f"Dron {dron['ID']} ha llegado a su posición final en {dron['POS']}")



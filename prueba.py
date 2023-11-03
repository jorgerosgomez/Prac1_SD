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
    

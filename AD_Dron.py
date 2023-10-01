import socket
import sys
import json 

def calcular_lrc(mensaje):
    bytes_mensaje = mensaje.encode('utf-8')
    
    lrc = 0
    # Calcular el LRC usando XOR
    for byte in bytes_mensaje:
        lrc ^= byte
     # Convertir el resultado a una cadena hexadecimal
    lrc_hex = format(lrc, '02X')
    
    return lrc_hex



class AD_Drone:
    #CREAMOS LA CLASE DRON
    def __init__(self,id,Alias,IP_Engine , Puerto_Engine, IP_Broker , Puerto_Broker,IP_Registry , Puerto_Registry):
        self.Alias= Alias
        self.id =  id
        self.IP_Engine= IP_Engine
        self.Puerto_Engine= Puerto_Engine
        self.IP_Broker = IP_Broker
        self.Puerto_Broker= Puerto_Broker
        self.IP_Registry = IP_Registry
        self.Puerto_Registry= Puerto_Registry
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
                    opcion = input("option:\n1-Dar de alta\n2-Editar\n3-Dar de baja")
                    self.ejecutar_menu_registrar(opcion,cliente_conexion)
                else:
                    print(f"No hemos recibido el ACK, cerramos conexion: {ack}")
                    cliente_conexion.close()

        except socket.error as err:
            print(f"Error de socket: {err}")
        except Exception as e:
            print(f"ERROR:  {e}")
    
    
    
    
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
                'id': self.id,
                'alias': self.Alias
            }   
            print(dato)
            json_dato= json.dumps(dato)
            lrc =  calcular_lrc(stx + json_dato + etx)
            envio=  stx+ json_dato +etx +lrc
            cliente_conexion.send(envio.encode())
            ack = cliente_conexion.recv(1024).decode()
            if ack == "<ACK>":
                print("Mensaje enviado correctamente")
                token = cliente_conexion.recv(1024).decode()
                print(f"Token recibido:  {token}")
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
        IP_Broker , Puerto_Broker =  separar_arg(sys.argv[2])
        IP_Registry , Puerto_Registry =  separar_arg(sys.argv[3])
        print("Puertos registrados...")
        id= int(input("Por favor, establece la ID del dispositivo"))
        Alias =  input("Por favor, establece el alias del dispositivo")
         # Crear una instancia de AD_Drone
        drone = AD_Drone(id,Alias, IP_Engine, Puerto_Engine, IP_Broker, Puerto_Broker, IP_Registry, Puerto_Registry)
        while True:
            menu =input("Elige una de las opciones:\n" +"1-Registrar\n" + "2-Unirse al espectaculo\n"+ "3-Comprobar funcionamiento")
            if (menu== '1'):
                drone.registrar()
            elif (menu=='2'):
                drone.unirse_espectaculo()
            elif(menu=='3'):
                drone.funcionamiento()
            else:
                print("Error de menu")
                sys.exit(1)

    

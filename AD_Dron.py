import socket
import sys





class AD_Drone:
    #CREAMOS LA CLASE DRON
    def __init__(self,IP_Engine , Puerto_Engine, IP_Broker , Puerto_Broker,IP_Registry , Puerto_Registry):
        self.IP_Engine= IP_Engine
        self.Puerto_Engine= Puerto_Engine
        self.IP_Broker = IP_Broker
        self.Puerto_Broker= Puerto_Broker
        self.IP_Registry = IP_Registry
        self.Puerto_Registry= Puerto_Registry
    def registrar(self):
        #logica del registrar en AD_Registry
        
            try:
                self.conectarse()
            except ConnectionRefusedError as e:
                print(f"Error de tipo: {e}")
            except (socket.error, OSError) as e:
                print(f"Error de socket: {e}")
            except Exception as e:
                print(f"Error: {e}")
        
            print("te has conectado")
           # opcion = input("option:\n1-Dar de alta\n2-Editar\n3-Dar de baja")
            #self.ejecutar_menu_registrar(opcion)
    
    def ejecutar_menu_registrar(self, opcion):
        try:
            if opcion == '1':
                self.Dar_alta()
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
    
    def Dar_alta(self):
         print("por implementar")
    def Dar_baja(self):
         print("por implementar")
    def Editar(self):
         print("por implementar")


        
    def conectarse(self):
        with socket.socket(socket.AF_INET6, socket.SOCK_STREAM) as conexion:
            servidor = (self.IP_Registry, self.Puerto_Registry)
            conexion.connect(servidor)

    def unirse_espectaculo(self):
        #logica unise al espectaculo
        print("Por implementar")

    def funcionamiento(self):
        print("Por implementar")

  





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

         # Crear una instancia de AD_Drone
        drone = AD_Drone(IP_Engine, Puerto_Engine, IP_Broker, Puerto_Broker, IP_Registry, Puerto_Registry)
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

    

    




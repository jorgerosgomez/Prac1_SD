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

    

    




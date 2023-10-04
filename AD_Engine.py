import time 
import sys

def separar_arg(arg):
    parte=arg.split(':')
    return parte[0] , int(parte[1]) 

class AD_Engine:
    
    def __init__(self) -> None:
        pass











if __name__ == "__main__":


    
    if len(sys.argv) != 5:
        print("Error de argumentos..")
        sys.exit(1)

    puerto_escucha, numero_drones, ip_puerto_broker, ip_puerto_weather =  sys.argv[1:5]
    
    ip_broker, puerto_broker =  separar_arg	(ip_puerto_broker)   
    ip_weather, puerto_weather =  separar_arg	(ip_puerto_weather)
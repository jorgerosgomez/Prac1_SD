# Usa una imagen base de Python
FROM python:3.9-slim

# Establece el directorio de trabajo en el contenedor
WORKDIR /app

# Instala las dependencias necesarias
RUN pip install kafka-python

# Copia los archivos necesarios al contenedor
COPY AD_Engine.py .
COPY fichero_destinos.txt .
COPY bd_Engine.json .
COPY entrypoint.sh /entrypoint.sh

# Da permisos de ejecución al script de entrada
RUN chmod +x /entrypoint.sh

# Usa el script de entrada como punto de entrada
ENTRYPOINT ["/entrypoint.sh"]

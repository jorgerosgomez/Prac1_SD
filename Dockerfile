# Usa una imagen base de Python
FROM python:3.9-slim

# Establece el directorio de trabajo en el contenedor
WORKDIR /app

# Instala las dependencias necesarias
RUN pip install kafka-python

# Copia el archivo AD_Engine.py al contenedor
COPY AD_Engine.py .
COPY fichero_destinos.txt .

# Comando para ejecutar cuando se inicie el contenedor
CMD ["python", "./AD_Engine.py", "12:12", "21:12", "21:22", "21:12"]

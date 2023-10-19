#!/bin/bash

# Recoge o solicita el primer parámetro
if [[ -z "${PARAM1}" ]]; then
    echo -n "Por favor, introduce el valor para PARAM1: "
    read param1
else
    param1="${PARAM1}"
fi

# Recoge o solicita el segundo parámetro
if [[ -z "${PARAM2}" ]]; then
    echo -n "Por favor, introduce el valor para PARAM2: "
    read param2
else
    param2="${PARAM2}"
fi

# Recoge o solicita el tercer parámetro
if [[ -z "${PARAM3}" ]]; then
    echo -n "Por favor, introduce el valor para PARAM3: "
    read param3
else
    param3="${PARAM3}"
fi

# Recoge o solicita el cuarto parámetro
if [[ -z "${PARAM4}" ]]; then
    echo -n "Por favor, introduce el valor para PARAM4: "
    read param4
else
    param4="${PARAM4}"
fi

# Ejecuta tu aplicación principal con los parámetros
python AD_Engine.py $param1 $param2 $param3 $param4

@echo off
FOR /L %%i IN (1,1,3) DO (
    START powershell -NoExit -Command "python AD_Dron.py 192.168.1.17:9999 192.168.1.17:9092 192.168.1.17:1111 --id %%i"
    timeout /t 1 /nobreak >nul
)

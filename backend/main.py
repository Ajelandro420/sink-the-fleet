from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, conint
import random

app = FastAPI()

# 🔹 CORS para permitir fetch desde frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 🔹 Modelo de partida
class Partida(BaseModel):
    filas: conint(ge=7, le=20)
    columnas: conint(ge=7, le=20)
    jugador: str = "Anònim"


# 🔹 Clase Tablero
class Tablero:
    def __init__(self, filas, columnas):
        self.filas = filas
        self.columnas = columnas
        self.grid = [[0 for _ in range(columnas)] for _ in range(filas)]

    def colocar_barco_aleatorio(self, tamaño):
        fila = random.randint(0, self.filas - 1)
        col = random.randint(0, self.columnas - 1)

        if col + tamaño <= self.columnas:
            for i in range(tamaño):
                self.grid[fila][col + i] = tamaño

    def generar_barcos_basicos(self):
        for tamaño in [1, 2, 3, 4, 5]:
            self.colocar_barco_aleatorio(tamaño)


# 🔹 Variable global tablero
tablero = None


# 🔹 Endpoint de prueba
@app.get("/prova")
async def prova():
    return {"estat": "ok", "dia": 3}


# 🔹 Crear partida
@app.post("/crearPartida")
async def crear_partida(partida: Partida):
    global tablero

    tablero = Tablero(partida.filas, partida.columnas)
    tablero.generar_barcos_basicos()

    return {
        "estat": "Partida creada!",
        "filas": partida.filas,
        "columnas": partida.columnas,
        "jugador": partida.jugador
    }


# 🔹 Disparar
@app.post("/disparar")
async def disparar(fila: int, columna: int):
    resultado = "agua"
    if tablero.grid[fila][columna] > 0:
        resultado = "tocado"

    return {"resultado": resultado}
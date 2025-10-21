from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, conint
import random

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Partida(BaseModel):
    filas: conint(ge=7, le=20)
    columnas: conint(ge=7, le=20)
    jugador: str = "Anònim"

class Tablero:
    def __init__(self, filas, columnas):
        self.filas = filas
        self.columnas = columnas
        self.grid = [[0 for _ in range(columnas)] for _ in range(filas)]
        self.barcos = []

    def colocar_barco_aleatorio(self, tamaño):
        while True:
            fila = random.randint(0, self.filas-1)
            col = random.randint(0, self.columnas-1)
            direccion = random.choice(['H', 'V'])
            posiciones = []

            if direccion == 'H' and col + tamaño <= self.columnas:
                posiciones = [(fila, col+i) for i in range(tamaño)]
            elif direccion == 'V' and fila + tamaño <= self.filas:
                posiciones = [(fila+i, col) for i in range(tamaño)]

            if posiciones and all(self.grid[r][c]==0 for r,c in posiciones):
                for r,c in posiciones:
                    self.grid[r][c] = tamaño
                self.barcos.append({'posiciones': posiciones, 'hundido': False})
                break

    def generar_barcos_basicos(self):
        for tamaño in [1, 2, 3, 4, 5]:
            self.colocar_barco_aleatorio(tamaño)

    def disparar(self, fila, col):
        if self.grid[fila][col] > 0:
            for barco in self.barcos:
                if (fila, col) in barco['posiciones']:
                    barco['posiciones'].remove((fila, col))
                    if not barco['posiciones']:
                        barco['hundido'] = True
                        return 'hundido'
                    return 'tocado'
        return 'agua'

tablero = None
estadisticas = {'dispars':0, 'encerts':0, 'vaixells_hundidos':0, 'puntuacio':0}

@app.get("/prova")
async def prova():
    return {"estat": "ok"}

@app.post("/crearPartida")
async def crear_partida(partida: Partida):
    global tablero, estadisticas
    tablero = Tablero(partida.filas, partida.columnas)
    tablero.generar_barcos_basicos()
    estadisticas = {'dispars':0, 'encerts':0, 'vaixells_hundidos':0, 'puntuacio':0}
    return {
        "estat": "Partida creada",
        "filas": partida.filas,
        "columnas": partida.columnas,
        "jugador": partida.jugador
    }

@app.post("/disparar")
async def disparar(fila: int, columna: int):
    global estadisticas
    if tablero is None:
        raise HTTPException(status_code=400, detail="No hay partida activa")

    resultado = tablero.disparar(fila, columna)
    estadisticas['dispars'] += 1
    if resultado in ['tocado','hundido']:
        estadisticas['encerts'] += 1
    if resultado == 'hundido':
        estadisticas['vaixells_hundidos'] += 1
    estadisticas['puntuacio'] = estadisticas['encerts']*10

    return {**estadisticas, "resultado": resultado}

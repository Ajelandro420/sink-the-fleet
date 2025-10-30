from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, conint
import math
import random

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# --- Carpeta de logs ---
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

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
        self.casillas_objetivo = math.floor(0.3*(filas * columnas))
        self.casillas_ocupadas = 0

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
            self.casillas_ocupadas += tamaño
            
        while self.casillas_ocupadas < self.casillas_objetivo:
            tamaño = random.randint(1, 5)
            self.colocar_barco_aleatorio(tamaño)
            self.casillas_ocupadas += tamaño


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

# --- Funciones de log ---
def crear_log(jugador, filas, columnas):
    global partida_id
    partida_id = str(uuid.uuid4())
    log_data = {
        "id_partida": partida_id,
        "jugador": jugador,
        "filas": filas,
        "columnas": columnas,
        "movimientos": [],
        "fecha_inicio": datetime.now().isoformat()
    }
    path = os.path.join(LOG_DIR, f"{partida_id}.json")
    with open(path, "w") as f:
        json.dump(log_data, f, indent=2)
    return partida_id


def log_disparo(fila, columna, resultado):
    if not partida_id:
        return
    path = os.path.join(LOG_DIR, f"{partida_id}.json")
    with open(path, "r") as f:
        log_data = json.load(f)
    log_data["movimientos"].append({
        "fila": fila,
        "columna": columna,
        "resultado": resultado,
        "hora": datetime.now().isoformat()
    })
    with open(path, "w") as f:
        json.dump(log_data, f, indent=2)


def finalizar_log(victoria, puntuacion):
    """Guarda el resultado final de la partida en el log."""
    if not partida_id:
        return
    path = os.path.join(LOG_DIR, f"{partida_id}.json")
    with open(path, "r") as f:
        log_data = json.load(f)
    log_data["final"] = {
        "victoria": victoria,
        "puntuacion": puntuacion,
        "hora_fin": datetime.now().isoformat()
    }
    with open(path, "w") as f:
        json.dump(log_data, f, indent=2)

@app.get("/prova")
async def prova():
    return {"estat": "ok"}

@app.post("/crearPartida")
async def crear_partida(partida: Partida):
    global tablero, estadisticas
    tablero = Tablero(partida.filas, partida.columnas)
    tablero.generar_barcos_basicos()
    estadisticas = {
        'dispars': 0,
        'encerts': 0,
        'vaixells_hundidos': 0,
        'puntuacio': 0
    }
    crear_log(partida.jugador, partida.filas, partida.columnas)
    return {
        "estat": "Partida creada",
        "filas": partida.filas,
        "columnas": partida.columnas,
        "jugador": partida.jugador,
        "id_partida": partida_id
    }
@app.post("/disparar")
async def disparar(fila: int, columna: int):
    global estadisticas
    if tablero is None:
        raise HTTPException(status_code=400, detail="No hay partida activa")

    resultado = tablero.disparar(fila, columna)
    estadisticas['dispars'] += 1
    if resultado in ['tocado', 'hundido']:
        estadisticas['encerts'] += 1
    if resultado == 'hundido':
        estadisticas['vaixells_hundidos'] += 1
    estadisticas['puntuacio'] = estadisticas['encerts'] * 10

    log_disparo(fila, columna, resultado)

    victoria = estadisticas['vaixells_hundidos'] == len(tablero.barcos)
    if victoria:
        finalizar_log(True, estadisticas['puntuacio'])

    return {**estadisticas, "resultado": resultado, "victoria": victoria}
@app.get("/ranking")
async def ranking():
    """Devuelve el top 10 de jugadores con mayor puntuación."""
    resultados = []
    for f in os.listdir(LOG_DIR):
        with open(os.path.join(LOG_DIR, f)) as archivo:
            data = json.load(archivo)
            if "final" in data:
                resultados.append({
                    "jugador": data["jugador"],
                    "puntuacion": data["final"]["puntuacion"],
                    "fecha": data["fecha_inicio"]
                })
    resultados.sort(key=lambda x: x["puntuacion"], reverse=True)
    return resultados[:10]
@app.get("/ranking")
async def get_ranking():
    registros = []
    for file in os.listdir(LOG_DIR):
        if file.endswith(".json"):
            path = os.path.join(LOG_DIR, file)
            with open(path, "r") as f:
                data = json.load(f)
                puntuacion = len([m for m in data.get("movimientos", []) if m["resultado"] in ["tocado", "hundido"]]) * 10
                registros.append({
                    "jugador": data.get("jugador", "Anònim"),
                    "puntuacion": puntuacion
                })
    registros.sort(key=lambda x: x["puntuacion"], reverse=True)
    return registros[:10]
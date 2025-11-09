from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing_extensions import Annotated
import math, random, os, json, uuid
from datetime import datetime

app = FastAPI()

frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")

app.mount("/static", StaticFiles(directory=frontend_path), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return FileResponse(os.path.join(frontend_path, "index.html"))

# --- Carpeta de logs ---
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# --- Estadísticas globales ---

DATA_DIR = "data"
STATS_PATH = os.path.join(DATA_DIR, "stats.json")

# Crea la carpeta "data" si no existe
os.makedirs(DATA_DIR, exist_ok=True)

# Datos por defecto si no hay archivo
DEFAULT_STATS = {
    "total_partidas": 0,
    "mejor_puntuacion": 0,
    "jugador_top": "",
    "promedio_disparos": 0.0,
    "promedio_encerts": 0.0,
    "top_players": []  # top 5
}

# Cargar estadísticas o crear
def load_stats():
    if not os.path.exists(STATS_PATH):
        with open(STATS_PATH, "w") as f:
            json.dump(DEFAULT_STATS, f, indent=2)
        return DEFAULT_STATS.copy()
    with open(STATS_PATH, "r") as f:
        return json.load(f)

# Guardar estadísticas actualizadas
def save_stats(stats):
    with open(STATS_PATH, "w") as f:
        json.dump(stats, f, indent=2)

# Actualizar estadísticas al finalizar partida
def actualizar_estadisticas_globales(jugador, puntuacion, dispars, encerts):
    stats = load_stats()
    stats["total_partidas"] += 1

    # Si hay una mejor puntuación, guardarla
    if puntuacion > stats["mejor_puntuacion"]:
        stats["mejor_puntuacion"] = puntuacion
        stats["jugador_top"] = jugador

    # Calcular promedios
    n = stats["total_partidas"]
    stats["promedio_disparos"] = round((stats["promedio_disparos"]*(n-1) + dispars) / n, 2)
    stats["promedio_encerts"] = round((stats["promedio_encerts"]*(n-1) + encerts) / n, 2)

    # Añadir al top 5
    top = stats.get("top_players", [])
    top.append({"jugador": jugador, "puntuacion": puntuacion})
    top = sorted(top, key=lambda x: x["puntuacion"], reverse=True)[:5]
    stats["top_players"] = top

    save_stats(stats)

class Partida(BaseModel):
    filas: Annotated[int, Field(ge=7, le=20)]
    columnas: Annotated[int, Field(ge=7, le=20)]
    jugador: str = "Anònim"

class Tablero:
    def __init__(self, filas, columnas):
        self.filas = filas
        self.columnas = columnas
        self.grid = [[0 for _ in range(columnas)] for _ in range(filas)]
        self.barcos = []
        self.casillas_objetivo = math.floor(0.3*(filas * columnas))
        self.casillas_ocupadas = 0
        self.disparadas = set()

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
                self.barcos.append({'posiciones': posiciones.copy(), 'hundido': False})
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
        if (fila, col) in self.disparadas:
            return 'repetido'
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
    """Cierra la partida y actualiza las estadísticas globales."""
    if not partida_id:
        return

    # Cargar log actual
    path = os.path.join(LOG_DIR, f"{partida_id}.json")
    with open(path, "r") as f:
        log_data = json.load(f)

    # Añadir datos finales
    log_data["final"] = {
        "victoria": victoria,
        "puntuacion": puntuacion,
        "hora_fin": datetime.now().isoformat()
    }

    # Guardar el log actualizado
    with open(path, "w") as f:
        json.dump(log_data, f, indent=2)

    # Actualizar estadísticas globales
    jugador = log_data.get("jugador", "Anónimo")
    dispars = estadisticas.get("dispars", 0)
    encerts = estadisticas.get("encerts", 0)
    actualizar_estadisticas_globales(jugador, puntuacion, dispars, encerts)


@app.get("/prova")
async def prova():
    return {"estat": "ok"}

@app.post("/crearPartida")
async def crear_partida(partida: Partida):
    global tablero, estadisticas, partida_id
    partida_id = str(uuid.uuid4())
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

    # Llamara a finalizar_log si la partida ha terminado
    finalizar_log(victoria, estadisticas['puntuacio'])

    return {**estadisticas, "resultado": resultado, "victoria": victoria}


@app.get("/top10")
async def top10():
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
# Endpoints de estadisticas globales
@app.get("/estadisticas")
async def estadisticas_globales():
    """Devuelve las estadísticas guardadas en data/stats.json"""
    return load_stats()

@app.get("/top5")
async def top5():
    """Devuelve el top 5 de jugadores"""
    stats = load_stats()
    return stats.get("top_players", [])

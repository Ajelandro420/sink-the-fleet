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

DEFAULT_STATS = {
    "total_partidas": 0,
    "mejor_puntuacion": 0,
    "jugador_top": "",
    "promedio_disparos": 0.0,
    "promedio_encerts": 0.0,
    "top_players": []  # top 5
}

def load_stats():
    if not os.path.exists(STATS_PATH):
        with open(STATS_PATH, "w") as f:
            json.dump(DEFAULT_STATS, f, indent=2)
        return DEFAULT_STATS.copy()
    with open(STATS_PATH, "r") as f:
        return json.load(f)

def save_stats(stats):
    with open(STATS_PATH, "w") as f:
        json.dump(stats, f, indent=2)

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

partidas_activas = {}

class PartidaActiva:
    def __init__(self, partida_id, tablero, jugador):
        self.id = partida_id
        self.tablero = tablero
        self.jugador = jugador
        self.estadisticas = {
            'dispars': 0,
            'encerts': 0,
            'vaixells_hundidos': 0,
            'puntuacio': 0
        }
        self.finalizada = False

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
            return 'repetido', None

        self.disparadas.add((fila, col))
        
        if self.grid[fila][col] > 0:
            for idx, barco in enumerate(self.barcos):
                if (fila, col) in barco['posiciones']:
                    barco['posiciones'].remove((fila, col))
                    if not barco['posiciones']:
                        barco['hundido'] = True
                        return 'hundido', idx
                    return 'tocado', idx
        return 'agua', None


# --- Funciones de log ---
def crear_log(partida_id,jugador, filas, columnas, tablero):
    
    barcos_info = []
    for idx, barco in enumerate(tablero.barcos):
        barcos_info.append({
            "id": idx,
            "posiciones": [[p[0], p[1]] for p in barco['posiciones']],  
            "tamaño": len(barco['posiciones']),
            "hundido": barco['hundido']
        })
    
    log_data = {
        "id_partida": partida_id,
        "jugador": jugador,
        "filas": filas,
        "columnas": columnas,
        "tablero": {
            "grid": tablero.grid,
            "barcos": barcos_info,
            "casillas_objetivo": tablero.casillas_objetivo,
            "casillas_ocupadas": tablero.casillas_ocupadas
        },
        "movimientos": [],
        "fecha_inicio": datetime.now().isoformat()
    }
    path = os.path.join(LOG_DIR, f"{partida_id}.json")
    with open(path, "w") as f:
        json.dump(log_data, f, indent=2)
    return partida_id


def log_disparo(partida_id, fila, columna, resultado, barco_afectado=None):
    if not partida_id:
        return
    path = os.path.join(LOG_DIR, f"{partida_id}.json")
    with open(path, "r") as f:
        log_data = json.load(f)
    
    movimiento = {
        "fila": fila,
        "columna": columna,
        "resultado": resultado,
        "hora": datetime.now().isoformat()
    }
    
    if barco_afectado is not None:
        movimiento["barco_id"] = barco_afectado
    
    log_data["movimientos"].append(movimiento)
    
    with open(path, "w") as f:
        json.dump(log_data, f, indent=2)


def finalizar_log(partida_id, jugador, victoria, puntuacion, estadisticas):
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
    
    dispars = estadisticas.get("dispars", 0)
    encerts = estadisticas.get("encerts", 0)
    actualizar_estadisticas_globales(jugador, puntuacion, dispars, encerts)

@app.get("/prova")
async def prova():
    return {"estat": "ok"}


@app.post("/crearPartida")
async def crear_partida(partida: Partida):
    print(f"[LOG] Creando partida para jugador: {partida.jugador}")

    partida_id = str(uuid.uuid4())
    tablero = Tablero(partida.filas, partida.columnas)
    tablero.generar_barcos_basicos()

    partida_activa = PartidaActiva(partida_id, tablero, partida.jugador)
    partidas_activas[partida_id] = partida_activa

    crear_log(partida_id, partida.jugador, partida.filas, partida.columnas, tablero)

    print(f"[LOG] Partida creada con ID: {partida_id} ({partida.filas}x{partida.columnas})")
    return {
        "estat": "Partida creada",
        "filas": partida.filas,
        "columnas": partida.columnas,
        "jugador": partida.jugador,
        "id_partida": partida_id
    }


@app.post("/disparar")
async def disparar(fila: int, columna: int, partida_id: str):
    print(f"[LOG] Disparo recibido: partida={partida_id}, fila={fila}, columna={columna}")

    if partida_id not in partidas_activas:
        raise HTTPException(status_code=404, detail="Partida no encontrada")

    partida_activa = partidas_activas[partida_id]

    if partida_activa.finalizada:
        raise HTTPException(status_code=400, detail="La partida ya ha finalizado")

    resultado, barco_id = partida_activa.tablero.disparar(fila, columna)
    partida_activa.estadisticas['dispars'] += 1

    if resultado in ['tocado', 'hundido']:
        partida_activa.estadisticas['encerts'] += 1
    if resultado == 'hundido':
        partida_activa.estadisticas['vaixells_hundidos'] += 1

    puntuacion_base = 1000
    costo_disparo = partida_activa.estadisticas['dispars'] * 10
    bonus_encerts = partida_activa.estadisticas['encerts'] * 20
    bonus_hundidos = partida_activa.estadisticas['vaixells_hundidos'] * 50

    partida_activa.estadisticas['puntuacio'] = max(0, puntuacion_base - costo_disparo + bonus_encerts + bonus_hundidos)

    log_disparo(partida_id, fila, columna, resultado, barco_id)

    victoria = partida_activa.estadisticas['vaixells_hundidos'] == len(partida_activa.tablero.barcos)

    if victoria:
        print(
            f"[LOG] Partida {partida_id} ganada por {partida_activa.jugador} con puntuación {partida_activa.estadisticas['puntuacio']}")
        partida_activa.finalizada = True
        finalizar_log(partida_id, partida_activa.jugador, victoria,
                    partida_activa.estadisticas['puntuacio'], partida_activa.estadisticas)

    print(
        f"[LOG] Resultado disparo: {resultado} | Puntuación actual: {partida_activa.estadisticas['puntuacio']}")
    return {**partida_activa.estadisticas, "resultado": resultado, "victoria": victoria}


@app.post("/abandonar")
async def abandonar_partida(partida_id: str):
    print(f"[LOG] Jugador abandona partida: {partida_id}")

    if partida_id in partidas_activas:
        partida_activa = partidas_activas[partida_id]

        if not partida_activa.finalizada:
            partida_activa.estadisticas['puntuacio'] = 0
            partida_activa.finalizada = True
            finalizar_log(partida_id, partida_activa.jugador, False,
                        partida_activa.estadisticas['puntuacio'], partida_activa.estadisticas)

        del partidas_activas[partida_id]
        print(f"[LOG] Partida {partida_id} eliminada del registro activo")
        return {"mensaje": "Partida abandonada"}

    raise HTTPException(status_code=404, detail="Partida no encontrada")


@app.get("/ranking")
async def get_ranking():
    print("[LOG] Solicitando ranking global...")
    registros = []
    for file in os.listdir(LOG_DIR):
        if file.endswith(".json"):
            path = os.path.join(LOG_DIR, file)
            with open(path, "r") as f:
                data = json.load(f)
                puntuacion = len(
                    [m for m in data.get("movimientos", []) if m["resultado"] in ["tocado", "hundido"]]) * 10
                registros.append({
                    "jugador": data.get("jugador", "Anònim"),
                    "puntuacion": puntuacion
                })
    registros.sort(key=lambda x: x["puntuacion"], reverse=True)
    print(f"[LOG] Ranking generado con {len(registros)} jugadores")
    return registros[:10]


@app.get("/estadisticas")
async def estadisticas_globales():
    """Devuelve las estadísticas guardadas en data/stats.json"""
    return load_stats()

@app.get("/top5")
async def top5():
    stats = load_stats()
    return stats.get("top_players", [])


app.get("/obtenerEstado")
async def obtener_estado(partida_id: str):
    if partida_id not in partidas_activas:
        raise HTTPException(status_code=404, detail="Partida no encontrada")
    
    partida_activa = partidas_activas[partida_id]
    
    return {
        **partida_activa.estadisticas,
        "finalizada": partida_activa.finalizada,
        "jugador": partida_activa.jugador
    }

@app.post("/reiniciarEstadisticas")
async def reiniciar_estadisticas():
    save_stats(DEFAULT_STATS.copy())
    return {"mensaje": "Estadísticas reiniciadas correctamente"}
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, conint

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
    dificultad: str

# 🔹 Endpoint de prueba
@app.get("/prova")
async def prova():
    return {"estat": "ok", "dia": 1}

# 🔹 Crear partida
@app.post("/crearPartida")
async def crear_partida(partida: Partida):
    # Aquí podrías crear la lógica de guardar la partida
    return {
        "estat": "Partida creada!",
        "filas": partida.filas,
        "columnas": partida.columnas,
        "dificultad": partida.dificultad
    }

# 🔹 Endpoint extra
@app.get("/endpoint")
async def endpoint():
    return {"info": "Endpoint extra"}

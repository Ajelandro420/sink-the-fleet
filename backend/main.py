from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
CORSMiddleware,
    allow_origins=["*"],
allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def inicio():
    return {"mensaje": "API funcionant"}

@app.get("/prova")
def prova():
    return {"estat": "Backend operatiu", "dia": 1}
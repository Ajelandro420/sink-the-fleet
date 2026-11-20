# Hundir la Flota

Juego clásico de **Hundir la Flota** para un jugador, con tablero de tamaño configurable, tres niveles de dificultad, puntuación y ranking global.
El backend es una API REST en **FastAPI** y el frontend una web estática en HTML, CSS y JavaScript puro. Todo se puede levantar con Docker Compose.

> Proyecto realizado en pareja como práctica de clase del ciclo de Desarrollo de Aplicaciones Web (DAW).

## Tecnologías

| Parte | Tecnología |
|---|---|
| Backend | Python, FastAPI, Uvicorn, Pydantic |
| Frontend | HTML, CSS y JavaScript (sin frameworks) |
| Despliegue | Docker, Docker Compose, Nginx (proxy inverso) |
| CI/CD | GitHub Actions (tests de humo y despliegue temporal con Ngrok) |

## Funcionalidades

- Tablero configurable de 7×7 hasta 20×20.
- Los barcos (tamaños de 1 a 5 casillas, en horizontal o vertical) se colocan de forma aleatoria; ocupan aproximadamente el 30 % del tablero.
- Tres dificultades (Fácil, Media, Difícil): pierdes si agotas el 80 %, 65 % o 50 % de las casillas en disparos sin hundir toda la flota.
- Puntuación: parte de 1000, resta 10 por disparo y suma 20 por acierto y 50 por barco hundido.
- Efectos de sonido (agua, tocado, hundido, victoria y derrota).
- Ranking Top 10 y estadísticas globales (partidas jugadas, mejor puntuación, medias de disparos y aciertos).
- Registro en JSON de cada partida, con todos sus movimientos.

## Cómo ejecutarlo

### Con Docker Compose

Requiere Docker.

```bash
docker compose up --build
```

Abre <http://localhost> en el navegador. Nginx sirve el frontend y reenvía el resto de peticiones al backend. Las partidas y las estadísticas se guardan en volúmenes de Docker.

### En local, sin Docker

Requiere Python 3. Desde la raíz del proyecto:

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows (en Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt
cd backend
uvicorn main:app --reload
```

Abre <http://localhost:8000>. En este modo FastAPI sirve también el frontend. La documentación interactiva de la API está en <http://localhost:8000/docs>.

Al jugar se crean las carpetas `data/` y `logs/` junto al backend.

## API

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/prova` | Comprobación de que el servidor está activo |
| POST | `/crearPartida` | Crea una partida (`filas`, `columnas`, `jugador`) y devuelve su `id_partida` |
| POST | `/disparar` | Dispara a una casilla (`fila`, `columna`, `partida_id`) y devuelve resultado y puntuación |
| POST | `/abandonar` | Abandona la partida (`partida_id`) |
| GET | `/obtenerEstado` | Estado y estadísticas de una partida activa (`partida_id`) |
| GET | `/ranking` | Top 10 de jugadores |
| GET | `/top5` | Top 5 de puntuaciones guardadas |
| GET | `/estadisticas` | Estadísticas globales |
| POST | `/reiniciarEstadisticas` | Reinicia las estadísticas globales |

## Despliegue y CI

- `.github/workflows/test.yml`: en cada push o pull request a `main` comprueba la sintaxis del backend, arranca la API y consulta `/prova` (Python 3.11).
- `.github/workflows/deploy.yml`: se lanza a mano desde la pestaña *Actions*. Levanta los contenedores y expone el frontend 10 minutos mediante un túnel Ngrok. Necesita el secreto `NGROK_AUTHTOKEN` en *Settings → Secrets and variables → Actions*.
- Más detalles en [document-desplegament.md](document-desplegament.md).

## Estructura

```
.
├── backend/              # API FastAPI (main.py)
├── frontend/             # index.html, app.js, style.css y sonidos
├── .github/workflows/    # test.yml y deploy.yml
├── Dockerfile.backend
├── Dockerfile.frontend
├── docker-compose.yml
├── nginx.conf
└── requirements.txt
```

## Autores

- **Alejandro Asensio Díaz** — [@Ajelandro420](https://github.com/Ajelandro420)
- **Ismail Kouira** — [@Tabascx](https://github.com/Tabascx)

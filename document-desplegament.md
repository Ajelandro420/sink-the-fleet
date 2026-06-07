================================================================================
1. ARQUITECTURA DEL DESPLEGAMENT
================================================================================

El projecte es desplega en 2 contenidors Docker independents que es
comuniquen entre ells mitjancant una xarxa interna de Docker (bridge).

Esquema:

    Internet (Navegador)
           |
    Ngrok (tunel HTTPS public)
           |
    Port 80 del Runner de GitHub Actions
           |
    +------------------+         +-------------------+
    |   FRONTEND       |         |    BACKEND        |
    |   (Nginx)        | <-----> |  (FastAPI+Uvicorn)|
    |   Port 80        |  xarxa  |    Port 8000      |
    |                  | interna |                   |
    | Serveix:         |         | API REST:         |
    |  index.html      |         |  POST /crearPartida|
    |  /static/*.css   |         |  POST /disparar   |
    |  /static/*.js    |         |  POST /abandonar  |
    |  /static/assets/ |         |  GET  /ranking    |
    |                  |         |  GET  /estadistiques|
    | Proxy invers:    |         |  GET  /top5       |
    |  rutes API -->   |         |  POST /reiniciar  |
    |  backend:8000    |         |                   |
    +------------------+         +-------------------+
                                         |
                                    Volums Docker:
                                    - /app/data
                                    - /app/logs

================================================================================
2. CONTENIDOR 1: BACKEND (FastAPI + Uvicorn)
================================================================================

Fitxers:
  - Dockerfile.backend     (instruccions per construir la imatge)
  - requirements.txt       (dependencies de Python)
  - backend/main.py        (codi de l'API)

Imatge base: python:3.13-slim

Funcionament:
  1. Copia el codi de backend/ al contenidor dins /app/
  2. Instal·la les dependencies: fastapi, uvicorn, pydantic
  3. Crea les carpetes /app/data i /app/logs (persistencia)
  4. Arrenca Uvicorn al port 8000 amb:
       uvicorn main:app --host 0.0.0.0 --port 8000

API REST que exposa:
  - POST /crearPartida   -> Crea una nova partida de Hundir la Flota
  - POST /disparar        -> Dispara a una casella del tauler
  - POST /abandonar       -> Abandona la partida actual
  - GET  /ranking         -> Retorna el top 10 de jugadors
  - GET  /estadisticas    -> Retorna estadistiques globals
  - GET  /top5            -> Retorna el top 5 de jugadors
  - POST /reiniciarEstadisticas -> Reinicia les estadistiques
  - GET  /prova           -> Health check ({"estat": "ok"})

Modificacions fetes al codi original:
  - El muntatge de fitxers estatics (/static/) es condicional:
    nome's s'activa si la carpeta frontend/ existeix al contenidor.
    Com que en Docker el frontend el serveix Nginx, no cal.
  - La ruta arrel (GET /) retorna {"app": "Hundir la Flota API"} si
    no troba la carpeta frontend, evitant errors.

================================================================================
3. CONTENIDOR 2: FRONTEND (Nginx)
================================================================================

Fitxers:
  - Dockerfile.frontend    (instruccions per construir la imatge)
  - nginx.conf             (configuracio del servidor Nginx)
  - frontend/index.html    (pagina principal del joc)
  - frontend/app.js        (logica del client, crides API)
  - frontend/style.css     (estils CSS)
  - frontend/assets/*.mp3  (efectes de so)

Imatge base: nginx:alpine (la mes lleugera, ~5MB)

Funcionament:
  1. Copia nginx.conf a /etc/nginx/conf.d/default.conf
  2. Copia index.html a /usr/share/nginx/html/
  3. Copia app.js i style.css a /usr/share/nginx/html/static/
  4. Copia els assets .mp3 a /usr/share/nginx/html/static/assets/
  5. Nginx escolta al port 80 i:
     - Si la peticio es un fitxer estatic (.html, .css, .js, .mp3),
       el serveix directament del disc.
     - Si el fitxer no existeix (rutes de l'API com /crearPartida),
       fa de proxy invers i reenvia la peticio al backend:8000.

Perque el proxy funcioni, s'ha canviat el fitxer app.js:
  Abans:  const API_URL = "http://localhost:8000";
  Ara:    const API_URL = "";
  Aixo fa que les crides fetch() utilitzin URLs relatives (/crearPartida,
  /disparar, etc.) i Nginx les redirigeix al backend automaticament.

Avantatges del proxy invers amb Nginx:
  - No hi ha problemes de CORS (tot es servit des del mateix origen).
  - El backend no necessita estar exposat a Internet.
  - Nginx es molt eficient servint fitxers estatics.

================================================================================
4. ORQUESTRACIO: docker-compose.yml
================================================================================

Docker Compose gestiona els dos contenidors com un conjunt:

  - Crea una xarxa interna "hundir-net" (bridge) perque els contenidors
    es puguin comunicar entre ells pel nom del servei (ex: "backend").
  - El backend NO exposa ports al host. Nomes es accessible desde dins
    de la xarxa interna.
  - El frontend SI exposa el port 80 al host perque Ngrok hi pugui
    connectar.
  - El backend te volums persistents per a /app/data i /app/logs.
  - El frontend depen del backend (depends_on) per assegurar l'ordre
    d'arrencada.

================================================================================
5. TUNEL NGROK
================================================================================

Ngrok crea un tunel HTTPS desde un domini public temporal (ex:
https://abc123.ngrok-free.app) fins al port 80 del runner de GitHub
Actions, on esta executant-se el contenidor del Frontend amb Nginx.

Token d'autenticacio:
  Es necessita un compte gratuit a ngrok.com. El token es guarda com a
  secret de GitHub (NGROK_AUTHTOKEN) i s'injecta durant l'execucio del
  workflow.

El workflow:
  1. Descarrega el binari de Ngrok v3
  2. Configura l'authtoken
  3. Inicia ngrok http 80 en segon pla
  4. Consulta l'API local de Ngrok (port 4040) per obtenir la URL publica
  5. Mostra la URL als logs del workflow
  6. Manten el tunel obert durant 10 minuts (sleep 600)
  7. Al finalitzar, para i elimina els contenidors amb docker compose down

================================================================================
6. RESUM DEL WORKFLOW (GitHub Actions)
================================================================================

Arxiu: .github/workflows/deploy.yml

Trigger: workflow_dispatch (execucio manual)

Passos:
  1. Descarregar codi         (actions/checkout@v4)
  2. docker compose up -d     (construir i arrencar contenidors)
  3. Esperar 5s               (donar temps als serveis)
  4. Instal·lar Ngrok         (descarregar binari + configurar token)
  5. Iniciar tunel Ngrok      (ngrok http 80 &)
  6. Obtenir URL publica      (curl a l'API de Ngrok)
  7. Esperar 10 minuts        (sleep 600)
  8. Netejar contenidors      (docker compose down -v)

El workflow te un timeout de 15 minuts i el pas de neteja s'executa
sempre (if: always()), fins i tot si algun pas falla.

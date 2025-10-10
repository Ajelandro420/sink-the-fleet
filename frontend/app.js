console.log("Frontend Dia 2: Estructura de blocs");

let gameId = null;

// Elements del DOM
const bloc1 = document.getElementById('bloc1');
const bloc2 = document.getElementById('bloc2');
const bloc3 = document.getElementById('bloc3');
const formConfig = document.getElementById('formConfig');
const tableroDiv = document.getElementById('tablero');

// Event: Crear partida
document.getElementById('btnComencar').addEventListener('click', async () => {
    const files = parseInt(document.getElementById('files').value);
    const columnes = parseInt(document.getElementById('columnes').value);
    const jugador = document.getElementById('jugador').value || 'Anònim';
    
    console.log(`Creant partida: ${files}x${columnes}, Jugador: ${jugador}`);
    
    // TEST FRONTEND SIN BACKEND
    mostrarBlocs2y3(files, columnes);
});

function mostrarBlocs2y3(files, columnes) {
    // Ocultar bloc 1
    bloc1.style.display = 'none';
    
    // Mostrar blocs 2 i 3
    bloc2.style.display = 'flex';
    bloc3.style.display = 'flex';
    
    generarTablero(files, columnes);
}

function generarTablero(files, columnes) {
    // Configurar grid
    tableroDiv.style.gridTemplateColumns = `repeat(${columnes}, 40px)`;
    tableroDiv.style.gridTemplateRows = `repeat(${files}, 40px)`;
    
    // Vaciar tablero
    tableroDiv.innerHTML = '';
    
    // Crear casillas
    for (let i = 0; i < files; i++) {
        for (let j = 0; j < columnes; j++) {
            const casilla = document.createElement('div');
            casilla.className = 'casilla';
            casilla.dataset.fila = i;
            casilla.dataset.columna = j;
            
            casilla.addEventListener('click', () => {
                dispararCasilla(i, j, casilla);
            });
            
            tableroDiv.appendChild(casilla);
        }
    }
}

function dispararCasilla(fila, columna, casilla) {
    // De momento solo cambia el color (sin backend)
    console.log(`Disparo a: (${fila}, ${columna})`);
    
    // Simulación 
    const random = Math.random();
    if (random > 0.7) {
        casilla.classList.add('tocado');
        casilla.textContent = '💥';
        document.getElementById('encerts').textContent =
            parseInt(document.getElementById('encerts').textContent) + 1;
    } else {
        casilla.classList.add('agua');
        casilla.textContent = '💧';
    }
    
    // Actualizar stats (simulado)
    document.getElementById('dispars').textContent = 
        parseInt(document.getElementById('dispars').textContent) + 1;


    // Desactiva botón
    casilla.classList.add('disparada');
    casilla.style.cursor = 'not-allowed';
}
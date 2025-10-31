const API_URL = "http://localhost:8000";
let jugador = "Anònim";
let totalCasillas = 0;
let dificultad = 0;

let bloc1, bloc2, bloc3, tableroDiv, mensajeVictoria, sonidos = {};

document.addEventListener('DOMContentLoaded', () => {
    bloc1 = document.getElementById('bloc1');
    bloc2 = document.getElementById('bloc2');
    bloc3 = document.getElementById('bloc3');
    tableroDiv = document.getElementById('tablero');
    mensajeVictoria = document.getElementById('mensajeVictoria');

    // EZ DJ
    sonidos = {
        tocado: document.getElementById('hit'),
        hundido: document.getElementById('sunken'),
        agua: document.getElementById('miss'),
        ganar: document.getElementById('win'),
        perder: document.getElementById('lose')
    };
}); 

function reproducirSonido(tipo) {
    if (sonidos[tipo]) {
        sonidos[tipo].currentTime = 0; // Reinicia el sonido
        sonidos[tipo].play().catch(e => console.log('Error reproduciendo sonido:', e));
    }
}

document.getElementById('btnComencar').addEventListener('click', async () => {
    const filas = parseInt(document.getElementById('files').value);
    const columnas = parseInt(document.getElementById('columnes').value);
    totalCasillas = filas * columnas;
    dificultad = document.querySelector('input[name="dificultat"]:checked').value;


    jugador = document.getElementById('jugador').value || "Anònim";

    try {
        await fetch(`${API_URL}/crearPartida`, {
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body: JSON.stringify({filas,columnas,jugador})
        });
        mostrarBlocs(filas,columnas);
    } catch(e){console.error(e);}
});
document.getElementById('btnAbandonar').addEventListener('click', reiniciarJuego);
function reiniciarJuego() {
    bloc2.style.display = "none";
    bloc3.style.display = "none";
    bloc1.style.display = "flex";

    tableroDiv.innerHTML = "";

    // Restablecer stats
    document.getElementById('dispars').textContent = "0";
    document.getElementById('encerts').textContent = "0";
    document.getElementById('enfonsats').textContent = "0";
    document.getElementById('puntuacio').textContent = "0";

    // Ocultar mensaje de victoria
    mensajeVictoria.style.display = "none";
}

function mostrarBlocs(filas,columnas){
    bloc1.style.display="none";
    bloc2.style.display="flex";
    bloc3.style.display="flex";
    generarTablero(filas,columnas);
}

function generarTablero(filas,columnas){
    tableroDiv.style.gridTemplateColumns = `repeat(${columnas},40px)`;
    tableroDiv.style.gridTemplateRows = `repeat(${filas},40px)`;
    tableroDiv.innerHTML = '';
    for(let i=0;i<filas;i++){
        for(let j=0;j<columnas;j++){
            const c=document.createElement('div');
            c.className='casilla';
            c.dataset.fila=i;
            c.dataset.columna=j;
            c.addEventListener('click',()=>dispararCasilla(i,j,c));
            tableroDiv.appendChild(c);
        }
    }
}

function perder() {
    reproducirSonido('perder');
    mensajeVictoria.textContent=`¡Lo siento, ${jugador}! Has alcanzado el límite de disparos.`;
    mensajeVictoria.style.display='block';
    setTimeout(()=>mensajeVictoria.style.display='none',3000);
    document.querySelectorAll('.casilla').forEach(c=>c.classList.add('disparada'));
}
function ganar() {
    reproducirSonido('ganar');
    mensajeVictoria.textContent=`¡Felicidades, ${jugador}! Has hundido todos los barcos.`;
    mensajeVictoria.style.display='block';
    setTimeout(()=>mensajeVictoria.style.display='none',3000);
    document.querySelectorAll('.casilla').forEach(c=>c.classList.add('disparada'));
}
async function mostrarRanking() {
    try {
        const res = await fetch(`${API_URL}/ranking`);
        const ranking = await res.json();
        const lista = document.getElementById("ranking");
        lista.innerHTML = ranking
            .map((r, i) => `<li>${i + 1}. ${r.jugador} - ${r.puntuacion} pts</li>`)
            .join("");
    } catch(e){ console.error("Error al obtener ranking", e); }
}

async function dispararCasilla(fila,columna,casilla){
    if(casilla.classList.contains('disparada') || casilla.classList.contains('hundido')) return;

    try{
        const r=await fetch(`${API_URL}/disparar?fila=${fila}&columna=${columna}`,{method:'POST'});
        const data=await r.json();

        casilla.classList.add('disparada');
        casilla.style.cursor='not-allowed';

        if(data.resultado==='tocado') {
            casilla.classList.add('tocado'); 
            casilla.textContent='💥';
            reproducirSonido('tocado');
        }   
        else if(data.resultado==='hundido') {
            casilla.classList.add('hundido');
            casilla.textContent='☠️';
            reproducirSonido('hundido');
        }
        else {
            casilla.classList.add('agua');
            casilla.textContent='💧';
            reproducirSonido('agua');
        }

        // Stats
        document.getElementById('dispars').textContent=data.dispars;
        document.getElementById('encerts').textContent=data.encerts;
        document.getElementById('enfonsats').textContent=data.vaixells_hundidos;
        document.getElementById('puntuacio').textContent=data.puntuacio;

        //  SISTEMA DE RANKING
        async function cargarRanking() {
            try {
                const res = await fetch(`${API_URL}/ranking`);
                const data = await res.json();

                const rankingList = document.getElementById("ranking");
                rankingList.innerHTML = "";

                data.slice(0, 5).forEach((item, i) => {
                    const li = document.createElement("li");
                    li.textContent = `${i + 1}. ${item.jugador} — ${item.puntuacion} pts`;
                    rankingList.appendChild(li);
                });
            } catch (e) {
                console.error("Error cargando ranking:", e);
            }
        }

// Cargar ranking automáticamente al entrar al juego
        document.addEventListener("DOMContentLoaded", cargarRanking);

        // Ganar
        if(data.encerts === data.casillas_ocupadas){
            ganar();
        }
        // Perder
        switch (dificultad) {
            case '1':
                if (Number(data.dispars)>= totalCasillas*0.7){
                    perder();
                }
                break;

            case '2':
                if (Number(data.dispars)>= totalCasillas*0.5){
                    perder();
                }
                break;

            case '3':
                if (Number(data.dispars)>= totalCasillas*0.32){
                    perder();
                }
                break;
            }
    } catch(e){console.error(e);} 
}
